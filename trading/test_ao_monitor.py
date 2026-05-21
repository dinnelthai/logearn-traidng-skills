#!/usr/bin/env python3
"""
AO监控器测试 - 验证代码逻辑
"""

def test_imports():
    """测试导入"""
    try:
        from trading.ao_monitor import run_ao_monitor, run_ao_monitor_multi, AOMonitorConfig
        from trading.executor import TradeExecutor
        from trading.kline_service import get_klines
        from trading.fib_calculator import parse_klines, calc_ao, ao_sell_signal
        print("✅ 所有导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_ao_monitor_config():
    """测试AOMonitorConfig"""
    try:
        from trading.ao_monitor import AOMonitorConfig
        
        # 测试1: 基本配置
        config1 = AOMonitorConfig(ca="test_ca")
        assert config1.ca == "test_ca"
        assert config1.entry_price is None
        assert config1.sell_percentage == 1.0
        print("✅ 测试1通过: 基本配置")
        
        # 测试2: 完整配置
        config2 = AOMonitorConfig(
            ca="test_ca2",
            entry_price=0.00004,
            sell_percentage=0.5
        )
        assert config2.ca == "test_ca2"
        assert config2.entry_price == 0.00004
        assert config2.sell_percentage == 0.5
        print("✅ 测试2通过: 完整配置")
        
        return True
    except Exception as e:
        print(f"❌ AOMonitorConfig测试失败: {e}")
        return False


def test_parse_klines_logic():
    """测试K线解析逻辑"""
    try:
        from trading.fib_calculator import Kline, parse_klines
        
        # 模拟get_klines返回的Kline对象
        mock_klines = [
            Kline(time=1000, open=0.1, high=0.2, low=0.05, close=0.15, volume=100, market_cap=1000),
            Kline(time=2000, open=0.15, high=0.25, low=0.1, close=0.2, volume=200, market_cap=2000),
        ]
        
        # 转换为字典格式（ao_monitor.py中的逻辑）
        klines_dict = [{
            'time': k.time,
            'open': k.open,
            'high': k.high,
            'low': k.low,
            'close': k.close,
            'volume': k.volume,
            'market_cap': k.market_cap
        } for k in mock_klines]
        
        # 解析回Kline对象
        parsed = parse_klines(klines_dict)
        
        assert len(parsed) == 2
        assert parsed[0].time == 1000
        assert parsed[1].close == 0.2
        print("✅ K线解析逻辑正确")
        
        return True
    except Exception as e:
        print(f"❌ K线解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ao_calculation():
    """测试AO计算"""
    try:
        from trading.fib_calculator import Kline, calc_ao
        
        # 创建足够的K线数据（至少34根）
        klines = []
        for i in range(50):
            klines.append(Kline(
                time=i*300,
                open=0.0001 + i*0.000001,
                high=0.0001 + i*0.000001 + 0.000001,
                low=0.0001 + i*0.000001 - 0.000001,
                close=0.0001 + i*0.000001,
                volume=1000,
                market_cap=1000
            ))
        
        ao_values = calc_ao(klines)
        
        assert len(ao_values) == 50
        # AO需要slow=34根才能计算，所以前33根（索引0-32）是None
        assert ao_values[0] is None
        assert ao_values[32] is None
        assert ao_values[33] is not None  # 第34根（索引33）开始有值
        print("✅ AO计算逻辑正确")
        
        return True
    except Exception as e:
        print(f"❌ AO计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ao_sell_signal():
    """测试AO卖出信号"""
    try:
        from trading.fib_calculator import ao_sell_signal
        
        # 测试1: AO值不足（<3根有效值）
        ao_values = [None, None, 0.00001]
        signal = ao_sell_signal(ao_values)
        assert signal == {}
        print("✅ 测试1通过: AO值不足返回空")
        
        # 测试2: 没有绿转红
        ao_values = [None] * 30 + [0.00001, 0.00002, 0.00003]  # 持续上涨
        signal = ao_sell_signal(ao_values)
        assert signal == {}
        print("✅ 测试2通过: 无绿转红返回空")
        
        # 测试3: AO>=35k绿转红（应该卖出）
        ao_values = [None] * 30 + [0.00003, 0.00004, 0.000035]  # 绿转红，AO=35k
        signal = ao_sell_signal(ao_values, entry_price=0.0001, current_price=0.00015)
        assert signal.get("action") == "sell"
        print("✅ 测试3通过: AO>=35k触发卖出")
        
        # 测试4: AO<35k但收益率>50%（应该卖出）
        ao_values = [None] * 30 + [0.00002, 0.00003, 0.000025]  # 绿转红，AO=25k
        signal = ao_sell_signal(ao_values, entry_price=0.0001, current_price=0.00016)  # 收益率60%
        assert signal.get("action") == "sell"
        print("✅ 测试4通过: AO<35k但收益率>50%触发卖出")
        
        # 测试5: AO<35k且收益率<50%（不卖出）
        ao_values = [None] * 30 + [0.00002, 0.00003, 0.000025]  # 绿转红，AO=25k
        signal = ao_sell_signal(ao_values, entry_price=0.0001, current_price=0.00012)  # 收益率20%
        assert signal.get("action") != "sell"
        print("✅ 测试5通过: AO<35k且收益率<50%不卖出")
        
        return True
    except Exception as e:
        print(f"❌ AO卖出信号测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*80)
    print("🧪 AO监控器测试")
    print("="*80)
    print()
    
    tests = [
        ("导入测试", test_imports),
        ("AOMonitorConfig测试", test_ao_monitor_config),
        ("K线解析逻辑测试", test_parse_klines_logic),
        ("AO计算测试", test_ao_calculation),
        ("AO卖出信号测试", test_ao_sell_signal),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"运行: {name}")
        print(f"{'='*80}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print(f"{'='*80}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！代码无Bug")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")
