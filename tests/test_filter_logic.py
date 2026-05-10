#!/usr/bin/env python3
"""测试市值过滤逻辑"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from trading.fib_calculator import Kline
from trading.trade_checker import filter_klines_by_market_cap, check_single_trade

print("=" * 70)
print("测试市值过滤逻辑")
print("=" * 70)

# 模拟场景：所有K线市值都是33k（低于180k）
print("\n场景1: 所有K线市值都是33k（应该被过滤）")
klines_33k = [
    Kline(time=1000000 + i*3600, open=0.0001, high=0.00011, low=0.00009, 
          close=0.0001, volume=1000, market_cap=33.2)
    for i in range(100)
]

print(f"原始K线数: {len(klines_33k)}")
print(f"所有K线market_cap: 33.2k")

# 测试过滤
filtered = filter_klines_by_market_cap(klines_33k, min_market_cap=180.0)
print(f"过滤后K线数: {len(filtered)}")
print(f"预期: 0（因为没有K线>=180k）")
print(f"结果: {'✅ 正确' if len(filtered) == 0 else '❌ 错误'}")

# 测试check_single_trade
result = check_single_trade(klines_33k, total_capital=2.0, min_market_cap=180.0)
print(f"\ncheck_single_trade结果:")
print(f"  matched: {result['matched']}")
print(f"  预期: False")
print(f"  结果: {'✅ 正确' if not result['matched'] else '❌ 错误'}")
if result.get('filter_reason'):
    print(f"  过滤原因: {result['filter_reason']}")

# 场景2: 有部分K线>=180k
print("\n" + "=" * 70)
print("场景2: 前50根33k，后50根200k（应该从第50根开始）")
klines_mixed = [
    Kline(time=1000000 + i*3600, open=0.0001, high=0.00011, low=0.00009,
          close=0.0001, volume=1000, market_cap=33.2 if i < 50 else 200.0)
    for i in range(100)
]

print(f"原始K线数: {len(klines_mixed)}")
print(f"前50根: 33.2k, 后50根: 200k")

filtered = filter_klines_by_market_cap(klines_mixed, min_market_cap=180.0)
print(f"过滤后K线数: {len(filtered)}")
print(f"第一根K线market_cap: {filtered[0].market_cap if filtered else 'N/A'}k")
print(f"预期: 从第50根开始（保留前50根用于fib计算）")

# 场景3: market_cap=0的情况
print("\n" + "=" * 70)
print("场景3: 所有K线market_cap=0（无市值数据）")
klines_zero = [
    Kline(time=1000000 + i*3600, open=0.0001, high=0.00011, low=0.00009,
          close=0.0001, volume=1000, market_cap=0.0)
    for i in range(100)
]

filtered = filter_klines_by_market_cap(klines_zero, min_market_cap=180.0)
print(f"过滤后K线数: {len(filtered)}")
print(f"预期: 0（因为market_cap都是0）")
print(f"结果: {'✅ 正确' if len(filtered) == 0 else '❌ 错误'}")

result = check_single_trade(klines_zero, total_capital=2.0, min_market_cap=180.0)
print(f"\ncheck_single_trade结果:")
print(f"  matched: {result['matched']}")
print(f"  预期: False")
print(f"  结果: {'✅ 正确' if not result['matched'] else '❌ 错误'}")

print("\n" + "=" * 70)
print("结论:")
print("  如果过滤逻辑正确，33k的K线应该被完全过滤掉")
print("  如果仍然有交易，可能原因:")
print("  1. K线数据中market_cap字段缺失或为0")
print("  2. min_market_cap参数没有正确传递")
print("  3. 缓存的K线数据是旧版本（无market_cap）")
print("=" * 70)
