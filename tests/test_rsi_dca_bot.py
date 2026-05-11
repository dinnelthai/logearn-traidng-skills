#!/usr/bin/env python3
"""
RSI定投机器人测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from trading.rsi_dca_bot import RSIDCABot, run_rsi_dca
from trading.fib_calculator import Kline


class TestRSIDCABot:
    """RSI定投机器人测试"""
    
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
    
    def test_init_basic(self):
        """测试初始化（基本）"""
        bot = RSIDCABot(
            ca="test_ca",
            dca_amount=0.1,
            max_buy_count=10
        )
        
        assert bot.ca == "test_ca"
        assert bot.dca_amount == 0.1
        assert bot.max_buy_count == 10
        assert bot.rsi_period == 14
        assert bot.rsi_buy_threshold == 30.0
        assert bot.rsi_reset_threshold == 50.0
        assert bot.buy_count == 0
        assert bot.waiting_for_reset == False
    
    def test_init_custom_params(self):
        """测试初始化（自定义参数）"""
        bot = RSIDCABot(
            ca="test_ca",
            dca_amount=0.2,
            max_buy_count=20,
            rsi_period=21,
            rsi_buy_threshold=25.0,
            rsi_reset_threshold=60.0
        )
        
        assert bot.rsi_period == 21
        assert bot.rsi_buy_threshold == 25.0
        assert bot.rsi_reset_threshold == 60.0
    
    def test_get_status(self):
        """测试获取状态"""
        bot = RSIDCABot(ca="test_ca", dca_amount=0.1, max_buy_count=10)
        bot.buy_count = 3
        bot.waiting_for_reset = True
        bot.last_rsi = 35.5
        
        status = bot.get_status()
        
        assert status['ca'] == "test_ca"
        assert status['dca_amount'] == 0.1
        assert status['max_buy_count'] == 10
        assert status['buy_count'] == 3
        assert status['waiting_for_reset'] == True
        assert status['last_rsi'] == 35.5
        assert status['progress'] == "3/10"
        assert status['completed'] == False
    
    def test_get_status_completed(self):
        """测试获取状态（已完成）"""
        bot = RSIDCABot(ca="test_ca", dca_amount=0.1, max_buy_count=10)
        bot.buy_count = 10
        
        status = bot.get_status()
        
        assert status['completed'] == True
    
    @patch('trading.rsi_dca_bot.get_klines')
    @patch('trading.rsi_dca_bot.TradeExecutor')
    def test_execute_buy_success(self, mock_executor_class, mock_get_klines):
        """测试执行买入（成功）"""
        # Mock K线
        prices = list(range(100, 120))
        klines = self.create_test_klines(prices)
        mock_get_klines.return_value = klines
        
        # Mock执行器
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_executor.buy.return_value = mock_result
        mock_executor_class.return_value = mock_executor
        
        bot = RSIDCABot(ca="test_ca", dca_amount=0.1, max_buy_count=10)
        
        # 执行买入
        bot._execute_buy(klines[-1], 28.5)
        
        # 验证买入被调用
        mock_executor.buy.assert_called_once()
        call_args = mock_executor.buy.call_args
        assert call_args[1]['ca'] == "test_ca"
        assert call_args[1]['amount_sol'] == 0.1
        
        # 验证状态更新
        assert bot.buy_count == 1
    
    @patch('trading.rsi_dca_bot.get_klines')
    @patch('trading.rsi_dca_bot.TradeExecutor')
    def test_execute_buy_failure(self, mock_executor_class, mock_get_klines):
        """测试执行买入（失败）"""
        prices = list(range(100, 120))
        klines = self.create_test_klines(prices)
        mock_get_klines.return_value = klines
        
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.message = "Insufficient balance"
        mock_executor.buy.return_value = mock_result
        mock_executor_class.return_value = mock_executor
        
        bot = RSIDCABot(ca="test_ca", dca_amount=0.1, max_buy_count=10)
        
        # 执行买入
        bot._execute_buy(klines[-1], 28.5)
        
        # 验证买入次数未增加
        assert bot.buy_count == 0
    
    @patch('trading.rsi_dca_bot.run_rsi_dca')
    def test_run_rsi_dca_function(self, mock_run):
        """测试run_rsi_dca函数"""
        run_rsi_dca(
            ca="test_ca",
            dca_amount=0.1,
            max_buy_count=10,
            interval='1h',
            check_interval=300
        )
        
        mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
