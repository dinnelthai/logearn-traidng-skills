#!/usr/bin/env python3
"""
Fibonacci交易入口测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from trading.fibonacci_trade import run_fibonacci_trade


class TestFibonacciTrade:
    """Fibonacci交易入口测试"""
    
    @patch('trading.fibonacci_trade.SingleTradeBot')
    @patch('trading.fibonacci_trade.get_klines_raw')
    def test_run_fibonacci_trade_basic(self, mock_get_klines, mock_bot_class):
        """测试运行Fibonacci交易（基本）"""
        # Mock K线数据
        mock_get_klines.return_value = [
            {"time": 1775883000, "open": 0.001, "high": 0.001, "low": 0.001, "close": 0.001, "volume": 100}
        ]
        
        # Mock机器人
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        
        # 运行交易
        run_fibonacci_trade(ca="test_ca", total_capital=2.0, check_interval=60)
        
        # 验证机器人被正确初始化
        mock_bot_class.assert_called_once_with(ca="test_ca", total_capital=2.0)
        
        # 验证机器人run方法被调用
        assert mock_bot.run.called
        call_args = mock_bot.run.call_args
        assert call_args[1]['check_interval'] == 60
    
    @patch('trading.fibonacci_trade.SingleTradeBot')
    @patch('trading.fibonacci_trade.get_klines_raw')
    def test_run_fibonacci_trade_klines_provider(self, mock_get_klines, mock_bot_class):
        """测试K线提供函数"""
        mock_get_klines.return_value = [
            {"time": 1775883000, "open": 0.001, "high": 0.001, "low": 0.001, "close": 0.001, "volume": 100}
        ]
        
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        
        run_fibonacci_trade(ca="test_ca")
        
        # 获取klines_provider函数
        call_args = mock_bot.run.call_args
        klines_provider = call_args[0][0]
        
        # 调用klines_provider
        klines = klines_provider()
        
        # 验证调用了get_klines_raw，使用5分钟K线
        mock_get_klines.assert_called_with("test_ca", interval='5m', page_size=200)
        assert len(klines) == 1
    
    @patch('trading.fibonacci_trade.SingleTradeBot')
    @patch('trading.fibonacci_trade.get_klines_raw')
    def test_run_fibonacci_trade_default_params(self, mock_get_klines, mock_bot_class):
        """测试默认参数"""
        mock_get_klines.return_value = []
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        
        run_fibonacci_trade(ca="test_ca")
        
        # 验证使用默认参数
        mock_bot_class.assert_called_once_with(ca="test_ca", total_capital=2.0)
        call_args = mock_bot.run.call_args
        assert call_args[1]['check_interval'] == 60
    
    @patch('trading.fibonacci_trade.SingleTradeBot')
    @patch('trading.fibonacci_trade.get_klines_raw')
    def test_run_fibonacci_trade_custom_params(self, mock_get_klines, mock_bot_class):
        """测试自定义参数"""
        mock_get_klines.return_value = []
        mock_bot = Mock()
        mock_bot_class.return_value = mock_bot
        
        run_fibonacci_trade(ca="custom_ca", total_capital=5.0, check_interval=120)
        
        # 验证使用自定义参数
        mock_bot_class.assert_called_once_with(ca="custom_ca", total_capital=5.0)
        call_args = mock_bot.run.call_args
        assert call_args[1]['check_interval'] == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
