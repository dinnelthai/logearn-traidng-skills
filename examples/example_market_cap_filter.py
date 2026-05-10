#!/usr/bin/env python3
"""
市值过滤功能使用示例
演示如何使用180k市值过滤进行回测
"""

from trading.trade_checker import check_single_trade_from_raw, print_trade_result


def create_klines_with_market_cap():
    """
    创建包含市值的K线数据
    模拟场景：市值从100k涨到180k，然后回调到120k，再涨到250k
    """
    raw_klines = []
    base_time = 1000000
    
    print("📊 创建K线数据（包含市值）...")
    print()
    
    # 阶段1: 市值 100k -> 170k（未达到180k）
    print("   阶段1: 市值上涨 100k -> 170k（未达到180k）")
    for i in range(15):
        market_cap = 100.0 + i * 5  # 100k -> 170k
        price = 0.00005 + i * 0.000002
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": price,
            "high": price + 0.000001,
            "low": price - 0.000001,
            "close": price,
            "volume": "1000000",
            "market_cap": market_cap
        })
    
    # 阶段2: 市值突破180k（185k）← 从这里开始回测
    print("   阶段2: 市值突破180k达到185k ← 回测起点")
    raw_klines.append({
        "time": base_time + 15 * 3600,
        "open": 0.00008,
        "high": 0.000085,
        "low": 0.000075,
        "close": 0.00008,
        "volume": "1000000",
        "market_cap": 185.0  # 第一次达到180k
    })
    
    # 阶段3: 市值回调到120k（仍然保留）
    print("   阶段3: 市值回调到120k（仍然保留在回测中）")
    for i in range(5):
        market_cap = 185.0 - i * 13  # 185k -> 120k
        price = 0.00008 - i * 0.000005
        raw_klines.append({
            "time": base_time + (16 + i) * 3600,
            "open": price,
            "high": price + 0.000001,
            "low": price - 0.000001,
            "close": price,
            "volume": "1000000",
            "market_cap": market_cap
        })
    
    # 阶段4: 市值再次上涨到250k
    print("   阶段4: 市值再次上涨到250k")
    for i in range(20):
        market_cap = 120.0 + i * 6.5  # 120k -> 250k
        price = 0.00006 + i * 0.000003
        raw_klines.append({
            "time": base_time + (21 + i) * 3600,
            "open": price,
            "high": price + 0.000002,
            "low": price - 0.000001,
            "close": price,
            "volume": "1000000",
            "market_cap": market_cap
        })
    
    print(f"   总K线数: {len(raw_klines)}")
    print(f"   市值范围: {raw_klines[0]['market_cap']:.0f}k -> {raw_klines[-1]['market_cap']:.0f}k")
    print()
    
    return raw_klines


def example_with_180k_filter():
    """示例1: 使用180k市值过滤"""
    print("=" * 60)
    print("示例1: 使用180k市值过滤")
    print("=" * 60)
    print()
    
    raw_klines = create_klines_with_market_cap()
    
    print("🔍 开始检测（使用180k市值过滤）...")
    print()
    
    result = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=180.0  # 关键参数：180k过滤
    )
    
    print_trade_result(result)
    
    # 显示过滤统计
    print()
    print("📊 过滤统计:")
    print(f"  总K线数: {len(raw_klines)}")
    
    # 计算被过滤掉的K线数
    filtered_count = sum(1 for k in raw_klines if k['market_cap'] < 180.0)
    print(f"  被过滤K线数: {filtered_count}（市值 < 180k）")
    print(f"  参与回测K线数: {len(raw_klines) - filtered_count}（市值首次达到180k后的所有K线）")
    print()


def example_without_filter():
    """示例2: 不使用市值过滤"""
    print("=" * 60)
    print("示例2: 不使用市值过滤（对比）")
    print("=" * 60)
    print()
    
    raw_klines = create_klines_with_market_cap()
    
    print("🔍 开始检测（不使用市值过滤）...")
    print()
    
    result = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0
        # 不传入min_market_cap参数
    )
    
    print_trade_result(result)
    
    print()
    print("📊 统计:")
    print(f"  参与回测K线数: {len(raw_klines)}（全部K线）")
    print()


def example_never_reached_180k():
    """示例3: 市值从未达到180k"""
    print("=" * 60)
    print("示例3: 市值从未达到180k")
    print("=" * 60)
    print()
    
    # 创建市值始终 < 180k 的K线
    raw_klines = []
    base_time = 1000000
    
    for i in range(20):
        market_cap = 100.0 + i * 3  # 100k -> 157k
        price = 0.00005 + i * 0.000001
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": price,
            "high": price + 0.000001,
            "low": price - 0.000001,
            "close": price,
            "volume": "1000000",
            "market_cap": market_cap
        })
    
    print(f"📊 创建K线数据: {len(raw_klines)}根")
    print(f"   市值范围: {raw_klines[0]['market_cap']:.0f}k -> {raw_klines[-1]['market_cap']:.0f}k")
    print()
    
    print("🔍 开始检测（使用180k市值过滤）...")
    print()
    
    result = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=180.0
    )
    
    print_trade_result(result)
    print()


def example_custom_threshold():
    """示例4: 自定义市值阈值"""
    print("=" * 60)
    print("示例4: 自定义市值阈值（200k）")
    print("=" * 60)
    print()
    
    raw_klines = create_klines_with_market_cap()
    
    print("🔍 开始检测（使用200k市值过滤）...")
    print()
    
    result = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=200.0  # 自定义阈值：200k
    )
    
    print_trade_result(result)
    
    print()
    print("📊 过滤统计:")
    print(f"  总K线数: {len(raw_klines)}")
    filtered_count = sum(1 for k in raw_klines if k['market_cap'] < 200.0)
    print(f"  被过滤K线数: {filtered_count}（市值 < 200k）")
    print(f"  参与回测K线数: {len(raw_klines) - filtered_count}")
    print()


if __name__ == "__main__":
    print("\n")
    print("🚀 市值过滤功能使用示例")
    print("=" * 60)
    print()
    
    # 运行示例
    example_with_180k_filter()
    print("\n" + "=" * 60 + "\n")
    
    example_without_filter()
    print("\n" + "=" * 60 + "\n")
    
    example_never_reached_180k()
    print("\n" + "=" * 60 + "\n")
    
    example_custom_threshold()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)
    print()
    
    print("💡 使用提示:")
    print("  1. 在K线数据中添加 'market_cap' 字段（单位：k）")
    print("  2. 调用 check_single_trade_from_raw() 时传入 min_market_cap 参数")
    print("  3. min_market_cap=None 表示不使用市值过滤（默认）")
    print("  4. min_market_cap=180.0 表示只回测市值首次达到180k后的K线")
    print()
