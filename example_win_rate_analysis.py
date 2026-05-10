#!/usr/bin/env python3
"""
胜率分析使用示例
演示如何统计第1次、第2次、第3次交易的胜率
"""

from trading.win_rate_analyzer import (
    analyze_token_trades,
    calculate_win_rate_stats,
    print_win_rate_report,
    print_token_trades_summary
)


def create_long_klines_with_multiple_trades():
    """
    创建包含多次交易机会的长K线数据
    模拟90天的数据，包含3次完整的交易周期
    """
    raw_klines = []
    base_time = 1000000
    kline_index = 0
    
    print("📊 创建模拟K线数据（90天，3个交易周期）...")
    
    # 第1次交易周期（60根K线）
    print("   周期1: 下跌 → 买入 → 上涨 → 卖出（盈利）")
    
    # 下跌阶段（从 0.00010 跌到 0.00006）
    for i in range(15):
        high = 0.00010 - i * 0.0000025
        low = high - 0.000005
        close = low + (high - low) * 0.6
        market_cap = 200.0 - i * 5  # 200k -> 125k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": high - 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    # 触底整理
    for i in range(5):
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": 0.00006,
            "high": 0.000065,
            "low": 0.000055,
            "close": 0.00006,
            "volume": "1000000",
            "market_cap": 120.0
        })
        kline_index += 1
    
    # 上涨阶段（从 0.00006 涨到 0.00015，盈利）
    for i in range(40):
        low = 0.00006 + i * 0.000002
        high = low + 0.000008
        close = high - 0.000001
        market_cap = 120.0 + i * 3  # 120k -> 240k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": low + 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    # 间隔期（10天）
    for i in range(10):
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": 0.00012,
            "high": 0.00013,
            "low": 0.00011,
            "close": 0.00012,
            "volume": "1000000",
            "market_cap": 250.0
        })
        kline_index += 1
    
    # 第2次交易周期（60根K线）
    print("   周期2: 下跌 → 买入 → 小幅上涨 → 卖出（小盈利）")
    
    # 下跌（从 0.00012 跌到 0.00007）
    for i in range(15):
        high = 0.00012 - i * 0.000003
        low = high - 0.000005
        close = low + (high - low) * 0.6
        market_cap = 250.0 - i * 6  # 250k -> 160k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": high - 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    # 触底
    for i in range(5):
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": 0.00007,
            "high": 0.000075,
            "low": 0.000065,
            "close": 0.00007,
            "volume": "1000000",
            "market_cap": 150.0
        })
        kline_index += 1
    
    # 小幅反弹（涨到 0.00010）
    for i in range(30):
        low = 0.00007 + i * 0.0000008
        high = low + 0.000005
        close = high - 0.000001
        market_cap = 150.0 + i * 2  # 150k -> 210k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": low + 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    # 间隔期
    for i in range(10):
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": 0.00009,
            "high": 0.0001,
            "low": 0.00008,
            "close": 0.00009,
            "volume": "1000000",
            "market_cap": 180.0
        })
        kline_index += 1
    
    # 第3次交易周期（60根K线）
    print("   周期3: 下跌 → 买入 → 上涨 → 卖出（盈利）")
    
    # 下跌（从 0.00010 跌到 0.00006）
    for i in range(15):
        high = 0.00010 - i * 0.0000025
        low = high - 0.000005
        close = low + (high - low) * 0.6
        market_cap = 200.0 - i * 5  # 200k -> 125k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": high - 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    # 触底
    for i in range(5):
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": 0.00006,
            "high": 0.000065,
            "low": 0.000055,
            "close": 0.00006,
            "volume": "1000000",
            "market_cap": 120.0
        })
        kline_index += 1
    
    # 上涨（涨到 0.00012）
    for i in range(30):
        low = 0.00006 + i * 0.000002
        high = low + 0.000006
        close = high - 0.000001
        market_cap = 120.0 + i * 3  # 120k -> 210k
        raw_klines.append({
            "time": base_time + kline_index * 3600,
            "open": low + 0.000001,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000",
            "market_cap": market_cap
        })
        kline_index += 1
    
    print(f"   总K线数: {len(raw_klines)}")
    print()
    
    return raw_klines


def example_single_token_analysis():
    """示例1: 分析单个币的多次交易"""
    print("=" * 60)
    print("示例1: 分析单个币的多次交易")
    print("=" * 60)
    print()
    
    # 创建K线数据
    raw_klines = create_long_klines_with_multiple_trades()
    
    # 分析交易
    result = analyze_token_trades(
        ca="ExampleToken123",
        raw_klines=raw_klines,
        symbol="EXAMPLE",
        total_capital=2.0,
        min_market_cap=None,  # 不使用市值过滤
        max_trades=5
    )
    
    # 打印结果
    print_token_trades_summary(result)


def example_multiple_tokens_analysis():
    """示例2: 批量分析多个币的胜率"""
    print("=" * 60)
    print("示例2: 批量分析多个币的胜率")
    print("=" * 60)
    print()
    
    # 模拟10个币的数据
    tokens = [
        {"ca": f"Token{i:03d}", "symbol": f"TK{i:03d}"}
        for i in range(1, 11)
    ]
    
    print(f"📊 分析 {len(tokens)} 个币...")
    print()
    
    all_trades = []
    
    for i, token in enumerate(tokens, 1):
        print(f"  [{i}/{len(tokens)}] 分析 {token['symbol']}...")
        
        # 为每个币创建不同的K线数据（模拟不同的交易结果）
        raw_klines = create_long_klines_with_multiple_trades()
        
        # 分析交易
        result = analyze_token_trades(
            ca=token['ca'],
            raw_klines=raw_klines,
            symbol=token['symbol'],
            total_capital=2.0,
            max_trades=3
        )
        
        all_trades.append(result)
    
    print()
    print(f"✅ 完成分析")
    print()
    
    # 统计胜率
    stats = calculate_win_rate_stats(all_trades, min_sample_size=3)
    
    # 打印报告
    print_win_rate_report(stats)


def example_with_market_cap_filter():
    """示例3: 使用市值过滤的胜率分析"""
    print("=" * 60)
    print("示例3: 使用180k市值过滤的胜率分析")
    print("=" * 60)
    print()
    
    raw_klines = create_long_klines_with_multiple_trades()
    
    # 使用市值过滤
    result = analyze_token_trades(
        ca="FilteredToken",
        raw_klines=raw_klines,
        symbol="FILTERED",
        total_capital=2.0,
        min_market_cap=180.0,  # 使用180k过滤
        max_trades=5
    )
    
    print_token_trades_summary(result)


if __name__ == "__main__":
    print("\n")
    print("🚀 交易胜率分析示例")
    print("=" * 60)
    print()
    
    # 运行示例
    example_single_token_analysis()
    print("\n" + "=" * 60 + "\n")
    
    example_multiple_tokens_analysis()
    print("\n" + "=" * 60 + "\n")
    
    example_with_market_cap_filter()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)
    print()
    
    print("💡 使用提示:")
    print("  1. 准备足够长的K线数据（建议30-90天）")
    print("  2. 使用 analyze_token_trades() 分析单个币")
    print("  3. 使用 calculate_win_rate_stats() 统计多个币的胜率")
    print("  4. 使用 print_win_rate_report() 查看报告")
    print()
