#!/usr/bin/env python3
"""
K线缓存管理 - 增量更新机制

提供K线缓存和增量更新功能，减少API调用和数据传输
"""

from typing import List, Dict, Optional
from .fib_calculator import Kline
from .kline_service import get_klines


class KlineCache:
    """K线缓存管理器"""
    
    def __init__(self, ca: str, interval: str = '5m', cache_size: int = 200):
        """
        初始化K线缓存
        
        Args:
            ca: 代币地址
            interval: K线周期
            cache_size: 缓存大小（保留最近N根K线）
        """
        self.ca = ca
        self.interval = interval
        self.cache_size = cache_size
        
        # 缓存的K线数据
        self.klines: List[Kline] = []
        
        # 最后更新时间
        self.last_update_time: Optional[int] = None
    
    def get_klines(self, force_refresh: bool = False) -> List[Kline]:
        """
        获取K线数据（增量更新）
        
        Args:
            force_refresh: 是否强制刷新（忽略缓存）
        
        Returns:
            K线列表（按时间倒序）
        
        工作原理:
            1. 首次调用：全量获取cache_size根K线
            2. 后续调用：只获取最新的K线（增量更新）
            3. 自动去重和排序
        """
        if force_refresh or not self.klines:
            # 首次获取或强制刷新：全量获取
            self.klines = get_klines(self.ca, self.interval, self.cache_size)
            if self.klines:
                self.last_update_time = self.klines[0].time
            return self.klines
        
        # 增量更新：只获取最新的K线
        try:
            # 获取最新的K线（page_size=10足够获取新增的K线）
            new_klines = get_klines(self.ca, self.interval, page_size=10)
            
            if not new_klines:
                return self.klines
            
            # 找出真正新增的K线
            latest_cached_time = self.klines[0].time if self.klines else 0
            truly_new = [k for k in new_klines if k.time > latest_cached_time]
            
            if truly_new:
                # 添加新K线到缓存前面（保持倒序）
                self.klines = truly_new + self.klines
                
                # 保持缓存大小
                if len(self.klines) > self.cache_size:
                    self.klines = self.klines[:self.cache_size]
                
                self.last_update_time = self.klines[0].time
                print(f"📊 增量更新: 新增{len(truly_new)}根K线")
            else:
                # 更新最新K线的数据（价格可能变化）
                if new_klines[0].time == self.klines[0].time:
                    self.klines[0] = new_klines[0]
                    print(f"📊 更新最新K线: time={new_klines[0].time}")
            
            return self.klines
            
        except Exception as e:
            print(f"⚠️ 增量更新失败，返回缓存数据: {e}")
            return self.klines
    
    def clear(self):
        """清空缓存"""
        self.klines = []
        self.last_update_time = None
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存信息
        
        Returns:
            缓存统计信息
        """
        return {
            'ca': self.ca,
            'interval': self.interval,
            'cache_size': len(self.klines),
            'max_cache_size': self.cache_size,
            'last_update_time': self.last_update_time,
            'oldest_time': self.klines[-1].time if self.klines else None,
            'newest_time': self.klines[0].time if self.klines else None
        }


# 全局缓存管理器
_cache_instances: Dict[str, KlineCache] = {}


def get_kline_cache(ca: str, interval: str = '5m', cache_size: int = 200) -> KlineCache:
    """
    获取K线缓存实例（单例模式）
    
    Args:
        ca: 代币地址
        interval: K线周期
        cache_size: 缓存大小
    
    Returns:
        KlineCache实例
    
    Note:
        每个(ca, interval)组合对应一个独立的缓存实例
    """
    cache_key = f"{ca}_{interval}"
    
    if cache_key not in _cache_instances:
        _cache_instances[cache_key] = KlineCache(ca, interval, cache_size)
    
    return _cache_instances[cache_key]


def clear_all_caches():
    """清空所有缓存"""
    global _cache_instances
    _cache_instances.clear()


if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("用法: python kline_cache.py <代币地址> [周期]")
        sys.exit(1)
    
    ca = sys.argv[1]
    interval = sys.argv[2] if len(sys.argv) > 2 else '5m'
    
    print("="*80)
    print("K线缓存测试")
    print("="*80)
    print(f"代币地址: {ca}")
    print(f"K线周期: {interval}")
    print("="*80)
    print()
    
    # 创建缓存
    cache = get_kline_cache(ca, interval, cache_size=200)
    
    # 首次获取（全量）
    print("1️⃣ 首次获取（全量）")
    klines = cache.get_klines()
    print(f"✅ 获取{len(klines)}根K线")
    print(f"最新: {datetime.fromtimestamp(klines[0].time).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"最旧: {datetime.fromtimestamp(klines[-1].time).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 缓存信息
    info = cache.get_cache_info()
    print("📊 缓存信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # 增量更新
    print("2️⃣ 增量更新")
    import time
    time.sleep(2)  # 等待2秒
    klines = cache.get_klines()
    print(f"✅ 当前{len(klines)}根K线")
    print()
    
    # 强制刷新
    print("3️⃣ 强制刷新")
    klines = cache.get_klines(force_refresh=True)
    print(f"✅ 刷新后{len(klines)}根K线")
