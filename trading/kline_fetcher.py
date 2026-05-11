#!/usr/bin/env python3
"""
K线数据获取模块 - 从LogEarn API获取K线
"""

import os
import requests
from typing import List, Dict


def get_klines_from_logearn(ca: str, interval: str = '1h', page_size: int = 200, 
                           end_time: int = None) -> List[Dict]:
    """
    从LogEarn API获取K线数据
    
    Args:
        ca: 代币地址
        interval: K线周期
            - '1m': 1分钟 (60秒)
            - '5m': 5分钟 (300秒)
            - '15m': 15分钟 (900秒)
            - '1h': 1小时 (3600秒)
            - '1d': 1天 (86400秒)
        page_size: 返回K线数量（默认200，建议不超过200）
        end_time: 结束时间（Unix秒时间戳），用于翻页，默认为当前时间
    
    Returns:
        K线数据列表（按时间倒序，最新的在前）
        [
            {
                "time": 1775883000,          # Unix时间戳（秒）
                "open": 0.001234,            # 开盘价（SOL）
                "openU": 0.001234,           # 开盘价（USD）
                "high": 0.001300,            # 最高价（SOL）
                "highU": 0.001300,           # 最高价（USD）
                "low": 0.001200,             # 最低价（SOL）
                "lowU": 0.001200,            # 最低价（USD）
                "close": 0.001280,           # 收盘价（SOL）
                "closeU": 0.001280,          # 收盘价（USD）
                "volume": 98765,             # 成交量
                "volumeU": 98765,            # 成交量（USD）
                "market_cap": 0              # 市值（添加字段）
            },
            ...
        ]
    
    Note:
        - 带U结尾的字段表示以USD计价
        - 不带U的字段表示以链的Native Token（SOL）计价
        - 使用end_time可以向前翻页获取更早的K线
    
    Example:
        # 获取最新200根1小时K线
        klines = get_klines_from_logearn("CA地址", interval='1h', page_size=200)
        
        # 翻页获取更早的K线
        oldest_time = klines[-1]['time']
        older_klines = get_klines_from_logearn("CA地址", interval='1h', 
                                               page_size=200, end_time=oldest_time)
    
    Raises:
        ValueError: API Key未设置或参数错误
        requests.RequestException: API请求失败
    """
    # 获取API Key
    api_key = os.getenv("LOGEARN_API_KEY")
    if not api_key:
        raise ValueError("LOGEARN_API_KEY environment variable not set")
    
    # 转换周期为秒数
    interval_map = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '1h': 3600,
        '1d': 86400
    }
    
    if interval not in interval_map:
        raise ValueError(f"不支持的K线周期: {interval}，支持: {list(interval_map.keys())}")
    
    interval_seconds = interval_map[interval]
    
    # API配置
    api_base = os.getenv("LOGEARN_API_BASE", "https://logearn.com/logearn")
    url = f"{api_base}/open/api/v1/call/get_kline_list"
    
    # 请求参数
    payload = {
        "chain": "3",  # Solana
        "base": ca,
        "intervalTime": interval_seconds,
        "pageSize": page_size
    }
    
    # 如果指定了end_time，添加到请求参数
    if end_time is not None:
        payload["endTime"] = end_time
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # 发送请求
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != 200:
            raise ValueError(f"API返回错误: {data.get('msg', 'Unknown error')}")
        
        # 提取K线数据
        klines = data.get("data", {}).get("body", [])
        
        if not klines:
            raise ValueError(f"未获取到K线数据，代币地址: {ca}")
        
        # 转换数据格式（添加market_cap字段）
        for kline in klines:
            # 如果没有market_cap，设置为0
            if "market_cap" not in kline:
                kline["market_cap"] = 0
            
            # 转换价格字段为float
            for field in ["open", "high", "low", "close", "volume"]:
                if field in kline and isinstance(kline[field], str):
                    kline[field] = float(kline[field])
        
        return klines
        
    except requests.RequestException as e:
        raise requests.RequestException(f"获取K线失败: {e}")


def get_latest_kline(ca: str, interval: str = '1h') -> Dict:
    """
    获取最新一根K线
    
    Args:
        ca: 代币地址
        interval: K线周期
    
    Returns:
        最新K线数据
    """
    klines = get_klines_from_logearn(ca, interval, page_size=1)
    return klines[0] if klines else None


def get_all_klines(ca: str, interval: str = '1h', max_pages: int = 10) -> List[Dict]:
    """
    获取所有历史K线（通过翻页）
    
    Args:
        ca: 代币地址
        interval: K线周期
        max_pages: 最大翻页次数（默认10，即最多2000根K线）
    
    Returns:
        所有K线数据列表（按时间倒序）
    
    Example:
        # 获取所有历史K线
        all_klines = get_all_klines("CA地址", interval='1h', max_pages=10)
        print(f"总共获取{len(all_klines)}根K线")
    """
    all_klines = []
    end_time = None
    page_count = 0
    
    while page_count < max_pages:
        try:
            # 获取一页K线
            klines = get_klines_from_logearn(ca, interval, page_size=200, end_time=end_time)
            
            if not klines:
                break
            
            all_klines.extend(klines)
            page_count += 1
            
            # 使用最后一根K线的时间作为下一页的end_time
            end_time = klines[-1]['time']
            
            print(f"已获取{len(all_klines)}根K线（第{page_count}页）")
            
        except Exception as e:
            print(f"翻页失败: {e}")
            break
    
    return all_klines


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python kline_fetcher.py <代币地址> [周期]")
        print("周期: 1m, 5m, 15m, 1h, 1d (默认1h)")
        sys.exit(1)
    
    ca = sys.argv[1]
    interval = sys.argv[2] if len(sys.argv) > 2 else '1h'
    
    print(f"获取K线数据: {ca}")
    print(f"周期: {interval}")
    print("="*80)
    
    try:
        klines = get_klines_from_logearn(ca, interval, page_size=10)
        print(f"✅ 成功获取{len(klines)}根K线")
        print("\n最新5根K线:")
        for i, kline in enumerate(klines[:5]):
            from datetime import datetime
            time_str = datetime.fromtimestamp(kline['time']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{i+1}. {time_str} | O:{kline['open']:.8f} H:{kline['high']:.8f} L:{kline['low']:.8f} C:{kline['close']:.8f}")
    except Exception as e:
        print(f"❌ 错误: {e}")
