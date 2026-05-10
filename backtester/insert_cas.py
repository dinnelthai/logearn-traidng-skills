#!/usr/bin/env python3
"""从 signals_3x.db 补全 swap_begin_time，缺的从 gmgn 查询"""
import sqlite3, json, subprocess, sys, os

SRC_DB = '/root/logearn-signal-pipeline/signals_3x.db'
DST_DB = '/root/ca-backtester/data/backtest.db'

CAs = [
    "HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump",
    "Au2PSMbU2jX8QW8FrM98xAy6SVY9XhBmCd9BRqfwpump",
    "21rwEDi83RveK3DNgtC6Trs4vyERfqvQTN36F1dmW6ND",
    "jvKtLFLnNGPM7edS9KEpYqPxuY8HPGTZohLFM4Spump",
    "5LNAmDt1VNK7FXeZqcuvJB3zfCxx8QQ3NFDUSbqLpump",
    "FMpFhPyqb5bbZoxb4i5AfFeR4AZSfvBfWXwjBXeDark",
    "2RuPn3xbxwKcx2VsQtfjZpjrNP3p2GX864yAwsafpump",
    "7tQh4cnMcwnhxLzrURBsFMnkeWaXVXRTZQtyNy37pump",
    "FWRKcALU6t3mfY4UaYK9CnDk3aVuzJ77ogsDCk3Cpump",
]

def get_from_src(ca):
    """从 signals_3x.db 查 swap_begin_time / symbol / mcap"""
    try:
        conn = sqlite3.connect(SRC_DB)
        cur = conn.cursor()
        cur.execute("""SELECT symbol, mcap, swap_begin_time FROM raw_tokens
                       WHERE token_address = ? LIMIT 1""", (ca,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {'symbol': row[0], 'mcap': row[1], 'swap_begin_time': int(row[2]) if row[2] else None}
    except:
        pass
    return None

def get_from_gmgn(ca):
    """从 gmgn-cli 查 symbol + swap_begin_time"""
    try:
        r = subprocess.run([
            'gmgn-cli', 'token', 'info',
            '--chain', 'sol', '--address', ca
        ], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        return {
            'symbol': data.get('symbol', 'UNKNOWN'),
            'mcap': float(data.get('market_cap', 0) or 0),
            'swap_begin_time': None  # gmgn token info 没有这个字段，需要换别的方式
        }
    except:
        return None

def upsert(ca, data):
    conn = sqlite3.connect(DST_DB)
    cur = conn.cursor()
    sym = data.get('symbol', 'UNKNOWN')
    mcap = data.get('mcap', 0) or 0
    sbt = data.get('swap_begin_time')
    cur.execute("""INSERT OR REPLACE INTO raw_tokens
        (token_address, symbol, mcap, swap_begin_time)
        VALUES (?, ?, ?, ?)""",
        (ca, sym, mcap, sbt))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    unique_cas = list(dict.fromkeys(CAs))
    print(f"共 {len(unique_cas)} 个唯一CA\n")

    for ca in unique_cas:
        src = get_from_src(ca)
        if src and src.get('swap_begin_time'):
            print(f"✅ {ca[:16]}... | {src['symbol']} | swap_begin={src['swap_begin_time']} [来自signals_3x.db]")
            upsert(ca, src)
        else:
            # 尝试从gmgn补充 symbol/mcap（swap_begin_time 需要从K线或别处获取）
            info = get_from_gmgn(ca)
            if info:
                print(f"⚠️  {ca[:16]}... | {info['symbol']} | swap_begin=未找到 [来自gmgn]")
            else:
                print(f"❌ {ca[:16]}... | 获取失败")
            upsert(ca, info or {'symbol': 'UNKNOWN', 'mcap': 0, 'swap_begin_time': None})

    print("\n完成")
