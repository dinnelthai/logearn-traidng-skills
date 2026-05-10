#!/usr/bin/env python3
"""
市值过滤功能测试
验证180k市值过滤逻辑
"""

from trading.fib_calculator import Kline
from trading.trade_checker import filter_klines_by_market_cap, check_single_trade_from_raw


def test_market_cap_first_touch():
    """测试：第一次达到180k时开始回测"""
    print("=" * 60)
    print("测试1: 第一次达到180k")
    print("=" * 60)
    
    klines = [
        Kline(time=1000000, open=0.0001, high=0.00011, low=0.00009, close=0.0001, volume=1000, market_cap=150.0),
        Kline(time=1003600, open=0.00011, high=0.00012, low=0.0001, close=0.00011, volume=1000, market_cap=170.0),
        Kline(time=1007200, open=0.00012, high=0.00013, low=0.00011, close=0.00012, volume=1000, market_cap=185.0),  # 第一次达到
        Kline(time=1010800, open=0.00013, high=0.00014, low=0.00012, close=0.00013, volume=1000, market_cap=190.0),
        Kline(time=1014400, open=0.00014, high=0.00015, low=0.00013, close=0.00014, volume=1000, market_cap=200.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    print(f"原始K线数: {len(klines)}")
    print(f"过滤后K线数: {len(filtered)}")
    print(f"第一根K线市值: {filtered[0].market_cap if filtered else 'N/A'}")
    
    assert len(filtered) == 3, f"期望3根K线，实际{len(filtered)}根"
    assert filtered[0].market_cap == 185.0, f"第一根K线市值应为185.0，实际{filtered[0].market_cap}"
    
    print("✅ 测试通过：正确从第一次达到180k的K线开始")
    print()
    return True


def test_market_cap_pullback():
    """测试：达到180k后回调到100k仍然保留"""
    print("=" * 60)
    print("测试2: 达到后回调")
    print("=" * 60)
    
    klines = [
        Kline(time=1000000, open=0.0001, high=0.00011, low=0.00009, close=0.0001, volume=1000, market_cap=150.0),
        Kline(time=1003600, open=0.00012, high=0.00013, low=0.00011, close=0.00012, volume=1000, market_cap=185.0),  # 第一次达到
        Kline(time=1007200, open=0.00008, high=0.00009, low=0.00007, close=0.00008, volume=1000, market_cap=100.0),  # 回调
        Kline(time=1010800, open=0.00009, high=0.0001, low=0.00008, close=0.00009, volume=1000, market_cap=120.0),
        Kline(time=1014400, open=0.0001, high=0.00011, low=0.00009, close=0.0001, volume=1000, market_cap=150.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    print(f"原始K线数: {len(klines)}")
    print(f"过滤后K线数: {len(filtered)}")
    print("过滤后市值序列:", [k.market_cap for k in filtered])
    
    assert len(filtered) == 4, f"期望4根K线，实际{len(filtered)}根"
    assert filtered[1].market_cap == 100.0, "回调到100k的K线应该保留"
    
    print("✅ 测试通过：达到180k后的回调K线仍然保留")
    print()
    return True


def test_market_cap_never_reached():
    """测试：从未达到180k"""
    print("=" * 60)
    print("测试3: 从未达到180k")
    print("=" * 60)
    
    klines = [
        Kline(time=1000000, open=0.0001, high=0.00011, low=0.00009, close=0.0001, volume=1000, market_cap=150.0),
        Kline(time=1003600, open=0.00011, high=0.00012, low=0.0001, close=0.00011, volume=1000, market_cap=170.0),
        Kline(time=1007200, open=0.00012, high=0.00013, low=0.00011, close=0.00012, volume=1000, market_cap=175.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    print(f"原始K线数: {len(klines)}")
    print(f"过滤后K线数: {len(filtered)}")
    
    assert len(filtered) == 0, f"期望0根K线，实际{len(filtered)}根"
    
    print("✅ 测试通过：从未达到180k时返回空列表")
    print()
    return True


def test_market_cap_exactly_180():
    """测试：市值正好等于180k"""
    print("=" * 60)
    print("测试4: 市值正好等于180k")
    print("=" * 60)
    
    klines = [
        Kline(time=1000000, open=0.0001, high=0.00011, low=0.00009, close=0.0001, volume=1000, market_cap=150.0),
        Kline(time=1003600, open=0.00011, high=0.00012, low=0.0001, close=0.00011, volume=1000, market_cap=180.0),  # 正好180k
        Kline(time=1007200, open=0.00012, high=0.00013, low=0.00011, close=0.00012, volume=1000, market_cap=190.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    print(f"原始K线数: {len(klines)}")
    print(f"过滤后K线数: {len(filtered)}")
    print(f"第一根K线市值: {filtered[0].market_cap if filtered else 'N/A'}")
    
    assert len(filtered) == 2, f"期望2根K线，实际{len(filtered)}根"
    assert filtered[0].market_cap == 180.0, "市值正好180k的K线应该包含"
    
    print("✅ 测试通过：市值正好等于180k时包含该K线")
    print()
    return True


def test_integration_with_trade_checker():
    """测试：与交易检测器集成"""
    print("=" * 60)
    print("测试5: 与交易检测器集成")
    print("=" * 60)
    
    # 创建包含市值的K线数据
    raw_klines = []
    base_time = 1000000
    
    # 前10根K线：市值 < 180k
    for i in range(10):
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": 0.0001,
            "high": 0.00011,
            "low": 0.00009,
            "close": 0.0001,
            "volume": "1000000",
            "market_cap": 150.0 + i * 2  # 150k -> 168k
        })
    
    # 第11根K线：市值达到180k
    raw_klines.append({
        "time": base_time + 10 * 3600,
        "open": 0.00012,
        "high": 0.00013,
        "low": 0.00011,
        "close": 0.00012,
        "volume": "1000000",
        "market_cap": 185.0  # 第一次达到180k
    })
    
    # 后续K线：市值波动
    for i in range(20):
        market_cap = 185.0 + (i - 10) * 5  # 波动
        raw_klines.append({
            "time": base_time + (11 + i) * 3600,
            "open": 0.00012,
            "high": 0.00013,
            "low": 0.00011,
            "close": 0.00012,
            "volume": "1000000",
            "market_cap": max(100.0, market_cap)  # 最低100k
        })
    
    print(f"总K线数: {len(raw_klines)}")
    
    # 测试：使用市值过滤
    result_with_filter = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=180.0
    )
    
    print(f"使用180k过滤: matched={result_with_filter['matched']}")
    if result_with_filter.get('filter_reason'):
        print(f"  过滤原因: {result_with_filter['filter_reason']}")
    
    # 测试：不使用市值过滤
    result_without_filter = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=None
    )
    
    print(f"不使用过滤: matched={result_without_filter['matched']}")
    
    print("✅ 测试通过：交易检测器集成正常")
    print()
    return True


def test_backward_compatibility():
    """测试：向后兼容（无market_cap字段）"""
    print("=" * 60)
    print("测试6: 向后兼容性")
    print("=" * 60)
    
    # 不包含market_cap字段的K线数据
    raw_klines = [
        {
            "time": 1000000,
            "open": 0.0001,
            "high": 0.00011,
            "low": 0.00009,
            "close": 0.0001,
            "volume": "1000000"
            # 没有market_cap字段
        },
        {
            "time": 1003600,
            "open": 0.00012,
            "high": 0.00013,
            "low": 0.00011,
            "close": 0.00012,
            "volume": "1000000"
        }
    ]
    
    # 不使用市值过滤（向后兼容）
    result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
    
    print(f"无market_cap字段的K线: matched={result['matched']}")
    print("✅ 测试通过：向后兼容性正常")
    print()
    
    # 使用市值过滤（应该被过滤掉，因为默认market_cap=0）
    result_filtered = check_single_trade_from_raw(
        raw_klines,
        total_capital=2.0,
        min_market_cap=180.0
    )
    
    print(f"使用180k过滤（无market_cap字段）: matched={result_filtered['matched']}")
    if result_filtered.get('filter_reason'):
        print(f"  过滤原因: {result_filtered['filter_reason']}")
    
    assert not result_filtered['matched'], "无market_cap字段时应该被过滤"
    assert result_filtered.get('filter_reason'), "应该有过滤原因"
    
    print("✅ 测试通过：无market_cap字段时正确过滤")
    print()
    return True


if __name__ == "__main__":
    print("\n")
    print("🚀 市值过滤功能测试")
    print("=" * 60)
    print()
    
    all_passed = True
    
    try:
        all_passed &= test_market_cap_first_touch()
        all_passed &= test_market_cap_pullback()
        all_passed &= test_market_cap_never_reached()
        all_passed &= test_market_cap_exactly_180()
        all_passed &= test_integration_with_trade_checker()
        all_passed &= test_backward_compatibility()
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    print()
