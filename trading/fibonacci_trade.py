#!/usr/bin/env python3
"""
Fibonacci交易入口 - 对外公开接口

只需传递CA地址，内部自动处理K线获取和交易执行
默认使用K线缓存和增量更新，提升性能
"""

from .single_trade_bot import SingleTradeBot
from .kline_cache import get_kline_cache


def run_fibonacci_trade(ca: str, total_capital: float = 2.0, check_interval: int = 60):
    """
    运行Fibonacci交易（对外公开接口）
    
    在一个代币上执行一次完整的买入-卖出交易，然后停止。
    内部自动获取5分钟K线（使用缓存+增量更新），无需手动提供K线数据。
    
    Args:
        ca: 代币地址（必需）
        total_capital: 总资金（SOL），默认2.0
        check_interval: 检查间隔（秒），默认60
    
    策略说明:
        - K线周期: 5分钟（自动缓存+增量更新）
        - 买入策略: Fibonacci回撤（61.8%, 78.6%, 86.1%）
        - 卖出策略: AO信号 + Fibonacci档位
        - 交易次数: 1次完整交易后停止
        - 资金管理: 分批买入，分批卖出
    
    性能优化:
        - 首次获取: 全量获取所有历史K线（自动翻页，可能几千根）
        - 后续更新: 只获取最新的K线（增量，1-10根）
        - 自动去重: 避免重复数据
        - 减少90%+ API调用和数据传输
    
    Example:
        >>> from trading import run_fibonacci_trade
        >>> 
        >>> # 运行Fibonacci交易
        >>> run_fibonacci_trade(
        ...     ca="代币地址",
        ...     total_capital=2.0,
        ...     check_interval=60
        ... )
    
    Note:
        - LogEarn skill与token绑定，不需要指定钱包
        - 必须设置LOGEARN_API_KEY环境变量
        - 按Ctrl+C可随时停止
    """
    # 创建机器人
    bot = SingleTradeBot(
        ca=ca,
        total_capital=total_capital
    )
    
    # 创建K线缓存（内部实现，使用5分钟K线）
    # 注意：首次获取全量历史K线，后续增量更新
    cache = get_kline_cache(ca, interval='5m', cache_size=10000)  # 足够大的缓存
    
    # 首次获取全量K线标志
    first_fetch = True
    
    # K线提供函数（使用缓存+增量更新）
    def klines_provider():
        """
        K线提供函数（内部实现）
        
        首次调用：全量获取所有历史K线（翻页）
        后续调用：增量更新（只获取新K线）
        
        Returns:
            原始K线数据（字典格式）
        """
        nonlocal first_fetch
        
        if first_fetch:
            # 首次：强制刷新，获取全量K线
            print("📊 首次获取全量历史K线...")
            from .kline_service import KlineService
            service = KlineService()
            
            # 获取全量K线（自动翻页）
            all_klines = service.get_all_klines(ca, interval='5m', max_pages=50)
            print(f"✅ 获取全量K线: {len(all_klines)}根")
            
            # 存入缓存（注意：K线按时间倒序，all_klines[0]是最新K线）
            cache.klines = all_klines
            cache.last_update_time = all_klines[0].time if all_klines else None  # 最新K线时间
            
            first_fetch = False
            klines = all_klines
        else:
            # 后续：增量更新
            klines = cache.get_klines()
        
        # 转换为原始格式（兼容现有接口）
        raw_klines = []
        for kline in klines:
            raw_klines.append({
                'time': kline.time,
                'open': kline.open,
                'high': kline.high,
                'low': kline.low,
                'close': kline.close,
                'volume': kline.volume,
                'market_cap': kline.market_cap
            })
        
        return raw_klines
    
    # 运行交易
    bot.run(klines_provider, check_interval=check_interval)


if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("用法: python fibonacci_trade.py <代币地址> [总资金] [检查间隔]")
        print("示例: python fibonacci_trade.py FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump 2.0 60")
        sys.exit(1)
    
    ca = sys.argv[1]
    total_capital = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    check_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    print("="*80)
    print("🤖 Fibonacci交易")
    print("="*80)
    print(f"代币地址: {ca}")
    print(f"总资金: {total_capital} SOL")
    print(f"检查间隔: {check_interval}秒")
    print(f"K线周期: 5分钟（自动获取）")
    print("="*80)
    print()
    
    run_fibonacci_trade(
        ca=ca,
        total_capital=total_capital,
        check_interval=check_interval
    )
