#!/usr/bin/env python3
"""
技术指标测试
"""

import pytest
from trading.indicators import calculate_rsi, calculate_rsi_series
from trading.fib_calculator import Kline


class TestIndicators:
    """技术指标测试"""
    
    def create_test_klines(self, prices):
        """创建测试K线"""
        klines = []
        for i, price in enumerate(prices):
            kline = Kline(
                time=1000000 + i * 3600,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=1000,
                market_cap=0
            )
            klines.append(kline)
        return klines
    
    def test_calculate_rsi_basic(self):
        """测试RSI计算（基本）"""
        # 创建上涨趋势的K线
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                  120, 122, 124, 126, 128, 130, 132, 134, 136, 138]
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        # 上涨趋势RSI应该偏高
        assert 50 < rsi <= 100
    
    def test_calculate_rsi_downtrend(self):
        """测试RSI计算（下跌趋势）"""
        # 创建下跌趋势的K线
        prices = [138, 136, 134, 132, 130, 128, 126, 124, 122, 120,
                  118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        # 下跌趋势RSI应该偏低
        assert 0 <= rsi < 50
    
    def test_calculate_rsi_sideways(self):
        """测试RSI计算（横盘）"""
        # 创建横盘的K线
        prices = [100, 101, 100, 101, 100, 101, 100, 101, 100, 101,
                  100, 101, 100, 101, 100, 101, 100, 101, 100, 101]
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        # 横盘RSI应该接近50
        assert 40 < rsi < 60
    
    def test_calculate_rsi_insufficient_data(self):
        """测试RSI计算（数据不足）"""
        prices = [100, 102, 104]  # 只有3根K线
        klines = self.create_test_klines(prices)
        
        with pytest.raises(ValueError, match="K线数量不足"):
            calculate_rsi(klines, period=14)
    
    def test_calculate_rsi_exact_minimum_data(self):
        """测试RSI计算（恰好最少数据）"""
        prices = list(range(100, 116))  # 16根K线（period+1+1）
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        assert 0 <= rsi <= 100
    
    def test_calculate_rsi_all_gains(self):
        """测试RSI计算（全部上涨）"""
        prices = list(range(100, 120))  # 持续上涨
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        # 全部上涨RSI应该接近100
        assert rsi == 100.0
    
    def test_calculate_rsi_all_losses(self):
        """测试RSI计算（全部下跌）"""
        prices = list(range(120, 100, -1))  # 持续下跌
        klines = self.create_test_klines(prices)
        
        rsi = calculate_rsi(klines, period=14)
        
        # 全部下跌RSI应该接近0
        assert 0 <= rsi < 10
    
    def test_calculate_rsi_series_basic(self):
        """测试RSI序列计算（基本）"""
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                  120, 122, 124, 126, 128, 130, 132, 134, 136, 138]
        klines = self.create_test_klines(prices)
        
        rsi_values = calculate_rsi_series(klines, period=14)
        
        assert len(rsi_values) == len(klines)
        
        # 前period个值应该是None
        for i in range(14):
            assert rsi_values[i] is None
        
        # 后面的值应该是有效的RSI
        for i in range(14, len(rsi_values)):
            assert rsi_values[i] is not None
            assert 0 <= rsi_values[i] <= 100
    
    def test_calculate_rsi_series_insufficient_data(self):
        """测试RSI序列计算（数据不足）"""
        prices = [100, 102, 104]
        klines = self.create_test_klines(prices)
        
        rsi_values = calculate_rsi_series(klines, period=14)
        
        # 数据不足时返回全None
        assert all(v is None for v in rsi_values)
    
    def test_calculate_rsi_different_periods(self):
        """测试不同周期的RSI计算"""
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                  120, 122, 124, 126, 128, 130, 132, 134, 136, 138,
                  140, 142, 144, 146, 148, 150]
        klines = self.create_test_klines(prices)
        
        rsi_7 = calculate_rsi(klines, period=7)
        rsi_14 = calculate_rsi(klines, period=14)
        rsi_21 = calculate_rsi(klines, period=21)
        
        # 不同周期的RSI应该都有效
        assert 0 <= rsi_7 <= 100
        assert 0 <= rsi_14 <= 100
        assert 0 <= rsi_21 <= 100
    
    def test_calculate_rsi_with_zero_change(self):
        """测试RSI计算（价格无变化）"""
        prices = [100] * 20  # 价格不变
        klines = self.create_test_klines(prices)
        
        # 价格不变时，所有变化都是0，avg_loss=0
        # RSI应该返回100（因为没有损失）
        rsi = calculate_rsi(klines, period=14)
        
        # 实际上当价格完全不变时，gains和losses都是0
        # 这种情况下RSI的定义可能不同，但我们的实现会返回100
        assert rsi == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
