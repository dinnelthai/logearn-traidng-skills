#!/usr/bin/env python3
"""
主入口：CA → K线（LogEarn优先 + gmgn兜底）→ 回测 → 入库 → 生成HTML
"""
import sys, os, json, sqlite3, subprocess, time

DB = '/root/ca-backtester/data/backtest.db'
CACHE = '/root/ca-backtester/cache'
LOGEARN_KEY = 'sk_3f5eedad86974c0a8680da154b1a8028'

# ── LogEarn K线 ────────────────────────────────────────

def logearn_kline(ca, interval=300, size=96, end=None):
    cmd = [
        'python3', '/root/.hermes/skills/logearn/logearn-cli.py',
        'log-get-kline',
        '--chain', '3', '--token', ca,
        '--interval', str(interval), '--size', str(size),
    ]
    if end:
        cmd.extend(['--end', str(end)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                       env={**os.environ, 'LOGEARN_API_KEY': LOGEARN_KEY})
    try:
        return json.loads(r.stdout)
    except:
        return []

def fetch_logearn(ca):
    """LogEarn拉K线，翻页到swap_begin前2小时"""
    cache_file = f"{CACHE}/{ca}_logearn.json"
    if os.path.exists(cache_file):
        print(f"  📦 LogEarn缓存命中")
        with open(cache_file) as f:
            return json.load(f)

    swap_begin = _get_swap_begin(ca)
    print(f"  swap_begin: {swap_begin}")

    all_klines = []
    current_end = int(time.time())

    while True:
        klines = logearn_kline(ca, interval=300, size=96, end=current_end)
        if not klines:
            break
        all_klines.extend(klines)
        oldest = klines[0]['time']
        print(f"    拉到 {len(klines)} 条，最早 {oldest}")
        if oldest <= (swap_begin if swap_begin else 0):
            break
        current_end = oldest - 1

    # 去重排序
    seen = set()
    unique = []
    for k in sorted(all_klines, key=lambda x: x['time']):
        if k['time'] not in seen:
            seen.add(k['time'])
            unique.append(k)

    # 过滤到swap_begin前2小时
    if swap_begin:
        cutoff = swap_begin - 7200
        unique = [k for k in unique if k['time'] >= cutoff]
        print(f"  过滤后: {len(unique)} 条")

    os.makedirs(CACHE, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(unique, f)
    print(f"  ✅ LogEarn缓存写入: {len(unique)} 条")
    return unique

# ── gmgn K线兜底 ─────────────────────────────────────

def fetch_gmgn(ca):
    cache_file = f"{CACHE}/{ca}_gmgn.json"
    if os.path.exists(cache_file):
        print(f"  📦 gmgn缓存命中")
        with open(cache_file) as f:
            return json.load(f)

    swap_begin = _get_swap_begin(ca)

    r = subprocess.run([
        'gmgn-cli', 'market', 'kline',
        '--chain', 'sol', '--address', ca,
        '--resolution', '5m', '--raw'
    ], capture_output=True, text=True, timeout=20)
    try:
        latest = json.loads(r.stdout).get('list', [])
    except:
        return []

    if not latest:
        return []

    newest_ts = latest[-1]['time'] // 1000
    open_ts = (swap_begin - 3600) if swap_begin else (newest_ts - 86400)
    print(f"  时间范围: {open_ts} ~ {newest_ts}")

    all_klines = []
    current_to = newest_ts + 300

    while current_to > open_ts:
        r = subprocess.run([
            'gmgn-cli', 'market', 'kline',
            '--chain', 'sol', '--address', ca,
            '--resolution', '5m', '--to', str(current_to), '--raw'
        ], capture_output=True, text=True, timeout=20)
        try:
            lst = json.loads(r.stdout).get('list', [])
        except:
            break
        if not lst:
            break
        all_klines.extend(lst)
        oldest = lst[0]['time'] // 1000
        print(f"    拉到 {len(lst)} 条，最早 {oldest}")
        if len(lst) < 100:
            break
        current_to = oldest - 300

    seen = set()
    unique = []
    for k in reversed(all_klines):
        t = k['time'] // 1000
        if t not in seen and (not swap_begin or t >= swap_begin - 7200):
            seen.add(t)
            unique.append(k)
    unique.sort(key=lambda x: x['time'])

    os.makedirs(CACHE, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(unique, f)
    print(f"  ✅ gmgn缓存写入: {len(unique)} 条")
    return unique

# ── 统一入口 ─────────────────────────────────────────

def _get_swap_begin(ca):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT swap_begin_time FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row and row[0] else None

def fetch_klines(ca):
    """优先LogEarn，gmgn兜底"""
    print(f"  [1/2] LogEarn...")
    raw = fetch_logearn(ca)

    if raw and len(raw) >= 50:
        print(f"  ✅ LogEarn {len(raw)} 条")
        return raw

    print(f"  [2/2] gmgn兜底...")
    raw2 = fetch_gmgn(ca)
    if raw2 and len(raw2) >= 50:
        print(f"  ✅ gmgn {len(raw2)} 条")
        return raw2

    print(f"  ❌ 两数据源都失败")
    return raw or []

def normalize_klines(raw):
    return [{
        'time': k['time'] // 1000 if isinstance(k['time'], int) and k['time'] > 1e12 else k['time'],
        'open': float(k['open']),
        'high': float(k['high']),
        'low': float(k['low']),
        'close': float(k['close']),
        'volume': float(k.get('volume', 0)),
        'market_cap': float(k.get('market_cap', 0.0)),  # 保留market_cap字段
    } for k in raw]

# ── 回测 ─────────────────────────────────────────────

def run_backtest(ca):
    sys.path.insert(0, '/root/logearn-traidng-skills')
    from trading.win_rate_analyzer import analyze_token_trades

    raw = fetch_klines(ca)
    if not raw:
        return None, "无K线"
    klines = normalize_klines(raw)
    if len(klines) < 10:
        return None, f"K线不足({len(klines)}条)"

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT symbol, mcap FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    conn.close()
    symbol = row[0] if row else 'UNKNOWN'
    mcap = row[1] if row else 0

    # 使用180k作为最小市值阈值（单位：k）
    min_market_cap = 180.0  # 180k
    result = analyze_token_trades(
        ca=ca,
        raw_klines=klines,
        symbol=symbol,
        total_capital=2.0,
        min_market_cap=min_market_cap,
        max_trades=5
    )

    trades = result.get('trades', [])
    total = len(trades)
    wins = sum(1 for t in trades if t.get('is_win', False))
    win_rate = wins / total if total > 0 else 0
    total_profit_pct = sum(t.get('profit_rate', 0) * 100 for t in trades)
    profits = [t.get('profit_rate', 0) * 100 for t in trades] if trades else [0]

    return {
        'bt_trade_count': total,
        'bt_win_count': wins,
        'bt_win_rate': win_rate,
        'bt_total_profit_pct': total_profit_pct,
        'bt_min_profit_pct': min(profits),
        'bt_max_profit_pct': max(profits),
        'bt_klines_count': len(klines),
        'bt_trades_json': json.dumps(trades),
    }, None

# ── 入库 ─────────────────────────────────────────────

def save_result(ca, result, error=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT symbol, mcap, swap_begin_time FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    sym = row[0] if row else 'UNKNOWN'
    mcap_val = row[1] if row else 0
    sbt = row[2] if row else None

    if error:
        trade_count = win_count = win_rate = total_profit = min_pct = max_pct = 0
        trades_json = None
        klines_cnt = 0
    else:
        trade_count = result['bt_trade_count']
        win_count = result['bt_win_count']
        win_rate = result['bt_win_rate']
        total_profit = result['bt_total_profit_pct']
        min_pct = result['bt_min_profit_pct']
        max_pct = result['bt_max_profit_pct']
        trades_json = result['bt_trades_json']
        klines_cnt = result['bt_klines_count']

    cur.execute("""INSERT OR REPLACE INTO phase2_signals
        (token_address, symbol, mcap, swap_begin_time,
         bt_trade_count, bt_win_count, bt_win_rate,
         bt_total_profit_pct, bt_min_profit_pct, bt_max_profit_pct,
         bt_trades_json, bt_klines_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ca, sym, mcap_val, sbt,
         trade_count, win_count, win_rate,
         total_profit, min_pct, max_pct,
         trades_json, klines_cnt))
    conn.commit()
    conn.close()

# ── HTML ─────────────────────────────────────────────

def gen_html():
    result = subprocess.run(
        ['python3', '/root/ca-backtester/gen_html.py'],
        capture_output=True, text=True
    )
    print(result.stdout.strip())
    return '/root/ca-backtester/reports/backtest_report.html'

# ── 主流程 ─────────────────────────────────────────

def process_ca(ca):
    print(f"\n{'='*50}")
    print(f"处理: {ca}")
    result, error = run_backtest(ca)
    if error:
        print(f"  ❌ {error}")
    else:
        print(f"  ✅ 交易{result['bt_trade_count']}笔 | 胜率{result['bt_win_rate']*100:.0f}% | 盈亏{result['bt_total_profit_pct']:+.2f}%")
    save_result(ca, result, error)
    return result, error

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cas = sys.argv[1:]
    else:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT token_address FROM raw_tokens WHERE swap_begin_time IS NOT NULL")
        cas = [r[0] for r in cur.fetchall()]
        conn.close()
        if not cas:
            print("无CA，先运行 insert_cas.py")
            sys.exit(1)

    print(f"共 {len(cas)} 个CA...")

    for ca in cas:
        process_ca(ca)

    OUT = gen_html()
    print(f"\n✅ 完成！报表: {OUT}")
