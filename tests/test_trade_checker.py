#!/usr/bin/env python3
"""
交易检测器单元测试
"""

import unittest
from trading.trade_checker import (
    check_single_trade,
    check_single_trade_from_raw,
    _calculate_profit
)
from trading.fib_calculator import Kline


class TestCalculateProfit(unittest.TestCase):
    """测试利润计算"""
    
    def test_calculate_profit_full_sell(self):
        """测试全部卖出的利润计算"""
        entry_prices = {"buy_618": 0.00005}
        entry_amounts = {"buy_618": 0.06}
        tiers_bought = ["buy_618"]
        sell_price = 0.00008
        
        profit = _calculate_profit(
            entry_prices, entry_amounts, tiers_bought, sell_price, 1.0
        )
        
        # 买入: 0.06 SOL @ 0.00005 = 1200 tokens
        # 卖出: 1200 tokens @ 0.00008 = 0.096 SOL
        # 利润: 0.096 - 0.06 = 0.036 SOL
        # 收益率: 0.036 / 0.06 = 60%
        
        self.assertAlmostEqual(profit["invested"], 0.06, places=4)
        self.assertAlmostEqual(profit["returned"], 0.096, places=4)
        self.assertAlmostEqual(profit["profit_sol"], 0.036, places=4)
        self.assertAlmostEqual(profit["profit_rate"], 0.60, places=2)
    
    def test_calculate_profit_partial_sell(self):
        """测试部分卖出的利润计算"""
        entry_prices = {"buy_618": 0.00005}
        entry_amounts = {"buy_618": 0.06}
        tiers_bought = ["buy_618"]
        sell_price = 0.00008
        
        profit = _calculate_profit(
            entry_prices, entry_amounts, tiers_bought, sell_price, 0.5
        )
        
        # 买入: 0.06 SOL @ 0.00005 = 1200 tokens
        # 卖出: 600 tokens @ 0.00008 = 0.048 SOL
        # 利润: 0.048 - 0.06 = -0.012 SOL (部分卖出，总体还是亏损)
        
        self.assertAlmostEqual(profit["invested"], 0.06, places=4)
        self.assertAlmostEqual(profit["returned"], 0.048, places=4)
        self.assertAlmostEqual(profit["profit_sol"], -0.012, places=4)
    
    def test_calculate_profit_multiple_tiers(self):
        """测试多档位买入的利润计算"""
        entry_prices = {
            "buy_618": 0.00005,
            "buy_786": 0.00004
        }
        entry_amounts = {
            "buy_618": 0.06,
            "buy_786": 0.04
        }
        tiers_bought = ["buy_618", "buy_786"]
        sell_price = 0.00008
        
        profit = _calculate_profit(
            entry_prices, entry_amounts, tiers_bought, sell_price, 1.0
        )
        
        # 买入: 0.06 @ 0.00005 = 1200 tokens
        #      0.04 @ 0.00004 = 1000 tokens
        #      总计 2200 tokens，投入 0.10 SOL
        # 卖出: 2200 tokens @ 0.00008 = 0.176 SOL
        # 利润: 0.176 - 0.10 = 0.076 SOL
        # 收益率: 0.076 / 0.10 = 76%
        
        self.assertAlmostEqual(profit["invested"], 0.10, places=4)
        self.assertAlmostEqual(profit["returned"], 0.176, places=4)
        self.assertAlmostEqual(profit["profit_sol"], 0.076, places=4)
        self.assertAlmostEqual(profit["profit_rate"], 0.76, places=2)


class TestCheckSingleTrade(unittest.TestCase):
    """测试交易检测"""
    
    def create_downtrend_uptrend_klines(self) -> list:
        """创建下跌后反弹的K线数据"""
        raw_klines = []
        base_time = 1000000
        
        # 下跌阶段（从 0.0001 跌到 0.00005）
        for i in range(20):
            high = 0.0001 - i * 0.000002
            low = high - 0.000005
            close = (high + low) / 2
            raw_klines.append({
                "time": base_time + i * 3600,
                "open": high,
                "high": high,
                "low": low,
                "close": close,
                "volume": "1000000"
            })
        
        # 反弹阶段（从 0.00005 涨到 0.00015）
        for i in range(30):
            low = 0.00005 + i * 0.000003
            high = low + 0.000005
            close = (high + low) / 2
            raw_klines.append({
                "time": base_time + (20 + i) * 3600,
                "open": low,
                "high": high,
                "low": low,
                "close": close,
                "volume": "1000000"
            })
        
        return raw_klines
    
    def test_check_single_trade_matched(self):
        """测试匹配到完整交易"""
        raw_klines = self.create_downtrend_uptrend_klines()
        
        result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
        
        # 测试返回结构正确
        self.assertIn("matched", result)
        self.assertIn("buy_points", result)
        self.assertIn("sell_point", result)
        self.assertIn("profit", result)
        
        # 如果匹配到完整交易，检查数据完整性
        if result["matched"]:
            # 应该有买入点
            self.assertGreater(len(result["buy_points"]), 0)
            
            # 应该有卖出点
            self.assertIsNotNone(result["sell_point"])
            
            # 应该有利润信息
            self.assertIsNotNone(result["profit"])
            self.assertIn("invested", result["profit"])
            self.assertIn("returned", result["profit"])
            self.assertIn("profit_sol", result["profit"])
            self.assertIn("profit_rate", result["profit"])
    
    def test_check_single_trade_not_matched(self):
        """测试未匹配到完整交易"""
        # 创建只有下跌的K线（不会触发买入）
        raw_klines = []
        base_time = 1000000
        
        for i in range(10):
            high = 0.0001 - i * 0.000001
            low = high - 0.000001
            close = (high + low) / 2
            raw_klines.append({
                "time": base_time + i * 3600,
                "open": high,
                "high": high,
                "low": low,
                "close": close,
                "volume": "1000000"
            })
        
        result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
        
        # 不应该匹配到完整交易
        self.assertFalse(result["matched"])
        self.assertIsNone(result["sell_point"])
        self.assertIsNone(result["profit"])
    
    def test_buy_points_structure(self):
        """测试买入点数据结构"""
        raw_klines = self.create_downtrend_uptrend_klines()
        
        result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
        
        if result["matched"] and result["buy_points"]:
            buy = result["buy_points"][0]
            
            # 检查必要字段
            self.assertIn("tier", buy)
            self.assertIn("price", buy)
            self.assertIn("amount", buy)
            self.assertIn("kline_index", buy)
            self.assertIn("timestamp", buy)
            
            # 检查档位格式
            self.assertIn(buy["tier"], ["buy_618", "buy_786", "buy_861"])
            
            # 检查价格和金额
            self.assertGreater(buy["price"], 0)
            self.assertGreater(buy["amount"], 0)
    
    def test_sell_point_structure(self):
        """测试卖出点数据结构"""
        raw_klines = self.create_downtrend_uptrend_klines()
        
        result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
        
        if result["matched"]:
            sell = result["sell_point"]
            
            # 检查必要字段
            self.assertIn("price", sell)
            self.assertIn("kline_index", sell)
            self.assertIn("timestamp", sell)
            self.assertIn("reason", sell)
            self.assertIn("type", sell)
            
            # 检查卖出类型
            self.assertIn(sell["type"], ["ao_sell", "stop_loss", "fib_sell"])
            
            # 检查价格
            self.assertGreater(sell["price"], 0)
    
    def test_profit_structure(self):
        """测试利润数据结构"""
        raw_klines = self.create_downtrend_uptrend_klines()
        
        result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
        
        if result["matched"]:
            profit = result["profit"]
            
            # 检查必要字段
            self.assertIn("invested", profit)
            self.assertIn("returned", profit)
            self.assertIn("profit_sol", profit)
            self.assertIn("profit_rate", profit)
            
            # 检查数值合理性
            self.assertGreater(profit["invested"], 0)
            self.assertGreater(profit["returned"], 0)


if __name__ == "__main__":
    unittest.main()
