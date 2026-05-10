#!/usr/bin/env python3
"""
主入口：CA → K线（LogEarn优先 + gmgn兜底）→ 回测 → 入库 → 生成HTML
"""
import sys, os, json, sqlite3, subprocess
from backtester.fetch_klines import fetch_klines, normalize_klines, get_token_info

DB = '/root/ca-backtester/data/backtest.db'
CACHE = '/root/ca-backtester/cache'
LOGEARN_KEY = 'sk_3f5eedad86974c0a8680da154b1a8028'

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

    # 检查市值字段
    has_mcap = any('market_cap' in k and k['market_cap'] > 0 for k in klines)
    if not has_mcap:
        print(f"  ⚠️ K线无市值数据，跳过市值过滤")

    # 获取代币信息
    info = get_token_info(ca)
    symbol = info['symbol'] if info else 'UNKNOWN'

    # 回测：min_swing_high_mcap=180k USD（波峰市值门槛）
    min_swing_high_mcap = 180.0  # 180k
    result = analyze_token_trades(
        ca=ca,
        raw_klines=klines,
        symbol=symbol,
        total_capital=2.0,
        supply=info.get('total_supply') if info else None,
        min_swing_high_mcap=min_swing_high_mcap,
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
