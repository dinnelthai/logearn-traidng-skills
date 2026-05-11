#!/usr/bin/env python3
"""
Fibonacci交易入口 - 对外公开接口

只需传递CA地址，内部自动处理K线获取和交易执行
"""

from .single_trade_bot import SingleTradeBot
from .kline_service import get_klines_raw


def run_fibonacci_trade(ca: str, total_capital: float = 2.0, check_interval: int = 60):
    """
    运行Fibonacci交易（对外公开接口）
    
    在一个代币上执行一次完整的买入-卖出交易，然后停止。
    内部自动获取5分钟K线，无需手动提供K线数据。
    
    Args:
        ca: 代币地址（必需）
        total_capital: 总资金（SOL），默认2.0
        check_interval: 检查间隔（秒），默认60
    
    策略说明:
        - K线周期: 5分钟（内部自动获取）
        - 买入策略: Fibonacci回撤（61.8%, 78.6%, 86.1%）
        - 卖出策略: AO信号 + Fibonacci档位
        - 交易次数: 1次完整交易后停止
        - 资金管理: 分批买入，分批卖出
    
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
    
    # K线提供函数（内部实现，使用5分钟K线）
    def klines_provider():
        return get_klines_raw(ca, interval='5m', page_size=200)
    
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
