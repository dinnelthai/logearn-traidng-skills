#!/usr/bin/env python3
"""
K线服务测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from trading.kline_service import KlineService, get_kline_service, get_klines, get_klines_raw
from trading.fib_calculator import Kline


class TestKlineService:
    """K线服务测试"""
    
    def test_init_with_api_key(self):
        """测试初始化（提供API Key）"""
        service = KlineService(api_key="test_key")
        assert service.api_key == "test_key"
    
    def test_init_without_api_key(self):
        """测试初始化（未提供API Key）"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="LOGEARN_API_KEY not set"):
                KlineService()
    
    def test_init_with_env_api_key(self):
        """测试初始化（从环境变量获取API Key）"""
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'env_key'}):
            service = KlineService()
            assert service.api_key == "env_key"
    
    @patch('trading.kline_service.requests.post')
    def test_get_klines_raw_success(self, mock_post):
        """测试获取原始K线（成功）"""
        # Mock响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {
                        "time": 1775883000,
                        "open": "0.001234",
                        "high": "0.001300",
                        "low": "0.001200",
                        "close": "0.001280",
                        "volume": "98765"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        klines = service.get_klines_raw("test_ca", interval='5m', page_size=10)
        
        assert len(klines) == 1
        assert klines[0]['time'] == 1775883000
        assert klines[0]['open'] == 0.001234
        assert klines[0]['close'] == 0.001280
    
    @patch('trading.kline_service.requests.post')
    def test_get_klines_raw_with_end_time(self, mock_post):
        """测试获取原始K线（带endTime）"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {"body": [{"time": 1775883000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}]}
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        service.get_klines_raw("test_ca", interval='5m', page_size=10, end_time=1775883000)
        
        # 验证请求参数包含endTime
        call_args = mock_post.call_args
        assert call_args[1]['json']['endTime'] == 1775883000
    
    def test_get_klines_raw_invalid_interval(self):
        """测试获取原始K线（无效周期）"""
        service = KlineService(api_key="test_key")
        
        with pytest.raises(ValueError, match="不支持的K线周期"):
            service.get_klines_raw("test_ca", interval='invalid')
    
    @patch('trading.kline_service.requests.post')
    def test_get_klines_raw_api_error(self, mock_post):
        """测试获取原始K线（API错误）"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 500,
            "msg": "Server error"
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        
        with pytest.raises(ValueError, match="API返回错误"):
            service.get_klines_raw("test_ca", interval='5m')
    
    @patch('trading.kline_service.requests.post')
    def test_get_klines_raw_no_data(self, mock_post):
        """测试获取原始K线（无数据）"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {"body": []}
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        
        with pytest.raises(ValueError, match="未获取到K线数据"):
            service.get_klines_raw("test_ca", interval='5m')
    
    @patch('trading.kline_service.requests.post')
    def test_get_klines_success(self, mock_post):
        """测试获取K线对象（成功）"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {
                        "time": 1775883000,
                        "open": "0.001234",
                        "high": "0.001300",
                        "low": "0.001200",
                        "close": "0.001280",
                        "volume": "98765"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        klines = service.get_klines("test_ca", interval='5m')
        
        assert len(klines) == 1
        assert isinstance(klines[0], Kline)
        assert klines[0].time == 1775883000
        assert klines[0].close == 0.001280
        assert klines[0].market_cap == 0  # 自动添加
    
    @patch('trading.kline_service.requests.post')
    def test_get_latest_kline(self, mock_post):
        """测试获取最新K线"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {
                        "time": 1775883000,
                        "open": "0.001234",
                        "high": "0.001300",
                        "low": "0.001200",
                        "close": "0.001280",
                        "volume": "98765"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        service = KlineService(api_key="test_key")
        kline = service.get_latest_kline("test_ca", interval='5m')
        
        assert isinstance(kline, Kline)
        assert kline.time == 1775883000
    
    @patch('trading.kline_service.requests.post')
    def test_get_all_klines(self, mock_post):
        """测试获取所有历史K线（无重复）"""
        # 第一页
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {"time": 1775883000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"},
                    {"time": 1775882000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}
                ]
            }
        }
        
        # 第二页（包含重复的最后一根K线）
        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {"time": 1775882000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"},  # 重复
                    {"time": 1775881000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}   # 新数据
                ]
            }
        }
        
        # 第三页（空）
        mock_response3 = Mock()
        mock_response3.json.return_value = {
            "code": 200,
            "data": {"body": []}
        }
        
        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]
        
        service = KlineService(api_key="test_key")
        klines = service.get_all_klines("test_ca", interval='5m', max_pages=3)
        
        # 应该有3根不重复的K线
        assert len(klines) == 3
        
        # 验证时间戳唯一
        times = [k.time for k in klines]
        assert len(times) == len(set(times))  # 无重复
        assert 1775883000 in times
        assert 1775882000 in times
        assert 1775881000 in times
    
    @patch('trading.kline_service.requests.post')
    def test_get_all_klines_stop_on_duplicate(self, mock_post):
        """测试获取所有K线（完全重复时自动停止）"""
        # 第一页
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {"time": 1775883000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"},
                    {"time": 1775882000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}
                ]
            }
        }
        
        # 第二页（完全重复）
        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {"time": 1775882000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"},
                    {"time": 1775881000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}
                ]
            }
        }
        
        # 第三页（完全重复，应该自动停止）
        mock_response3 = Mock()
        mock_response3.json.return_value = {
            "code": 200,
            "data": {
                "body": [
                    {"time": 1775881000, "open": "0.001", "high": "0.001", "low": "0.001", "close": "0.001", "volume": "100"}
                ]
            }
        }
        
        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]
        
        service = KlineService(api_key="test_key")
        klines = service.get_all_klines("test_ca", interval='5m', max_pages=10)
        
        # 应该有3根不重复的K线，并且在第三页自动停止
        assert len(klines) == 3
        assert mock_post.call_count == 3  # 调用3次后停止
    
    def test_get_kline_service_singleton(self):
        """测试全局单例"""
        with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
            service1 = get_kline_service()
            service2 = get_kline_service()
            
            assert service1 is service2
    
    @patch('trading.kline_service.get_kline_service')
    def test_get_klines_convenience_function(self, mock_get_service):
        """测试便捷函数get_klines"""
        mock_service = Mock()
        mock_service.get_klines.return_value = [Mock(spec=Kline)]
        mock_get_service.return_value = mock_service
        
        result = get_klines("test_ca", interval='5m', page_size=100)
        
        mock_service.get_klines.assert_called_once_with("test_ca", '5m', 100)
        assert len(result) == 1
    
    @patch('trading.kline_service.get_kline_service')
    def test_get_klines_raw_convenience_function(self, mock_get_service):
        """测试便捷函数get_klines_raw"""
        mock_service = Mock()
        mock_service.get_klines_raw.return_value = [{"time": 1775883000}]
        mock_get_service.return_value = mock_service
        
        result = get_klines_raw("test_ca", interval='5m', page_size=100)
        
        mock_service.get_klines_raw.assert_called_once_with("test_ca", '5m', 100)
        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
