#!/usr/bin/env python3
"""
交易执行器测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from trading.executor import TradeExecutor, TradeResult


class TestTradeExecutor:
    """交易执行器测试"""
    
    def test_init_without_api_key(self):
        """测试初始化（未设置API Key）"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="LOGEARN_API_KEY not set"):
                TradeExecutor()
    
    def test_init_with_api_key(self):
        """测试初始化（设置API Key）"""
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            assert executor.api_key == "test_key"
    
    @patch('subprocess.run')
    def test_buy_success(self, mock_run):
        """测试买入（成功）"""
        # Mock subprocess返回
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "code": 200,
            "message": "Success",
            "data": {"tx": "test_tx"}
        })
        mock_run.return_value = mock_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.buy(ca="test_ca", amount_sol=0.1, current_price=0.00005)
        
        assert result.success == True
        assert result.code == 200
        assert result.message == "Success"
    
    @patch('subprocess.run')
    def test_buy_price_exceeded(self, mock_run):
        """测试买入（价格超限）"""
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.buy(
                ca="test_ca",
                amount_sol=0.1,
                limit_price=0.00005,
                current_price=0.00010,  # 当前价格高于限价
                slippage=0.02
            )
        
        assert result.success == False
        assert result.error == "price_exceeded"
    
    @patch('subprocess.run')
    def test_buy_cli_failure(self, mock_run):
        """测试买入（CLI调用失败）"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "CLI error"
        mock_run.return_value = mock_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.buy(ca="test_ca", amount_sol=0.1)
        
        assert result.success == False
        assert result.code == -1
    
    @patch('subprocess.run')
    def test_buy_timeout(self, mock_run):
        """测试买入（超时）"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.buy(ca="test_ca", amount_sol=0.1)
        
        assert result.success == False
        assert "超时" in result.error
    
    @patch('subprocess.run')
    def test_sell_success(self, mock_run):
        """测试卖出（成功）"""
        # Mock get_positions
        positions_result = Mock()
        positions_result.returncode = 0
        positions_result.stdout = json.dumps([
            {
                "token_address": "test_ca",
                "hold_amount": "1000",
                "decimals": "6"
            }
        ])
        
        # Mock swap
        swap_result = Mock()
        swap_result.returncode = 0
        swap_result.stdout = json.dumps({
            "code": 200,
            "message": "Success"
        })
        
        mock_run.side_effect = [positions_result, swap_result]
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.sell(ca="test_ca", percentage=1.0)
        
        assert result.success == True
    
    @patch('subprocess.run')
    def test_sell_position_not_found(self, mock_run):
        """测试卖出（未找到持仓）"""
        positions_result = Mock()
        positions_result.returncode = 0
        positions_result.stdout = json.dumps([])
        mock_run.return_value = positions_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.sell(ca="test_ca")
        
        assert result.success == False
        assert result.error == "position_not_found"
    
    @patch('subprocess.run')
    def test_sell_zero_position(self, mock_run):
        """测试卖出（持仓为0）"""
        positions_result = Mock()
        positions_result.returncode = 0
        positions_result.stdout = json.dumps([
            {
                "token_address": "test_ca",
                "hold_amount": "0",
                "decimals": "6"
            }
        ])
        mock_run.return_value = positions_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.sell(ca="test_ca")
        
        assert result.success == False
        assert result.error == "zero_position"
    
    @patch('subprocess.run')
    def test_sell_partial(self, mock_run):
        """测试卖出（部分卖出）"""
        positions_result = Mock()
        positions_result.returncode = 0
        positions_result.stdout = json.dumps([
            {
                "token_address": "test_ca",
                "hold_amount": "1000",
                "decimals": "6"
            }
        ])
        
        swap_result = Mock()
        swap_result.returncode = 0
        swap_result.stdout = json.dumps({"code": 200})
        
        mock_run.side_effect = [positions_result, swap_result]
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            result = executor.sell(ca="test_ca", percentage=0.5)
        
        assert result.success == True
    
    @patch('subprocess.run')
    def test_get_positions_success(self, mock_run):
        """测试获取持仓（成功）"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"token_address": "ca1", "hold_amount": "1000"},
            {"token_address": "ca2", "hold_amount": "2000"}
        ])
        mock_run.return_value = mock_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            positions = executor.get_positions()
        
        assert len(positions) == 2
        assert positions[0]["token_address"] == "ca1"
    
    @patch('subprocess.run')
    def test_get_positions_dict_format(self, mock_run):
        """测试获取持仓（字典格式）"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "data": [
                {"token_address": "ca1", "hold_amount": "1000"}
            ]
        })
        mock_run.return_value = mock_result
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            positions = executor.get_positions()
        
        assert len(positions) == 1
    
    @patch('subprocess.run')
    def test_get_positions_failure(self, mock_run):
        """测试获取持仓（失败）"""
        mock_run.side_effect = Exception("Network error")
        
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            executor = TradeExecutor()
            positions = executor.get_positions()
        
        assert positions == []


class TestTradeResult:
    """交易结果测试"""
    
    def test_trade_result_success(self):
        """测试交易结果（成功）"""
        result = TradeResult(
            success=True,
            code=200,
            message="Success",
            data={"tx": "test_tx"}
        )
        
        assert result.success == True
        assert result.code == 200
        assert result.message == "Success"
        assert result.data == {"tx": "test_tx"}
        assert result.error is None
    
    def test_trade_result_failure(self):
        """测试交易结果（失败）"""
        result = TradeResult(
            success=False,
            code=-1,
            message="Failed",
            error="insufficient_balance"
        )
        
        assert result.success == False
        assert result.error == "insufficient_balance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
