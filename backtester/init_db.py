#!/usr/bin/env python3
"""初始化 CA 回测数据库"""
import sqlite3, os

DB = '/root/ca-backtester/data/backtest.db'

def init():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # raw_tokens: 原始代币数据
    cur.execute("""CREATE TABLE IF NOT EXISTS raw_tokens (
        token_address TEXT PRIMARY KEY,
        symbol TEXT,
        name TEXT,
        mcap REAL,
        liquidity REAL,
        swap_begin_time INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # phase2_signals: 回测结果
    cur.execute("""CREATE TABLE IF NOT EXISTS phase2_signals (
        token_address TEXT PRIMARY KEY,
        symbol TEXT,
        mcap REAL,
        swap_begin_time INTEGER,
        bt_trade_count INTEGER DEFAULT 0,
        bt_win_count INTEGER DEFAULT 0,
        bt_win_rate REAL DEFAULT 0,
        bt_total_profit_pct REAL DEFAULT 0,
        bt_min_profit_pct REAL,
        bt_max_profit_pct REAL,
        bt_trades_json TEXT,
        bt_klines_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB}")

if __name__ == '__main__':
    init()
