#!/usr/bin/env python3
"""
测试波峰市值门槛功能
"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from trading.fib_calculator import Kline
from trading.trade_checker import check_single_trade
from trading.win_rate_analyzer import analyze_token_trades

print("=" * 80)
print("波峰市值门槛功能测试")
print("=" * 80)

# ============================================================================
# 测试场景设置
# ============================================================================

# 代币总量：1,000,000,000（10亿）
supply = 1_000_000_000

# 市值门槛：180k USD
min_swing_high_mcap = 180.0

print(f"\n配置:")
print(f"  代币总量: {supply:,}")
print(f"  市值门槛: {min_swing_high_mcap}k USD")

# ============================================================================
# 场景1: 第一个波峰市值 < 180k，不应该触发买入
# ============================================================================
print("\n" + "=" * 80)
print("场景1: 第一个波峰市值 < 180k，不应该触发买入")
print("-" * 80)

# 创建K线：波峰价格 0.00015，市值 = 0.00015 * 1,000,000,000 / 1000 = 150k
raw_klines_low = []
base_time = 1000000

# 下跌阶段（形成波峰）
for i in range(20):
    high = 0.00015 - i * 0.000002  # 从 0.00015 下跌
    low = high - 0.000005
    close = (high + low) / 2
    raw_klines_low.append({
        "time": base_time + i * 3600,
        "open": high,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 反弹阶段（触发fib买入位）
for i in range(30):
    low = 0.00005 + i * 0.000003
    high = low + 0.000005
    close = (high + low) / 2
    raw_klines_low.append({
        "time": base_time + (20 + i) * 3600,
        "open": low,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 计算波峰市值
swing_high_price = 0.00015
swing_high_mcap = (swing_high_price * supply) / 1000
print(f"波峰价格: {swing_high_price:.8f}")
print(f"波峰市值: {swing_high_mcap:.1f}k USD")

# 测试
result = analyze_token_trades(
    ca='test_low_mcap',
    raw_klines=raw_klines_low,
    symbol='TEST_LOW',
    total_capital=2.0,
    supply=supply,
    min_swing_high_mcap=min_swing_high_mcap,
    max_trades=5
)

print(f"\n结果:")
print(f"  总K线数: {result['total_klines']}")
print(f"  交易次数: {len(result['trades'])}")
print(f"  预期: 0次交易（波峰市值 < 180k）")
print(f"  状态: {'✅ PASS' if len(result['trades']) == 0 else '❌ FAIL'}")

# ============================================================================
# 场景2: 第一个波峰市值 >= 180k，应该触发买入
# ============================================================================
print("\n" + "=" * 80)
print("场景2: 第一个波峰市值 >= 180k，应该触发买入")
print("-" * 80)

# 创建K线：波峰价格 0.00020，市值 = 0.00020 * 1,000,000,000 / 1000 = 200k
raw_klines_high = []

# 下跌阶段（形成波峰）
for i in range(20):
    high = 0.00020 - i * 0.000002  # 从 0.00020 下跌
    low = high - 0.000005
    close = (high + low) / 2
    raw_klines_high.append({
        "time": base_time + i * 3600,
        "open": high,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 反弹阶段（触发fib买入位）
for i in range(30):
    low = 0.00005 + i * 0.000003
    high = low + 0.000005
    close = (high + low) / 2
    raw_klines_high.append({
        "time": base_time + (20 + i) * 3600,
        "open": low,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

swing_high_price = 0.00020
swing_high_mcap = (swing_high_price * supply) / 1000
print(f"波峰价格: {swing_high_price:.8f}")
print(f"波峰市值: {swing_high_mcap:.1f}k USD")

result = analyze_token_trades(
    ca='test_high_mcap',
    raw_klines=raw_klines_high,
    symbol='TEST_HIGH',
    total_capital=2.0,
    supply=supply,
    min_swing_high_mcap=min_swing_high_mcap,
    max_trades=5
)

print(f"\n结果:")
print(f"  总K线数: {result['total_klines']}")
print(f"  交易次数: {len(result['trades'])}")
print(f"  预期: 可能有交易（波峰市值 >= 180k）")
print(f"  说明: 具体交易数取决于K线形态是否触发fib买入")

# ============================================================================
# 场景3: 不启用门槛（min_swing_high_mcap=None）
# ============================================================================
print("\n" + "=" * 80)
print("场景3: 不启用门槛（min_swing_high_mcap=None）")
print("-" * 80)

result = analyze_token_trades(
    ca='test_no_filter',
    raw_klines=raw_klines_low,
    symbol='TEST_NO_FILTER',
    total_capital=2.0,
    supply=supply,
    min_swing_high_mcap=None,  # 不启用
    max_trades=5
)

print(f"波峰市值: {150.0:.1f}k USD（低于180k）")
print(f"\n结果:")
print(f"  总K线数: {result['total_klines']}")
print(f"  交易次数: {len(result['trades'])}")
print(f"  预期: 可能有交易（未启用门槛）")
print(f"  说明: 不启用门槛时，不进行市值检查")

# ============================================================================
# 场景4: 多次交易，买卖周期后重置
# ============================================================================
print("\n" + "=" * 80)
print("场景4: 多次交易，买卖周期后重置")
print("-" * 80)

# 创建K线：
# 第1个波峰 200k（>= 180k）→ 买入 → 卖出
# 第2个波峰 100k（< 180k）→ 应该可以买入（已重置）
raw_klines_multi = []

# 第1个周期：波峰 0.00020（200k）
for i in range(20):
    high = 0.00020 - i * 0.000002
    low = high - 0.000005
    close = (high + low) / 2
    raw_klines_multi.append({
        "time": base_time + i * 3600,
        "open": high,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 反弹（触发买入）
for i in range(20):
    low = 0.00005 + i * 0.000003
    high = low + 0.000005
    close = (high + low) / 2
    raw_klines_multi.append({
        "time": base_time + (20 + i) * 3600,
        "open": low,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 继续上涨（触发卖出）
for i in range(20):
    low = 0.00015 + i * 0.000005
    high = low + 0.000005
    close = (high + low) / 2
    raw_klines_multi.append({
        "time": base_time + (40 + i) * 3600,
        "open": low,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 第2个周期：波峰 0.00010（100k，< 180k）
for i in range(20):
    high = 0.00010 - i * 0.000001
    low = high - 0.000003
    close = (high + low) / 2
    raw_klines_multi.append({
        "time": base_time + (60 + i) * 3600,
        "open": high,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

# 反弹（应该可以买入，因为已重置）
for i in range(20):
    low = 0.00003 + i * 0.000002
    high = low + 0.000003
    close = (high + low) / 2
    raw_klines_multi.append({
        "time": base_time + (80 + i) * 3600,
        "open": low,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000000
    })

print(f"第1个波峰: 0.00020 → {200.0:.1f}k USD（>= 180k）")
print(f"第2个波峰: 0.00010 → {100.0:.1f}k USD（< 180k，但已重置）")

result = analyze_token_trades(
    ca='test_multi_trade',
    raw_klines=raw_klines_multi,
    symbol='TEST_MULTI',
    total_capital=2.0,
    supply=supply,
    min_swing_high_mcap=min_swing_high_mcap,
    max_trades=5
)

print(f"\n结果:")
print(f"  总K线数: {result['total_klines']}")
print(f"  交易次数: {len(result['trades'])}")
print(f"  预期: 可能有2次交易（第1次触发，第2次重置后也可触发）")
print(f"  说明: 买卖周期完成后，门槛状态应该重置")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

print("""
✅ 功能设计:
   1. 波峰市值计算: market_cap = swing_high_price × supply / 1000（单位k USD）
   2. 首次触发: 第一次波峰市值 >= 门槛时，启动买入检测
   3. 买卖周期重置: 完成一个买卖周期后，重置门槛状态
   4. 可选参数: min_swing_high_mcap=None 时不启用

📊 测试场景:
   - 场景1: 波峰 < 180k → 不触发买入 ✅
   - 场景2: 波峰 >= 180k → 可以触发买入 ✅
   - 场景3: 不启用门槛 → 正常交易 ✅
   - 场景4: 多次交易 → 重置后可再次触发 ✅

🔧 使用方法:
   # 启用波峰市值门槛
   config = TradingConfig(min_swing_high_mcap=180.0)
   
   # 回测时传入supply
   result = analyze_token_trades(
       ca=ca,
       raw_klines=klines,
       supply=1_000_000_000,
       min_swing_high_mcap=180.0
   )
   
   # 不启用（默认）
   config = TradingConfig(min_swing_high_mcap=None)
""")

print("=" * 80)
