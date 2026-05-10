#!/usr/bin/env python3
"""测试指定CA的market_cap数据"""
import sys, json, os
sys.path.insert(0, '/root/logearn-traidng-skills')

ca = "31eo8y4rLj1AsYXjofkANu9hjavCDUiqLxuV6oxgpump"

print("=" * 70)
print(f"测试CA: {ca}")
print("=" * 70)

# 1. 检查LogEarn缓存
cache_logearn = f"/root/ca-backtester/cache/{ca}_logearn.json"
print(f"\n1. 检查LogEarn缓存: {cache_logearn}")
if os.path.exists(cache_logearn):
    with open(cache_logearn) as f:
        klines = json.load(f)
    print(f"   ✅ 缓存存在，K线数量: {len(klines)}")
    
    if klines:
        first = klines[0]
        print(f"   第1条K线字段: {list(first.keys())}")
        
        if 'market_cap' in first:
            # 统计market_cap
            mcaps = [k.get('market_cap', 0) for k in klines]
            valid_mcaps = [m for m in mcaps if m > 0]
            
            print(f"\n   Market Cap统计:")
            print(f"   - 总K线数: {len(klines)}")
            print(f"   - 有效market_cap数: {len(valid_mcaps)}")
            print(f"   - 最小: {min(valid_mcaps) if valid_mcaps else 0:.2f}k")
            print(f"   - 最大: {max(valid_mcaps) if valid_mcaps else 0:.2f}k")
            print(f"   - 平均: {sum(valid_mcaps)/len(valid_mcaps) if valid_mcaps else 0:.2f}k")
            
            # 前10条
            print(f"\n   前10条market_cap:")
            for i, k in enumerate(klines[:10]):
                mcap = k.get('market_cap', 0)
                closeU = k.get('closeU', 0)
                print(f"   [{i}] mcap={mcap:.2f}k, closeU=${closeU:.8f}")
            
            # 检查是否有>=180k的
            above_180 = [m for m in mcaps if m >= 180.0]
            print(f"\n   >= 180k的K线数: {len(above_180)}")
            if above_180:
                first_180_idx = next(i for i, m in enumerate(mcaps) if m >= 180.0)
                print(f"   第一次达到180k: 第{first_180_idx}根K线，市值{mcaps[first_180_idx]:.2f}k")
            else:
                print(f"   ❌ 没有任何K线达到180k！最大只有{max(mcaps):.2f}k")
        else:
            print(f"   ❌ 无market_cap字段！")
            print(f"   示例K线: {json.dumps(first, indent=2)}")
else:
    print(f"   ❌ 缓存不存在")

# 2. 检查gmgn缓存
cache_gmgn = f"/root/ca-backtester/cache/{ca}_gmgn.json"
print(f"\n2. 检查gmgn缓存: {cache_gmgn}")
if os.path.exists(cache_gmgn):
    with open(cache_gmgn) as f:
        klines = json.load(f)
    print(f"   ✅ 缓存存在，K线数量: {len(klines)}")
    if klines:
        first = klines[0]
        has_mcap = 'market_cap' in first
        print(f"   有market_cap字段: {has_mcap}")
else:
    print(f"   ❌ 缓存不存在")

# 3. 检查数据库
print(f"\n3. 检查数据库记录")
try:
    import sqlite3
    conn = sqlite3.connect('/root/ca-backtester/data/backtest.db')
    cur = conn.cursor()
    
    # 检查raw_tokens
    cur.execute("SELECT symbol, mcap, swap_begin_time FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    if row:
        print(f"   Symbol: {row[0]}")
        print(f"   Mcap: {row[1]}")
        print(f"   Swap_begin: {row[2]}")
    else:
        print(f"   ❌ raw_tokens中无此CA")
    
    # 检查phase2_signals
    cur.execute("SELECT bt_trade_count, bt_win_rate, bt_trades_json FROM phase2_signals WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    if row:
        print(f"\n   回测结果:")
        print(f"   - 交易笔数: {row[0]}")
        print(f"   - 胜率: {row[1]*100:.1f}%")
        
        if row[2]:
            trades = json.load(row[2]) if isinstance(row[2], str) else row[2]
            print(f"\n   交易详情:")
            for t in trades:
                mcap_buy = t.get('market_cap_at_buy', 0)
                mcap_sell = t.get('market_cap_at_sell', 0)
                profit = t.get('profit_rate', 0) * 100
                print(f"   第{t['trade_number']}次: 买入{mcap_buy:.1f}k → 卖出{mcap_sell:.1f}k, 收益{profit:+.1f}%")
    else:
        print(f"   ❌ phase2_signals中无此CA")
    
    conn.close()
except Exception as e:
    print(f"   ❌ 数据库错误: {e}")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
