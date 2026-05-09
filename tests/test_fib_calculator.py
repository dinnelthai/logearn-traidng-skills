#!/usr/bin/env python3
"""
Fibonacci 计算器单元测试
"""

import unittest
from trading.fib_calculator import (
    Kline,
    parse_klines,
    median_price,
    sma,
    calc_ao,
    ao_bars,
    fib_entry_levels,
    fib_sell_levels,
    check_penetration_with_tolerance,
    ao_sell_signal,
    fib_sell_signal,
    zigzag_pivots,
    _swing_from_klines,
)
from trading.config import FibonacciConfig, AOConfig


class TestKlineParser(unittest.TestCase):
    """测试 K线解析"""
    
    def test_parse_klines(self):
        """测试解析 K线数据"""
        raw = [
            {
                "time": 1000000,
                "open": "0.00005",
                "high": "0.00006",
                "low": "0.00004",
                "close": "0.000055",
                "volume": "1000000"
            }
        ]
        
        klines = parse_klines(raw)
        
        self.assertEqual(len(klines), 1)
        self.assertEqual(klines[0].time, 1000000)
        self.assertEqual(klines[0].open, 0.00005)
        self.assertEqual(klines[0].high, 0.00006)
        self.assertEqual(klines[0].low, 0.00004)
        self.assertEqual(klines[0].close, 0.000055)
        self.assertEqual(klines[0].volume, 1000000)
    
    def test_parse_klines_no_volume(self):
        """测试解析无成交量的 K线"""
        raw = [
            {
                "time": 1000000,
                "open": "0.00005",
                "high": "0.00006",
                "low": "0.00004",
                "close": "0.000055"
            }
        ]
        
        klines = parse_klines(raw)
        self.assertEqual(klines[0].volume, 0.0)


class TestAOCalculation(unittest.TestCase):
    """测试 AO 计算"""
    
    def test_median_price(self):
        """测试中位价计算"""
        k = Kline(time=1000000, open=0.00005, high=0.00006, low=0.00004, close=0.000055, volume=1000)
        
        mp = median_price(k)
        expected = (0.00006 + 0.00004) / 2
        
        self.assertEqual(mp, expected)
    
    def test_sma(self):
        """测试简单移动平均"""
        values = [1, 2, 3, 4, 5]
        
        result = sma(values, 3)
        
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertEqual(result[2], 2.0)  # (1+2+3)/3
        self.assertEqual(result[3], 3.0)  # (2+3+4)/3
        self.assertEqual(result[4], 4.0)  # (3+4+5)/3
    
    def test_calc_ao(self):
        """测试 AO 计算"""
        klines = [
            Kline(time=i, open=0.00005, high=0.00006, low=0.00004, close=0.000055, volume=1000)
            for i in range(40)
        ]
        
        ao = calc_ao(klines, fast=5, slow=34)
        
        self.assertEqual(len(ao), 40)
        # 前 33 个应该是 None
        for i in range(33):
            self.assertIsNone(ao[i])
        # 后面应该有值（虽然可能接近0，因为价格恒定）
        self.assertIsNotNone(ao[34])
    
    def test_ao_bars(self):
        """测试 AO 柱状图数据"""
        ao_values = [None, None, 0.00001, 0.00002, 0.00001]
        
        bars = ao_bars(ao_values)
        
        self.assertEqual(len(bars), 5)
        self.assertEqual(bars[0]["color"], "dim")
        self.assertEqual(bars[1]["color"], "dim")
        self.assertEqual(bars[2]["color"], "green")  # 第一个有效值
        self.assertEqual(bars[3]["color"], "green")  # 0.00002 >= 0.00001
        self.assertEqual(bars[4]["color"], "red")    # 0.00001 < 0.00002


class TestFibonacciLevels(unittest.TestCase):
    """测试 Fibonacci 档位计算"""
    
    def test_fib_entry_levels(self):
        """测试买入档位计算"""
        swing_high = 0.00010
        swing_low = 0.00005
        
        levels = fib_entry_levels(swing_high, swing_low)
        
        diff = swing_high - swing_low  # 0.00005
        
        self.assertAlmostEqual(levels["buy_618"], swing_high - diff * 0.618, places=8)
        self.assertAlmostEqual(levels["buy_786"], swing_high - diff * 0.786, places=8)
        self.assertAlmostEqual(levels["buy_861"], swing_high - diff * 0.861, places=8)
        self.assertAlmostEqual(levels["stop"], swing_high - diff * 0.920, places=8)
    
    def test_fib_entry_levels_invalid(self):
        """测试无效波峰波谷"""
        levels = fib_entry_levels(0.00005, 0.00010)  # swing_high < swing_low
        
        self.assertEqual(levels, {})
    
    def test_fib_sell_levels(self):
        """测试卖出档位计算"""
        swing_high = 0.00010
        swing_low = 0.00005
        
        levels = fib_sell_levels(swing_high, swing_low)
        
        diff = swing_high - swing_low  # 0.00005
        
        self.assertAlmostEqual(levels["sell_100"], swing_high, places=8)
        self.assertAlmostEqual(levels["sell_1272"], swing_high + diff * 0.272, places=8)


class TestPenetrationDetection(unittest.TestCase):
    """测试穿透检测"""
    
    def test_shallow_penetration_valid(self):
        """测试浅插针有效穿透"""
        config = FibonacciConfig()
        
        # 插针 1%，收盘回升 2%
        latest_low = 0.00004950
        latest_close = 0.00005100
        level_price = 0.00005000
        
        result = check_penetration_with_tolerance(latest_low, latest_close, level_price, config)
        
        self.assertTrue(result)
    
    def test_shallow_penetration_invalid(self):
        """测试浅插针假突破"""
        config = FibonacciConfig()
        
        # 插针 1%，收盘回升 6%（超过容差）
        latest_low = 0.00004950
        latest_close = 0.00005300
        level_price = 0.00005000
        
        result = check_penetration_with_tolerance(latest_low, latest_close, level_price, config)
        
        self.assertFalse(result)
    
    def test_deep_penetration_valid(self):
        """测试深插针有效穿透"""
        config = FibonacciConfig()
        
        # 插针 4%，收盘回升 4%
        latest_low = 0.00004800
        latest_close = 0.00005200
        level_price = 0.00005000
        
        result = check_penetration_with_tolerance(latest_low, latest_close, level_price, config)
        
        self.assertTrue(result)
    
    def test_no_penetration(self):
        """测试未穿透"""
        config = FibonacciConfig()
        
        latest_low = 0.00005100
        latest_close = 0.00005200
        level_price = 0.00005000
        
        result = check_penetration_with_tolerance(latest_low, latest_close, level_price, config)
        
        self.assertFalse(result)


class TestAOSellSignal(unittest.TestCase):
    """测试 AO 卖出信号"""
    
    def test_ao_high_green_to_red(self):
        """测试 AO >= 35k 绿转红"""
        config = AOConfig()
        
        ao_values = [None] * 30 + [
            0.00003000,  # n-2
            0.00004000,  # n-1 (绿)
            0.00003800,  # n-0 (红)
        ]
        
        signal = ao_sell_signal(ao_values, config=config)
        
        self.assertEqual(signal["action"], "sell")
        self.assertIn("35k", signal["reason"])
    
    def test_ao_low_with_profit(self):
        """测试 AO < 35k 但收益率 > 50%"""
        config = AOConfig()
        
        ao_values = [None] * 30 + [
            0.00002000,  # n-2
            0.00003000,  # n-1 (绿)
            0.00002500,  # n-0 (红)
        ]
        
        signal = ao_sell_signal(
            ao_values,
            entry_price=0.00004000,
            current_price=0.00007000,  # 75% 收益
            config=config
        )
        
        self.assertEqual(signal["action"], "sell")
        self.assertIn("收益率", signal["reason"])
    
    def test_ao_low_without_profit(self):
        """测试 AO < 35k 且收益率不足"""
        config = AOConfig()
        
        ao_values = [None] * 30 + [
            0.00002000,  # n-2
            0.00003000,  # n-1 (绿)
            0.00002500,  # n-0 (红)
        ]
        
        signal = ao_sell_signal(
            ao_values,
            entry_price=0.00004000,
            current_price=0.00005000,  # 25% 收益
            config=config
        )
        
        # Bug Fix: 应该返回 watch 而不是空字典
        self.assertEqual(signal["action"], "watch")
        self.assertIn("无持仓价格信息", signal["reason"])
    
    def test_ao_no_green_to_red(self):
        """测试未触发绿转红"""
        config = AOConfig()
        
        ao_values = [None] * 30 + [
            0.00003000,  # n-2
            0.00004000,  # n-1 (绿)
            0.00005000,  # n-0 (绿，继续上涨)
        ]
        
        signal = ao_sell_signal(ao_values, config=config)
        
        self.assertEqual(signal, {})
    
    def test_ao_insufficient_data(self):
        """测试数据不足"""
        ao_values = [None, None]
        
        signal = ao_sell_signal(ao_values)
        
        self.assertEqual(signal, {})


class TestFibSellSignal(unittest.TestCase):
    """测试 Fibonacci 卖出信号"""
    
    def test_sell_100_trigger(self):
        """测试触达 100% 位"""
        swing_high = 0.00010
        swing_low = 0.00005
        current_price = 0.00010  # 回到波峰
        
        signal = fib_sell_signal(swing_high, swing_low, current_price)
        
        self.assertEqual(signal["action"], "fib_sell")
        self.assertEqual(signal["tier"], "sell_100")
        self.assertEqual(signal["percentage"], 0.30)
    
    def test_sell_1272_trigger(self):
        """测试触达 127.2% 位"""
        swing_high = 0.00010
        swing_low = 0.00005
        diff = swing_high - swing_low
        current_price = swing_high + diff * 0.272  # 127.2% 扩展位
        
        # 需要先标记 sell_100 已卖出，才能触发 sell_1272
        fib_sold_tiers = ["sell_100"]
        signal = fib_sell_signal(swing_high, swing_low, current_price, fib_sold_tiers)
        
        self.assertEqual(signal["action"], "fib_sell")
        self.assertEqual(signal["tier"], "sell_1272")
        self.assertEqual(signal["percentage"], 0.50)
    
    def test_already_sold_tier(self):
        """测试已卖出的档位不再触发"""
        swing_high = 0.00010
        swing_low = 0.00005
        current_price = 0.00010
        fib_sold_tiers = ["sell_100"]
        
        signal = fib_sell_signal(swing_high, swing_low, current_price, fib_sold_tiers)
        
        # 应该跳过 sell_100，检查 sell_1272
        self.assertEqual(signal, {})
    
    def test_no_trigger(self):
        """测试未触达任何档位"""
        swing_high = 0.00010
        swing_low = 0.00005
        current_price = 0.00008  # 低于波峰
        
        signal = fib_sell_signal(swing_high, swing_low, current_price)
        
        self.assertEqual(signal, {})


class TestZigzagPivots(unittest.TestCase):
    """测试 ZIGZAG 拐点检测"""
    
    def test_zigzag_simple(self):
        """测试简单的 ZIGZAG 拐点"""
        # 创建一个简单的波动序列
        highs = [5, 6, 7, 8, 9, 10, 9, 8, 7, 6, 5, 4, 5, 6, 7, 8, 9, 10, 11, 12, 11, 10, 9, 8, 7]
        lows = [4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 4, 5, 6, 7, 8, 9, 10, 11, 10, 9, 8, 7, 6]
        
        pivots = zigzag_pivots(highs, lows, deviation=5.0, depth=3, lookback=2)
        
        # 应该检测到一些拐点
        self.assertGreater(len(pivots), 0)
        
        # 检查拐点格式
        for idx, hl, price in pivots:
            self.assertIn(hl, ['H', 'L'])
            self.assertIsInstance(price, (int, float))


class TestSwingFromKlines(unittest.TestCase):
    """测试波峰波谷计算"""
    
    def test_swing_basic(self):
        """测试基本波峰波谷"""
        klines = [
            Kline(time=i, open=5, high=10 - i*0.1, low=5 - i*0.1, close=7, volume=1000)
            for i in range(50)
        ]
        
        swing_high, swing_low = _swing_from_klines(klines)
        
        # swing_low 应该是第一根 K 线的最低价
        self.assertEqual(swing_low, klines[0].low)
        
        # swing_high 应该是某个波峰
        self.assertIsInstance(swing_high, float)
        self.assertGreater(swing_high, swing_low)


if __name__ == "__main__":
    unittest.main()
