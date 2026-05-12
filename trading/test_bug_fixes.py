#!/usr/bin/env python3
"""
Bug修复验证脚本
验证关键Bug是否已修复
"""

def test_check_can_buy_exists():
    """测试 check_can_buy 方法是否存在"""
    from position_manager import PositionManager
    
    pm = PositionManager()
    
    # 验证方法存在
    assert hasattr(pm, 'check_can_buy'), "❌ check_can_buy 方法不存在"
    
    # 验证方法签名
    import inspect
    sig = inspect.signature(pm.check_can_buy)
    params = list(sig.parameters.keys())
    
    expected_params = ['tier', 'tiers_bought', 'total_capital', 'api_price']
    for param in expected_params:
        assert param in params, f"❌ 缺少参数: {param}"
    
    print("✅ BUG #1 已修复: check_can_buy 方法存在且签名正确")


def test_entry_amounts_logic():
    """测试 entry_amounts 数据类型逻辑"""
    from position_manager import PositionManager
    
    pm = PositionManager()
    
    # 模拟数据
    entry_prices = {
        "buy_618": 0.0001,
        "buy_786": 0.00008
    }
    entry_amounts = {
        "buy_618": 0.03,  # SOL金额
        "buy_786": 0.02   # SOL金额
    }
    tiers_bought = ["buy_618", "buy_786"]
    
    # 计算加权均价
    avg_price = pm.calculate_weighted_avg_price(entry_prices, entry_amounts, tiers_bought)
    
    # 验证计算逻辑
    # 总SOL = 0.03 + 0.02 = 0.05
    # 总tokens = 0.03/0.0001 + 0.02/0.00008 = 300 + 250 = 550
    # 加权均价 = 0.05 / 550 = 0.00009090909...
    
    expected_avg = 0.05 / 550
    assert abs(avg_price - expected_avg) < 1e-10, f"❌ 加权均价计算错误: {avg_price} != {expected_avg}"
    
    print(f"✅ BUG #2 已修复: entry_amounts 逻辑正确，加权均价 = {avg_price:.10f}")


def test_tier_sizes_initialized():
    """测试 tier_sizes 是否正确初始化"""
    from position_manager import PositionManager
    
    pm = PositionManager()
    
    assert hasattr(pm, 'tier_sizes'), "❌ tier_sizes 未初始化"
    assert "buy_618" in pm.tier_sizes, "❌ buy_618 档位缺失"
    assert "buy_786" in pm.tier_sizes, "❌ buy_786 档位缺失"
    assert "buy_861" in pm.tier_sizes, "❌ buy_861 档位缺失"
    
    print(f"✅ tier_sizes 已正确初始化: {pm.tier_sizes}")


def test_check_can_buy_logic():
    """测试 check_can_buy 方法的逻辑"""
    from position_manager import PositionManager
    
    pm = PositionManager(
        max_position_ratio=0.30,
        min_position_sol=0.005
    )
    
    # 测试1: 正常买入
    can_buy, reason = pm.check_can_buy(
        tier="buy_618",
        tiers_bought=[],
        total_capital=2.0,
        api_price=0.0001
    )
    assert can_buy, f"❌ 应该允许买入: {reason}"
    print(f"✅ 测试1通过: 正常买入 - {reason}")
    
    # 测试2: 超仓检查
    can_buy, reason = pm.check_can_buy(
        tier="buy_861",
        tiers_bought=["buy_618", "buy_786"],
        total_capital=2.0,
        api_price=0.0001
    )
    # buy_618=3% + buy_786=2% + buy_861=1% = 6% < 30%，应该允许
    assert can_buy, f"❌ 应该允许买入: {reason}"
    print(f"✅ 测试2通过: 仓位检查 - {reason}")
    
    # 测试3: 金额过小
    pm_strict = PositionManager(min_position_sol=1.0)
    can_buy, reason = pm_strict.check_can_buy(
        tier="buy_861",
        tiers_bought=[],
        total_capital=2.0,
        api_price=0.0001
    )
    # buy_861 = 2.0 * 0.01 = 0.02 < 1.0，应该拒绝
    assert not can_buy, f"❌ 应该拒绝买入（金额过小）"
    print(f"✅ 测试3通过: 最小金额检查 - {reason}")


if __name__ == "__main__":
    print("="*80)
    print("🔍 Bug修复验证测试")
    print("="*80)
    print()
    
    try:
        test_check_can_buy_exists()
        print()
        
        test_entry_amounts_logic()
        print()
        
        test_tier_sizes_initialized()
        print()
        
        test_check_can_buy_logic()
        print()
        
        print("="*80)
        print("🎉 所有测试通过！Bug已成功修复")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
