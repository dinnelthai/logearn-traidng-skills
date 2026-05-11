#!/usr/bin/env python3
"""
K线服务层 - 统一的K线数据获取接口

提供统一的K线获取方法，支持多种周期，供所有交易模块使用
"""

import os
import requests
from typing import List, Dict, Optional
from .fib_calculator import Kline, parse_klines


class KlineService:
    """K线服务 - 统一的K线数据获取接口"""
    
    # 周期映射（字符串 -> 秒数）
    INTERVAL_MAP = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '1h': 3600,
        '1d': 86400
    }
    
    def __init__(self, api_key: str = None, api_base: str = None):
        """
        初始化K线服务
        
        Args:
            api_key: LogEarn API Key（默认从环境变量获取）
            api_base: API基础URL（默认从环境变量获取）
        """
        self.api_key = api_key or os.getenv("LOGEARN_API_KEY")
        if not self.api_key:
            raise ValueError("LOGEARN_API_KEY not set")
        
        self.api_base = api_base or os.getenv("LOGEARN_API_BASE", "https://logearn.com/logearn")
        self.url = f"{self.api_base}/open/api/v1/call/get_kline_list"
    
    def get_klines_raw(self, ca: str, interval: str = '5m', page_size: int = 200, 
                       end_time: int = None) -> List[Dict]:
        """
        获取原始K线数据（LogEarn API格式）
        
        Args:
            ca: 代币地址
            interval: K线周期（'1m', '5m', '15m', '1h', '1d'）
            page_size: 返回K线数量（默认200，建议不超过200）
            end_time: 结束时间（Unix秒时间戳），用于翻页
        
        Returns:
            原始K线数据列表
            [
                {
                    "time": 1775883000,
                    "open": "0.001234",
                    "openU": "0.001234",
                    "high": "0.001300",
                    "highU": "0.001300",
                    "low": "0.001200",
                    "lowU": "0.001200",
                    "close": "0.001280",
                    "closeU": "0.001280",
                    "volume": "98765",
                    "volumeU": "98765"
                },
                ...
            ]
        """
        if interval not in self.INTERVAL_MAP:
            raise ValueError(f"不支持的K线周期: {interval}，支持: {list(self.INTERVAL_MAP.keys())}")
        
        interval_seconds = self.INTERVAL_MAP[interval]
        
        # 请求参数
        payload = {
            "chain": "3",  # Solana
            "base": ca,
            "intervalTime": interval_seconds,
            "pageSize": page_size
        }
        
        if end_time is not None:
            payload["endTime"] = end_time
        
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # 发送请求
        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") != 200:
                raise ValueError(f"API返回错误: {data.get('msg', 'Unknown error')}")
            
            klines = data.get("data", {}).get("body", [])
            
            if not klines:
                raise ValueError(f"未获取到K线数据，代币地址: {ca}")
            
            # 转换价格字段为float
            for kline in klines:
                for field in ["open", "high", "low", "close", "volume", 
                             "openU", "highU", "lowU", "closeU", "volumeU"]:
                    if field in kline and isinstance(kline[field], str):
                        kline[field] = float(kline[field])
            
            return klines
            
        except requests.RequestException as e:
            raise requests.RequestException(f"获取K线失败: {e}")
    
    def get_klines(self, ca: str, interval: str = '5m', page_size: int = 200, 
                   end_time: int = None) -> List[Kline]:
        """
        获取K线数据（解析为Kline对象）
        
        Args:
            ca: 代币地址
            interval: K线周期（'1m', '5m', '15m', '1h', '1d'）
            page_size: 返回K线数量（默认200）
            end_time: 结束时间（Unix秒时间戳）
        
        Returns:
            Kline对象列表
        
        Example:
            service = KlineService()
            klines = service.get_klines("CA地址", interval='5m')
            for kline in klines:
                print(f"时间: {kline.time}, 收盘价: {kline.close}")
        """
        raw_klines = self.get_klines_raw(ca, interval, page_size, end_time)
        
        # 添加market_cap字段（兼容现有代码）
        for kline in raw_klines:
            if "market_cap" not in kline:
                kline["market_cap"] = 0
        
        # 解析为Kline对象
        return parse_klines(raw_klines)
    
    def get_latest_kline(self, ca: str, interval: str = '5m') -> Optional[Kline]:
        """
        获取最新一根K线
        
        Args:
            ca: 代币地址
            interval: K线周期
        
        Returns:
            最新K线对象
        """
        klines = self.get_klines(ca, interval, page_size=1)
        return klines[0] if klines else None
    
    def get_all_klines(self, ca: str, interval: str = '5m', max_pages: int = 10) -> List[Kline]:
        """
        获取所有历史K线（通过翻页）
        
        Args:
            ca: 代币地址
            interval: K线周期
            max_pages: 最大翻页次数（默认10，即最多2000根K线）
        
        Returns:
            所有K线对象列表（按时间倒序，无重复）
        
        Note:
            翻页时会自动去重，确保K线数据完整且无重复
        """
        all_klines = []
        end_time = None
        page_count = 0
        seen_times = set()  # 用于去重
        
        while page_count < max_pages:
            try:
                klines = self.get_klines(ca, interval, page_size=200, end_time=end_time)
                
                if not klines:
                    break
                
                # 去重：只添加未见过的K线
                new_klines = []
                for kline in klines:
                    if kline.time not in seen_times:
                        new_klines.append(kline)
                        seen_times.add(kline.time)
                
                if not new_klines:
                    # 如果没有新K线，说明已经获取完所有数据
                    break
                
                all_klines.extend(new_klines)
                page_count += 1
                
                # 使用最后一根K线的时间作为下一页的end_time
                # 注意：下一页会包含这根K线，但会被去重逻辑过滤掉
                end_time = klines[-1].time
                
            except Exception as e:
                print(f"翻页失败: {e}")
                break
        
        return all_klines


# 全局单例
_kline_service = None


def get_kline_service() -> KlineService:
    """
    获取K线服务单例
    
    Returns:
        KlineService实例
    """
    global _kline_service
    if _kline_service is None:
        _kline_service = KlineService()
    return _kline_service


# 便捷函数
def get_klines(ca: str, interval: str = '5m', page_size: int = 200) -> List[Kline]:
    """
    获取K线数据（便捷函数）
    
    Args:
        ca: 代币地址
        interval: K线周期（'1m', '5m', '15m', '1h', '1d'）
        page_size: 返回K线数量
    
    Returns:
        Kline对象列表
    
    Example:
        from trading.kline_service import get_klines
        
        klines = get_klines("CA地址", interval='5m')
        print(f"获取{len(klines)}根K线")
    """
    service = get_kline_service()
    return service.get_klines(ca, interval, page_size)


def get_klines_raw(ca: str, interval: str = '5m', page_size: int = 200) -> List[Dict]:
    """
    获取原始K线数据（便捷函数）
    
    Args:
        ca: 代币地址
        interval: K线周期
        page_size: 返回K线数量
    
    Returns:
        原始K线数据列表
    """
    service = get_kline_service()
    return service.get_klines_raw(ca, interval, page_size)


if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("用法: python kline_service.py <代币地址> [周期] [数量]")
        print("周期: 1m, 5m, 15m, 1h, 1d (默认5m)")
        print("数量: 返回K线数量 (默认10)")
        sys.exit(1)
    
    ca = sys.argv[1]
    interval = sys.argv[2] if len(sys.argv) > 2 else '5m'
    page_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print("="*80)
    print("K线服务测试")
    print("="*80)
    print(f"代币地址: {ca}")
    print(f"K线周期: {interval}")
    print(f"获取数量: {page_size}")
    print("="*80)
    print()
    
    try:
        # 测试获取K线
        klines = get_klines(ca, interval, page_size)
        print(f"✅ 成功获取{len(klines)}根K线")
        print()
        print("最新5根K线:")
        for i, kline in enumerate(klines[:5]):
            time_str = datetime.fromtimestamp(kline.time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{i+1}. {time_str} | O:{kline.open:.8f} H:{kline.high:.8f} L:{kline.low:.8f} C:{kline.close:.8f}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
