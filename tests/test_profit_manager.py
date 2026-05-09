#!/usr/bin/env python3
"""
止盈止损管理器单元测试
"""

import unittest
from trading.profit_manager import ProfitManager, ProfitAction


class TestProfitManager(unittest.TestCase):
    """测试止盈止损管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.pm = ProfitManager(
            profit_target_50=0.50,
            profit_target_100=1.00,
            ao_threshold_normal=0.00003500,
            ao_profit_threshold=0.50
        )
    
    def test_calculate_profit_rate(self):
        """测试收益率计算"""
        profit_rate = self.pm.calculate_profit_rate(
            current_price=0.00006,
            avg_price=0.00004
        )
        
        expected = (0.00006 - 0.00004) / 0.00004
        self.assertAlmostEqual(profit_rate, expected, places=4)
        self.assertAlmostEqual(profit_rate, 0.50, places=4)  # 50%
    
    def test_calculate_profit_rate_zero_avg(self):
        """测试零平均价"""
        profit_rate = self.pm.calculate_profit_rate(
            current_price=0.00006,
            avg_price=0
        )
        
        self.assertEqual(profit_rate, 0.0)
    
    def test_check_profit_target_50(self):
        """测试 50% 止盈"""
        action = self.pm.check_profit_target(
            current_price=0.00006001,  # 略高于 50% 收益，避免浮点数精度问题
            avg_price=0.00004,
            profit_50_sold=False,
            ao_active=False
        )
        
        # 50% 收益应该触发卖出
        self.assertTrue(action.should_sell, f"Expected should_sell=True, got {action.should_sell}, reason: {action.reason}")
        self.assertEqual(action.percentage, 0.5)
        self.assertIn("50%", action.reason)
        self.assertGreaterEqual(action.profit_rate, 0.50)
    
    def test_check_profit_target_50_already_sold(self):
        """测试已卖出 50%"""
        action = self.pm.check_profit_target(
            current_price=0.00006,
            avg_price=0.00004,
            profit_50_sold=True,  # 已卖过
            ao_active=False
        )
        
        self.assertFalse(action.should_sell)
    
    def test_check_profit_target_100(self):
        """测试 100% 止盈"""
        action = self.pm.check_profit_target(
            current_price=0.00008,  # 100% 收益
            avg_price=0.00004,
            profit_50_sold=True,
            ao_active=False
        )
        
        self.assertTrue(action.should_sell)
        self.assertEqual(action.percentage, 1.0)
        self.assertIn("100%", action.reason)
        self.assertAlmostEqual(action.profit_rate, 1.00, places=4)
    
    def test_check_profit_target_ao_active(self):
        """测试 AO 已启动时不使用固定止盈"""
        action = self.pm.check_profit_target(
            current_price=0.00008,
            avg_price=0.00004,
            profit_50_sold=False,
            ao_active=True  # AO 已启动
        )
        
        self.assertFalse(action.should_sell)
        self.assertIn("AO已启动", action.reason)
    
    def test_check_profit_target_invalid_price(self):
        """测试无效价格"""
        action = self.pm.check_profit_target(
            current_price=0.00006,
            avg_price=0,
            profit_50_sold=False,
            ao_active=False
        )
        
        self.assertFalse(action.should_sell)
        self.assertIn("无效", action.reason)
    
    def test_check_ao_sell_signal_high_ao(self):
        """测试 AO >= 35k 绿转红"""
        ao_values = [None] * 30 + [
            0.00003000,  # n-2
            0.00004000,  # n-1 (绿)
            0.00003800,  # n-0 (红)
        ]
        
        should_sell, reason = self.pm.check_ao_sell_signal(ao_values)
        
        self.assertTrue(should_sell)
        self.assertIn("35k", reason)
    
    def test_check_ao_sell_signal_low_ao_with_profit(self):
        """测试 AO < 35k 但收益率 > 50%"""
        ao_values = [None] * 30 + [
            0.00002000,  # n-2
            0.00003000,  # n-1 (绿)
            0.00002500,  # n-0 (红)
        ]
        
        should_sell, reason = self.pm.check_ao_sell_signal(
            ao_values,
            entry_price=0.00004,
            current_price=0.00007  # 75% 收益
        )
        
        self.assertTrue(should_sell)
        self.assertIn("收益率", reason)
    
    def test_check_ao_sell_signal_low_ao_without_profit(self):
        """测试 AO < 35k 且收益率不足"""
        ao_values = [None] * 30 + [
            0.00002000,  # n-2
            0.00003000,  # n-1 (绿)
            0.00002500,  # n-0 (红)
        ]
        
        should_sell, reason = self.pm.check_ao_sell_signal(
            ao_values,
            entry_price=0.00004,
            current_price=0.00005  # 25% 收益
        )
        
        self.assertFalse(should_sell)
        self.assertIn("收益率不足", reason)
    
    def test_check_ao_sell_signal_no_green_to_red(self):
        """测试未触发绿转红"""
        ao_values = [None] * 30 + [
            0.00003000,  # n-2
            0.00004000,  # n-1 (绿)
            0.00005000,  # n-0 (绿，继续上涨)
        ]
        
        should_sell, reason = self.pm.check_ao_sell_signal(ao_values)
        
        self.assertFalse(should_sell)
        self.assertIn("未触发", reason)
    
    def test_check_ao_sell_signal_below_zero(self):
        """测试 AO 在零轴下方"""
        ao_values = [None] * 30 + [
            -0.00003000,  # n-2
            -0.00002000,  # n-1 (绿，上升)
            -0.00002500,  # n-0 (红，下降)
        ]
        
        should_sell, reason = self.pm.check_ao_sell_signal(ao_values)
        
        self.assertFalse(should_sell)
        self.assertIn("未触发", reason)
    
    def test_check_ao_sell_signal_insufficient_data(self):
        """测试数据不足"""
        ao_values = [None, None]
        
        should_sell, reason = self.pm.check_ao_sell_signal(ao_values)
        
        self.assertFalse(should_sell)
        self.assertIn("数据不足", reason)
    
    def test_check_stop_loss_triggered(self):
        """测试触发止损"""
        should_stop, reason = self.pm.check_stop_loss(
            current_price=0.00003,
            stop_price=0.000035
        )
        
        self.assertTrue(should_stop)
        self.assertIn("止损", reason)
    
    def test_check_stop_loss_not_triggered(self):
        """测试未触发止损"""
        should_stop, reason = self.pm.check_stop_loss(
            current_price=0.00004,
            stop_price=0.000035
        )
        
        self.assertFalse(should_stop)
        self.assertIn("未触发", reason)
    
    def test_check_stop_loss_invalid_price(self):
        """测试无效止损价"""
        should_stop, reason = self.pm.check_stop_loss(
            current_price=0.00004,
            stop_price=0
        )
        
        self.assertFalse(should_stop)
        self.assertIn("无效", reason)
    
    def test_is_ao_active_true(self):
        """测试 AO 已启动"""
        # 需要至少 34 个有效值
        ao_values = [None] * 10 + [0.00002, 0.00003, 0.00004, 0.00005, 0.00004] * 8
        
        is_active = self.pm.is_ao_active(ao_values)
        
        self.assertTrue(is_active)
    
    def test_is_ao_active_false_too_small(self):
        """测试 AO 未启动（值太小）"""
        ao_values = [0.0000001] * 40
        
        is_active = self.pm.is_ao_active(ao_values)
        
        self.assertFalse(is_active)
    
    def test_is_ao_active_false_insufficient_data(self):
        """测试 AO 未启动（数据不足）"""
        ao_values = [0.00002] * 20  # < 34
        
        is_active = self.pm.is_ao_active(ao_values)
        
        self.assertFalse(is_active)
    
    def test_is_ao_active_empty(self):
        """测试空 AO 数据"""
        ao_values = []
        
        is_active = self.pm.is_ao_active(ao_values)
        
        self.assertFalse(is_active)


if __name__ == "__main__":
    unittest.main()
