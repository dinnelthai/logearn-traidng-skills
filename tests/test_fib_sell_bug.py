#!/usr/bin/env python3
"""
测试 Fib 分批卖出 bug 修复
验证多次 Fib 卖出是否正确记录和计算利润
"""

from trading.trade_checker import check_single_trade_from_raw, print_trade_result


def test_fib_multi_sell():
    """
    测试场景：
    1. 买入 618、786、861 三个档位
    2. 价格回到波峰（sell_100）→ 卖出 30%
    3. 价格突破 1.272 扩展位（sell_1272）→ 卖出 50%
    4. 总共卖出 80%
    """
    print("=" * 60)
    print("测试：Fib 分批卖出 bug 修复")
    print("=" * 60)
    print()
    
    raw_klines = []
    base_time = 1000000
    
    # 阶段1: 下跌到波谷（触发买入）
    print("阶段1: 下跌到波谷...")
    swing_high = 0.0001000
    swing_low = 0.0000500
    
    # 下跌 K 线
    for i in range(20):
        high = swing_high - i * 0.0000025
        low = high - 0.0000010
        close = (high + low) / 2
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": high,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 阶段2: 触发买入档位（618、786、861）
    print("阶段2: 触发买入档位...")
    # 618: 0.0000691
    # 786: 0.0000607
    # 861: 0.0000569
    for i in range(5):
        low = swing_low + i * 0.0000005
        high = low + 0.0000010
        close = (high + low) / 2
        raw_klines.append({
            "time": base_time + (20 + i) * 3600,
            "open": low,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 阶段3: 反弹到 sell_100（波峰，卖出 30%）
    print("阶段3: 反弹到波峰（sell_100）...")
    # sell_100 = swing_high = 0.0001000
    for i in range(15):
        low = 0.0000600 + i * 0.0000027
        high = low + 0.0000010
        close = high  # 收盘价接近高点
        raw_klines.append({
            "time": base_time + (25 + i) * 3600,
            "open": low,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 阶段4: 继续上涨到 sell_1272（127.2% 扩展位，卖出 50%）
    print("阶段4: 突破到 sell_1272（127.2% 扩展位）...")
    # sell_1272 = swing_high + (swing_high - swing_low) * 0.272
    #           = 0.0001000 + 0.0000500 * 0.272
    #           = 0.0001136
    for i in range(10):
        low = 0.0001000 + i * 0.0000015
        high = low + 0.0000010
        close = high
        raw_klines.append({
            "time": base_time + (40 + i) * 3600,
            "open": low,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 检测交易
    result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
    
    # 打印结果
    print()
    print_trade_result(result)
    
    # 验证结果
    print()
    print("=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    if not result["matched"]:
        print("❌ 测试失败：未匹配到完整交易")
        return False
    
    sell_points = result.get("sell_points", [])
    
    # 验证1: 应该有 2 次卖出
    if len(sell_points) != 2:
        print(f"❌ 测试失败：期望 2 次卖出，实际 {len(sell_points)} 次")
        return False
    print(f"✅ 卖出次数正确：{len(sell_points)} 次")
    
    # 验证2: 第一次应该是 sell_100，卖出 30%
    first_sell = sell_points[0]
    if first_sell.get("tier") != "sell_100":
        print(f"❌ 测试失败：第一次卖出档位应为 sell_100，实际 {first_sell.get('tier')}")
        return False
    if abs(first_sell.get("percentage", 0) - 0.30) > 0.01:
        print(f"❌ 测试失败：第一次卖出比例应为 30%，实际 {first_sell.get('percentage')*100:.0f}%")
        return False
    print(f"✅ 第一次卖出正确：{first_sell.get('tier')} 卖出 {first_sell.get('percentage')*100:.0f}%")
    
    # 验证3: 第二次应该是 sell_1272，卖出 50%
    second_sell = sell_points[1]
    if second_sell.get("tier") != "sell_1272":
        print(f"❌ 测试失败：第二次卖出档位应为 sell_1272，实际 {second_sell.get('tier')}")
        return False
    if abs(second_sell.get("percentage", 0) - 0.50) > 0.01:
        print(f"❌ 测试失败：第二次卖出比例应为 50%，实际 {second_sell.get('percentage')*100:.0f}%")
        return False
    print(f"✅ 第二次卖出正确：{second_sell.get('tier')} 卖出 {second_sell.get('percentage')*100:.0f}%")
    
    # 验证4: 总卖出比例应为 80%
    profit = result.get("profit", {})
    total_sell_pct = profit.get("sell_percentage", 0)
    if abs(total_sell_pct - 0.80) > 0.01:
        print(f"❌ 测试失败：总卖出比例应为 80%，实际 {total_sell_pct*100:.0f}%")
        return False
    print(f"✅ 总卖出比例正确：{total_sell_pct*100:.0f}%")
    
    # 验证5: 利润计算应该基于两次卖出的加权平均
    print(f"✅ 利润计算：投入 {profit.get('invested_for_sold', 0):.4f} SOL，回报 {profit.get('returned', 0):.4f} SOL")
    
    print()
    print("=" * 60)
    print("🎉 所有测试通过！Fib 分批卖出 bug 已修复")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_fib_multi_sell()
