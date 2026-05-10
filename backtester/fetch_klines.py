#!/usr/bin/env python3
"""
统一K线获取：LogEarn优先，gmgn兜底
"""
import sys, os, json, sqlite3, subprocess, time

DB = '/root/ca-backtester/data/backtest.db'
CACHE = '/root/ca-backtester/cache'
LOGEARN_KEY = 'sk_3f5eedad86974c0a8680da154b1a8028'

# ── LogEarn ─────────────────────────────────────────────

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
    """用LogEarn拉K线，返回[(time, open, high, low, close, volume), ...]"""
    cache_file = f"{CACHE}/{ca}_logearn.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)

    swap_begin = _get_swap_begin(ca)

    all_klines = []
    current_end = int(time.time())

    while True:
        klines = logearn_kline(ca, interval=300, size=96, end=current_end)
        if not klines:
            break
        all_klines.extend(klines)
        oldest = klines[0]['time']
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

    if swap_begin:
        cutoff = swap_begin - 7200
        unique = [k for k in unique if k['time'] >= cutoff]

    os.makedirs(CACHE, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(unique, f)
    return unique

# ── gmgn 兜底 ───────────────────────────────────────────

def fetch_gmgn(ca):
    """gmgn-cli 拉K线"""
    cache_file = f"{CACHE}/{ca}.json"
    if os.path.exists(cache_file):
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
    return unique

def _get_swap_begin(ca):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT swap_begin_time FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row and row[0] else None

# ── 统一入口 ────────────────────────────────────────────

def fetch_klines(ca):
    """优先LogEarn，兜底gmgn"""
    print(f"  [LogEarn] 尝试获取K线...")
    raw = fetch_logearn(ca)

    if raw and len(raw) >= 50:
        print(f"  ✅ LogEarn获取到 {len(raw)} 条")
        return raw

    print(f"  ⚠️ LogEarn数据不足({len(raw) if raw else 0}条)，尝试gmgn...")
    raw_gmgn = fetch_gmgn(ca)
    if raw_gmgn and len(raw_gmgn) >= 50:
        print(f"  ✅ gmgn获取到 {len(raw_gmgn)} 条")
        return raw_gmgn

    print(f"  ❌ 两个数据源都失败")
    return raw or []

def normalize_klines(raw):
    return [{
        'time': k['time'] // 1000 if isinstance(k['time'], int) and k['time'] > 1e12 else k['time'],
        'open': float(k['open']),
        'high': float(k['high']),
        'low': float(k['low']),
        'close': float(k['close']),
        'volume': float(k.get('volume', 0)),
    } for k in raw]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 fetch_klines.py <CA>")
        sys.exit(1)
    ca = sys.argv[1]
    klines = fetch_klines(ca)
    print(f"共 {len(klines)} 条K线")
