#!/usr/bin/env python3
"""
配置模块单元测试
"""

import unittest
from trading.config import (
    FibonacciConfig,
    AOConfig,
    PositionConfig,
    ProfitConfig,
    TradingConfig,
    DEFAULT_CONFIG,
    create_custom_config,
)


class TestFibonacciConfig(unittest.TestCase):
    """测试 Fibonacci 配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = FibonacciConfig()
        
        self.assertEqual(len(config.buy_ratios), 3)
        self.assertEqual(config.buy_ratios[0], ("buy_618", 0.618))
        self.assertEqual(config.buy_ratios[1], ("buy_786", 0.786))
        self.assertEqual(config.buy_ratios[2], ("buy_861", 0.861))
        
        self.assertEqual(config.stop_ratio, 0.920)
        
        self.assertEqual(len(config.sell_ratios), 2)
        self.assertEqual(config.sell_ratios[0], ("sell_100", 1.000))
        self.assertEqual(config.sell_ratios[1], ("sell_1272", 1.272))
        
        self.assertEqual(config.sell_percentages["sell_100"], 0.30)
        self.assertEqual(config.sell_percentages["sell_1272"], 0.50)
    
    def test_custom_values(self):
        """测试自定义值"""
        config = FibonacciConfig(
            stop_ratio=0.95,
            shallow_tolerance=0.03
        )
        
        self.assertEqual(config.stop_ratio, 0.95)
        self.assertEqual(config.shallow_tolerance, 0.03)
    
    def test_zigzag_parameters(self):
        """测试 ZIGZAG 参数"""
        config = FibonacciConfig()
        
        self.assertEqual(config.zigzag_deviation, 5.0)
        self.assertEqual(config.zigzag_depth, 10)
        self.assertEqual(config.zigzag_lookback, 5)
    
    def test_penetration_tolerance(self):
        """测试穿透容差"""
        config = FibonacciConfig()
        
        self.assertEqual(config.shallow_penetration_threshold, 0.03)
        self.assertEqual(config.shallow_tolerance, 0.02)
        self.assertEqual(config.deep_tolerance, 0.05)


class TestAOConfig(unittest.TestCase):
    """测试 AO 配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = AOConfig()
        
        self.assertEqual(config.fast_period, 5)
        self.assertEqual(config.slow_period, 34)
        self.assertEqual(config.threshold_normal, 0.00003500)
        self.assertEqual(config.profit_threshold, 0.50)
    
    def test_custom_values(self):
        """测试自定义值"""
        config = AOConfig(
            threshold_normal=0.00005000,
            profit_threshold=0.60
        )
        
        self.assertEqual(config.threshold_normal, 0.00005000)
        self.assertEqual(config.profit_threshold, 0.60)


class TestPositionConfig(unittest.TestCase):
    """测试仓位配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = PositionConfig()
        
        self.assertEqual(config.max_position_ratio, 0.30)
        self.assertEqual(config.min_position_sol, 0.005)
        
        self.assertEqual(config.tier_sizes["buy_618"], 0.03)
        self.assertEqual(config.tier_sizes["buy_786"], 0.02)
        self.assertEqual(config.tier_sizes["buy_861"], 0.01)
        
        self.assertEqual(config.trading_start_hour, 0)
        self.assertEqual(config.trading_end_hour, 24)  # 默认24小时交易
    
    def test_custom_tier_sizes(self):
        """测试自定义档位大小"""
        custom_tiers = {
            "buy_618": 0.05,
            "buy_786": 0.03,
            "buy_861": 0.02,
        }
        config = PositionConfig(tier_sizes=custom_tiers)
        
        self.assertEqual(config.tier_sizes["buy_618"], 0.05)


class TestProfitConfig(unittest.TestCase):
    """测试止盈配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ProfitConfig()
        
        self.assertEqual(config.profit_target_50, 0.50)
        self.assertEqual(config.profit_target_100, 1.00)
        self.assertEqual(config.profit_50_sell_percentage, 0.50)
        self.assertEqual(config.profit_100_sell_percentage, 1.00)


class TestTradingConfig(unittest.TestCase):
    """测试完整交易配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = TradingConfig()
        
        self.assertIsInstance(config.fibonacci, FibonacciConfig)
        self.assertIsInstance(config.ao, AOConfig)
        self.assertIsInstance(config.position, PositionConfig)
        self.assertIsInstance(config.profit, ProfitConfig)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = create_custom_config(
            fibonacci=FibonacciConfig(stop_ratio=0.95),
            ao=AOConfig(threshold_normal=0.00005000)
        )
        
        self.assertEqual(config.fibonacci.stop_ratio, 0.95)
        self.assertEqual(config.ao.threshold_normal, 0.00005000)
    
    def test_default_config_singleton(self):
        """测试默认配置单例"""
        self.assertIsInstance(DEFAULT_CONFIG, TradingConfig)
        self.assertEqual(DEFAULT_CONFIG.ao.threshold_normal, 0.00003500)


if __name__ == "__main__":
    unittest.main()
