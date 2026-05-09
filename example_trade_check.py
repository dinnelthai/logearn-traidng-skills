#!/usr/bin/env python3
"""
交易检测器使用示例
演示如何使用 trade_checker 检测K线是否符合一次完整交易
"""

from trading.trade_checker import check_single_trade_from_raw, print_trade_result


def create_example_klines():
    """
    创建示例K线数据
    模拟一个完整的交易场景：下跌 → 触底 → 反弹 → 卖出
    """
    raw_klines = []
    base_time = 1000000
    
    print("📊 创建示例K线数据...")
    print("   阶段1: 下跌（0.00010 → 0.00006）")
    
    # 阶段1: 下跌（从 0.00010 跌到 0.00006）
    for i in range(15):
        high = 0.00010 - i * 0.0000025
        low = high - 0.000005
        close = low + (high - low) * 0.6
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": high - 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    print("   阶段2: 触底整理（0.00006 附近）")
    
    # 阶段2: 触底整理
    for i in range(5):
        high = 0.000065
        low = 0.000055
        close = 0.00006
        raw_klines.append({
            "time": base_time + (15 + i) * 3600,
            "open": 0.00006,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    print("   阶段3: 反弹（0.00006 → 0.00015）")
    
    # 阶段3: 强势反弹（从 0.00006 涨到 0.00015）
    for i in range(40):
        low = 0.00006 + i * 0.000002
        high = low + 0.000008
        close = high - 0.000001
        raw_klines.append({
            "time": base_time + (20 + i) * 3600,
            "open": low + 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    print(f"   总K线数: {len(raw_klines)}")
    print()
    
    return raw_klines


def example_basic_check():
    """示例1: 基本检测"""
    print("=" * 60)
    print("示例1: 基本交易检测")
    print("=" * 60)
    print()
    
    # 创建K线数据
    raw_klines = create_example_klines()
    
    # 检测交易
    print("🔍 开始检测...")
    result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
    print()
    
    # 打印结果
    print_trade_result(result)
    print()


def example_conditional_trade():
    """示例2: 条件判断 - 只交易未完成过的 token"""
    print("=" * 60)
    print("示例2: 条件判断 - 模拟实际使用场景")
    print("=" * 60)
    print()
    
    # 模拟多个 token
    tokens = [
        {"symbol": "TOKEN_A", "address": "addr_a"},
        {"symbol": "TOKEN_B", "address": "addr_b"},
        {"symbol": "TOKEN_C", "address": "addr_c"},
    ]
    
    print("📋 检测多个 token:")
    print()
    
    for token in tokens:
        print(f"检测 {token['symbol']}...")
        
        # 获取K线（这里用示例数据）
        raw_klines = create_example_klines()
        
        # 检测是否已有完整交易
        result = check_single_trade_from_raw(raw_klines)
        
        if result["matched"]:
            # 已有完整交易 → 跳过
            profit_rate = result["profit"]["profit_rate"]
            print(f"  ❌ 跳过 - 已有完整交易")
            print(f"     收益率: {profit_rate*100:+.2f}%")
            print(f"     买入: {len(result['buy_points'])} 个档位")
            print(f"     卖出: {result['sell_point']['reason']}")
        else:
            # 未有完整交易 → 可以交易
            print(f"  ✅ 可交易 - 未匹配到完整交易")
            print(f"     执行交易逻辑...")
        
        print()


def example_profit_analysis():
    """示例3: 利润分析"""
    print("=" * 60)
    print("示例3: 利润分析")
    print("=" * 60)
    print()
    
    raw_klines = create_example_klines()
    result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
    
    if not result["matched"]:
        print("未匹配到完整交易，无法分析利润")
        return
    
    print("📊 详细利润分析:")
    print()
    
    # 买入分析
    print("买入明细:")
    total_invested = 0
    for i, buy in enumerate(result["buy_points"], 1):
        print(f"  {i}. {buy['tier']}")
        print(f"     价格: {buy['price']:.8f}")
        print(f"     金额: {buy['amount']:.4f} SOL")
        print(f"     K线: #{buy['kline_index']}")
        total_invested += buy['amount']
    
    print(f"\n  总投入: {total_invested:.4f} SOL")
    print()
    
    # 卖出分析
    sell = result["sell_point"]
    profit = result["profit"]
    
    print("卖出明细:")
    print(f"  价格: {sell['price']:.8f}")
    print(f"  K线: #{sell['kline_index']}")
    print(f"  原因: {sell['reason']}")
    print(f"  类型: {sell['type']}")
    print()
    
    # 收益分析
    print("收益分析:")
    print(f"  投入: {profit['invested']:.4f} SOL")
    print(f"  回报: {profit['returned']:.4f} SOL")
    print(f"  利润: {profit['profit_sol']:+.4f} SOL")
    
    profit_emoji = "🟢" if profit['profit_rate'] >= 0 else "🔴"
    print(f"  收益率: {profit_emoji} {profit['profit_rate']*100:+.2f}%")
    
    # 计算涨幅
    avg_buy_price = profit['invested'] / sum(
        buy['amount'] / buy['price'] for buy in result['buy_points']
    )
    price_change = (sell['price'] - avg_buy_price) / avg_buy_price
    print(f"  价格涨幅: {price_change*100:+.2f}%")
    print()


if __name__ == "__main__":
    print("\n")
    print("🚀 交易检测器使用示例")
    print("=" * 60)
    print()
    
    # 运行示例
    example_basic_check()
    print("\n" + "=" * 60 + "\n")
    
    example_conditional_trade()
    print("\n" + "=" * 60 + "\n")
    
    example_profit_analysis()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)
    print()
