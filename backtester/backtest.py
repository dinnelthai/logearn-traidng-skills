#!/usr/bin/env python3
"""
复盘回测：对单个 CA 的 K线调用 analyze_token_trades
结果存入 phase2_signals 表
"""
import sys, os, json, sqlite3
sys.path.insert(0, '/root/logearn-traidng-skills')
from trading.win_rate_analyzer import analyze_token_trades

DB = '/root/ca-backtester/data/backtest.db'
CACHE = '/root/ca-backtester/cache'

def load_klines(ca):
    cache_file = f"{CACHE}/{ca}.json"
    if not os.path.exists(cache_file):
        return []
    with open(cache_file) as f:
        return json.load(f)

def normalize_klines(raw_klines):
    """gmgn K线格式 → fib_calculator 需要的格式"""
    return [{
        'time': k['time'] // 1000,
        'open': float(k['open']),
        'high': float(k['high']),
        'low': float(k['low']),
        'close': float(k['close']),
        'volume': float(k.get('volume', 0)),
    } for k in raw_klines]

def run_backtest(ca):
    """对单个CA跑回测"""
    # 1. 加载K线
    raw = load_klines(ca)
    if not raw:
        return None, "无K线数据"

    klines = normalize_klines(raw)
    if len(klines) < 10:
        return None, f"K线不足({len(klines)}条)"

    # 2. 获取CA信息
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT symbol, mcap FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    conn.close()
    symbol = row[0] if row else 'UNKNOWN'
    mcap = row[1] if row else 0

    # 3. 调用回测（使用180k作为最小市值阈值）
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
    profits = [t.get('profit_rate', 0) * 100 for t in trades]

    return {
        'bt_trade_count': total,
        'bt_win_count': wins,
        'bt_win_rate': win_rate,
        'bt_total_profit_pct': total_profit_pct,
        'bt_min_profit_pct': min(profits) if profits else 0,
        'bt_max_profit_pct': max(profits) if profits else 0,
        'bt_klines_count': len(klines),
        'bt_trades_json': json.dumps(trades),
    }, None

def save_result(ca, result, error=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if error:
        note = f"ERROR: {error}"
        trade_count = win_count = win_rate = total_profit_pct = 0
        min_pct = max_pct = 0
        trades_json = None
    else:
        note = None
        trade_count = result['bt_trade_count']
        win_count = result['bt_win_count']
        win_rate = result['bt_win_rate']
        total_profit_pct = result['bt_total_profit_pct']
        min_pct = result['bt_min_profit_pct']
        max_pct = result['bt_max_profit_pct']
        trades_json = result['bt_trades_json']

    cur.execute("""INSERT OR REPLACE INTO phase2_signals
        (token_address, symbol, mcap, swap_begin_time,
         bt_trade_count, bt_win_count, bt_win_rate,
         bt_total_profit_pct, bt_min_profit_pct, bt_max_profit_pct,
         bt_trades_json, bt_klines_count)
        VALUES (
            (SELECT token_address FROM raw_tokens WHERE token_address = ?),
            (SELECT symbol FROM raw_tokens WHERE token_address = ?),
            (SELECT mcap FROM raw_tokens WHERE token_address = ?),
            (SELECT swap_begin_time FROM raw_tokens WHERE token_address = ?),
            ?, ?, ?, ?, ?, ?, ?, ?
        )""",
        (ca, ca, ca, ca,
         trade_count, win_count, win_rate,
         total_profit_pct, min_pct, max_pct,
         trades_json,
         0))  # klines_count 待补
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 backtest.py <CA>")
        sys.exit(1)

    ca = sys.argv[1]
    result, error = run_backtest(ca)
    if error:
        print(f"❌ {ca[:16]}... | {error}")
    else:
        print(f"✅ {ca[:16]}...")
        print(f"   交易笔数: {result['bt_trade_count']}")
        print(f"   胜率: {result['bt_win_rate']*100:.1f}%")
        print(f"   总盈亏: {result['bt_total_profit_pct']:+.2f}%")
        print(f"   区间: {result['bt_min_profit_pct']:+.2f}% ~ {result['bt_max_profit_pct']:+.2f}%")

    save_result(ca, result, error)
    print(f"\n已存入数据库")
