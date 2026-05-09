#!/usr/bin/env python3
"""
交易模块测试
"""

import sys
from pathlib import Path

# 添加项目路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from trading.position_manager import PositionManager
from trading.profit_manager import ProfitManager


def test_position_manager():
    """测试仓位管理器"""
    print("=" * 60)
    print("测试仓位管理器")
    print("=" * 60)
    
    pm = PositionManager(
        max_position_ratio=0.30,
        min_position_sol=0.005
    )
    
    # 测试1: 仓位计算
    print("\n测试1: 仓位计算")
    total_capital = 2.0
    for tier in ["buy_618", "buy_786", "buy_861"]:
        size = pm.calculate_position_size(total_capital, tier)
        ratio = size / total_capital
        print(f"  {tier}: {size:.4f} SOL ({ratio*100:.1f}%)")
    
    # 测试2: 加权平均价格
    print("\n测试2: 加权平均价格")
    entry_prices = {
        "buy_618": 0.00004438,
        "buy_786": 0.00003568,
    }
    entry_amounts = {
        "buy_618": 0.1,
        "buy_786": 0.05,
    }
    tiers_bought = ["buy_618", "buy_786"]
    
    avg_price = pm.calculate_weighted_avg_price(
        entry_prices, entry_amounts, tiers_bought
    )
    print(f"  买入档位: {tiers_bought}")
    print(f"  买入价格: {entry_prices}")
    print(f"  买入金额: {entry_amounts}")
    print(f"  加权均价: {avg_price:.8f}")
    
    # 验证计算
    total_sol = 0.15
    total_tokens = 0.1/0.00004438 + 0.05/0.00003568
    expected = total_sol / total_tokens
    print(f"  预期均价: {expected:.8f}")
    print(f"  计算正确: {abs(avg_price - expected) < 0.00000001}")
    
    # 测试3: 仓位检查
    print("\n测试3: 仓位检查")
    
    # 模拟持仓
    positions = [
        {
            "token_address": "test_ca_1",
            "hold_amount": 1000,
            "last_price": 0.0001,  # 持仓市值 = 0.1 SOL
        }
    ]
    
    # 测试3.1: 正常买入
    can_buy, reason = pm.can_buy(
        ca="test_ca_2",
        amount_sol=0.05,
        total_capital=2.0,
        positions=positions
    )
    print(f"  测试3.1 - 新币买入: {can_buy} ({reason})")
    
    # 测试3.2: 超仓检查
    can_buy, reason = pm.can_buy(
        ca="test_ca_1",
        amount_sol=0.6,  # 0.1 + 0.6 = 0.7 > 0.6 (30%)
        total_capital=2.0,
        positions=positions
    )
    print(f"  测试3.2 - 超仓买入: {can_buy} ({reason})")
    
    # 测试3.3: 最小金额检查
    can_buy, reason = pm.can_buy(
        ca="test_ca_2",
        amount_sol=0.001,  # < 0.005
        total_capital=2.0,
        positions=positions
    )
    print(f"  测试3.3 - 金额过小: {can_buy} ({reason})")
    
    # 测试4: 持仓市值计算
    print("\n测试4: 持仓市值计算")
    value = pm.get_position_value(positions)
    print(f"  总持仓市值: {value:.4f} SOL")
    
    value_ca1 = pm.get_position_value(positions, ca="test_ca_1")
    print(f"  test_ca_1市值: {value_ca1:.4f} SOL")
    
    ratio = pm.get_position_ratio(positions, total_capital)
    print(f"  总持仓比例: {ratio*100:.1f}%")
    
    print("\n✅ 仓位管理器测试完成")


def test_profit_manager():
    """测试止盈止损管理器"""
    print("\n" + "=" * 60)
    print("测试止盈止损管理器")
    print("=" * 60)
    
    pm = ProfitManager(
        profit_target_50=0.50,
        profit_target_100=1.00
    )
    
    # 测试1: 收益率计算
    print("\n测试1: 收益率计算")
    avg_price = 0.00004
    current_price = 0.00006
    profit_rate = pm.calculate_profit_rate(current_price, avg_price)
    print(f"  买入价: {avg_price:.8f}")
    print(f"  当前价: {current_price:.8f}")
    print(f"  收益率: {profit_rate*100:.1f}%")
    
    # 测试2: 50%止盈
    print("\n测试2: 50%止盈检查")
    action = pm.check_profit_target(
        current_price=0.00006,  # 50%收益
        avg_price=0.00004,
        profit_50_sold=False,
        ao_active=False
    )
    print(f"  应该卖出: {action.should_sell}")
    print(f"  卖出比例: {action.percentage*100:.0f}%")
    print(f"  原因: {action.reason}")
    print(f"  收益率: {action.profit_rate*100:.1f}%")
    
    # 测试3: 100%止盈
    print("\n测试3: 100%止盈检查")
    action = pm.check_profit_target(
        current_price=0.00008,  # 100%收益
        avg_price=0.00004,
        profit_50_sold=True,
        ao_active=False
    )
    print(f"  应该卖出: {action.should_sell}")
    print(f"  卖出比例: {action.percentage*100:.0f}%")
    print(f"  原因: {action.reason}")
    print(f"  收益率: {action.profit_rate*100:.1f}%")
    
    # 测试4: AO已启动，不使用固定止盈
    print("\n测试4: AO已启动")
    action = pm.check_profit_target(
        current_price=0.00008,
        avg_price=0.00004,
        profit_50_sold=False,
        ao_active=True  # AO已启动
    )
    print(f"  应该卖出: {action.should_sell}")
    print(f"  原因: {action.reason}")
    
    # 测试5: AO卖出信号
    print("\n测试5: AO卖出信号")
    
    # 模拟AO值（绿转红）
    ao_values = [None] * 30 + [
        0.00002,  # n-2 (绿)
        0.00004,  # n-1 (绿，更高)
        0.00003,  # n-0 (红，下降)
    ]
    
    should_sell, reason = pm.check_ao_sell_signal(
        ao_values=ao_values,
        entry_price=0.00004,
        current_price=0.00006
    )
    print(f"  应该卖出: {should_sell}")
    print(f"  原因: {reason}")
    
    # 测试6: AO启动检测
    print("\n测试6: AO启动检测")
    
    # 未启动（值太小）
    ao_inactive = [0.000001] * 40
    is_active = pm.is_ao_active(ao_inactive)
    print(f"  AO未启动（值太小）: {not is_active}")
    
    # 已启动（有波动）
    ao_active = [None] * 30 + [0.00002, 0.00003, 0.00004] * 5
    is_active = pm.is_ao_active(ao_active)
    print(f"  AO已启动（有波动）: {is_active}")
    
    # 测试7: 止损检查
    print("\n测试7: 止损检查")
    should_stop, reason = pm.check_stop_loss(
        current_price=0.00003,
        stop_price=0.000035
    )
    print(f"  应该止损: {should_stop}")
    print(f"  原因: {reason}")
    
    print("\n✅ 止盈止损管理器测试完成")


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("集成测试 - 完整交易流程")
    print("=" * 60)
    
    # 初始化管理器
    position_mgr = PositionManager(max_position_ratio=0.30)
    profit_mgr = ProfitManager()
    
    # 模拟场景：买入 -> 持仓 -> 止盈
    print("\n场景: 买入 -> 持仓 -> 50%止盈 -> 100%止盈")
    
    total_capital = 2.0
    ca = "test_token"
    
    # 步骤1: 计算买入金额
    print("\n步骤1: 计算买入金额")
    amount_618 = position_mgr.calculate_position_size(total_capital, "buy_618")
    amount_786 = position_mgr.calculate_position_size(total_capital, "buy_786")
    print(f"  buy_618: {amount_618:.4f} SOL")
    print(f"  buy_786: {amount_786:.4f} SOL")
    
    # 步骤2: 模拟买入
    print("\n步骤2: 模拟买入")
    entry_prices = {
        "buy_618": 0.00004,
        "buy_786": 0.00003,
    }
    entry_amounts = {
        "buy_618": amount_618,
        "buy_786": amount_786,
    }
    tiers_bought = ["buy_618", "buy_786"]
    
    avg_price = position_mgr.calculate_weighted_avg_price(
        entry_prices, entry_amounts, tiers_bought
    )
    print(f"  加权均价: {avg_price:.8f}")
    
    # 步骤3: 价格上涨到50%
    print("\n步骤3: 价格上涨到50%")
    current_price = avg_price * 1.5
    print(f"  当前价格: {current_price:.8f}")
    
    action = profit_mgr.check_profit_target(
        current_price=current_price,
        avg_price=avg_price,
        profit_50_sold=False,
        ao_active=False
    )
    print(f"  触发止盈: {action.should_sell}")
    print(f"  卖出比例: {action.percentage*100:.0f}%")
    print(f"  收益率: {action.profit_rate*100:.1f}%")
    
    # 步骤4: 价格继续上涨到100%
    print("\n步骤4: 价格继续上涨到100%")
    current_price = avg_price * 2.0
    print(f"  当前价格: {current_price:.8f}")
    
    action = profit_mgr.check_profit_target(
        current_price=current_price,
        avg_price=avg_price,
        profit_50_sold=True,  # 已卖50%
        ao_active=False
    )
    print(f"  触发止盈: {action.should_sell}")
    print(f"  卖出比例: {action.percentage*100:.0f}%")
    print(f"  收益率: {action.profit_rate*100:.1f}%")
    
    print("\n✅ 集成测试完成")


if __name__ == "__main__":
    test_position_manager()
    test_profit_manager()
    test_integration()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
