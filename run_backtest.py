#!/usr/bin/env python3
"""
回测入库脚本 - release/v0.1.0 版本
获取CA的K线数据，调用trading回测，结果写入DB
用法: python run_backtest.py <CA地址> [市值门槛k]
"""
import sys
import os
import sqlite3
import json
from datetime import datetime, timezone

sys.path.insert(0, '/root/logearn-trading-skills')

from trading.kline_service import get_klines
from trading.win_rate_analyzer import analyze_token_trades

DB = '/root/ca-backtester/data/backtest.db'
CACHE = '/root/ca-backtester/cache'
os.makedirs(os.path.dirname(DB), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS phase2_signals (
        token_address TEXT PRIMARY KEY,
        symbol TEXT,
        mcap REAL,
        swap_begin_time INTEGER,
        bt_trade_count INTEGER DEFAULT 0,
        bt_win_count INTEGER DEFAULT 0,
        bt_win_rate REAL DEFAULT 0,
        bt_total_profit_pct REAL DEFAULT 0,
        bt_min_profit_pct REAL DEFAULT 0,
        bt_max_profit_pct REAL DEFAULT 0,
        bt_trades_json TEXT,
        bt_klines_count INTEGER DEFAULT 0,
        created_at INTEGER
    )''')
    conn.commit()
    conn.close()

def mcap(v):
    """格式化市值显示"""
    if v is None:
        return 'N/A'
    if v >= 1_000_000:
        return f'{v/1_000_000:.1f}M'
    elif v >= 1_000:
        return f'{v/1_000:.1f}K'
    return f'{v:.0f}'

init_db()

if len(sys.argv) < 2:
    print("用法: python run_backtest.py <CA地址> [市值门槛k]")
    sys.exit(1)

ca = sys.argv[1]
mcap_threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0

print("=" * 70)
print(f"回测入库: {ca}")
print("=" * 70)

# 获取K线数据
print("[K线获取]")
klines = get_klines(ca, interval='5m', page_size=500)
print(f"K线数: {len(klines)}")

if not klines:
    print("❌ 无K线数据")
    sys.exit(1)

# 原始数据 → dict列表
raw_klines = [
    {
        'time': k.time,
        'open': k.open,
        'high': k.high,
        'low': k.low,
        'close': k.close,
        'volume': k.volume,
        'market_cap': k.market_cap,
    }
    for k in klines
]

# 分析回测
print("\n[回测分析]")
result = analyze_token_trades(
    ca=ca,
    raw_klines=raw_klines,
    symbol=klines[0].symbol if hasattr(klines[0], 'symbol') else 'UNKNOWN',
    total_capital=2.0,
    max_trades=5
)

trades = result.get('trades', [])
total_trades = len(trades)
win_count = sum(1 for t in trades if t.get('is_win', False))
total_pnl = sum(t.get('profit_sol', 0) for t in trades)
avg_rate = sum(t.get('profit_rate', 0) for t in trades) / total_trades if total_trades > 0 else 0
win_rate = win_count / total_trades if total_trades > 0 else 0
profit_rates = [t.get('profit_rate', 0) for t in trades]

print(f"\n交易次数: {total_trades}")
if total_trades > 0:
    print(f"胜率: {win_rate*100:.1f}% | 平均收益: {avg_rate*100:.1f}% | PnL: {total_pnl:.4f} SOL")
    for t in trades:
        label = '✅' if t['is_win'] else '❌'
        print(f"  {label} Trade#{t['trade_number']}: {t['profit_rate']*100:+.1f}%")

# 写入DB
conn = sqlite3.connect(DB)
c = conn.cursor()
now_ts = int(datetime.now(timezone.utc).timestamp())
mcap_val = klines[-1].market_cap if klines else 0

c.execute('''INSERT OR REPLACE INTO phase2_signals
    (token_address, symbol, mcap, swap_begin_time, bt_trade_count, bt_win_count, bt_win_rate, bt_total_profit_pct, bt_min_profit_pct, bt_max_profit_pct, bt_trades_json, bt_klines_count, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (ca,
     result.get('symbol', 'UNKNOWN'),
     mcap_val,
     klines[-1].time if klines else 0,
     total_trades,
     win_count,
     round(win_rate * 100, 1),
     round(avg_rate * 100, 1),
     round(min(profit_rates) * 100, 1) if profit_rates else 0,
     round(max(profit_rates) * 100, 1) if profit_rates else 0,
     json.dumps(trades),
     len(klines),
     now_ts)
)
conn.commit()
conn.close()

print(f"\n✅ 已写入DB: {DB}")
