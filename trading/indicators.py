#!/usr/bin/env python3
"""
技术指标计算模块
"""

from typing import List
from .fib_calculator import Kline


def calculate_rsi(klines: List[Kline], period: int = 14) -> float:
    """
    计算RSI指标（Relative Strength Index）
    
    Args:
        klines: K线数据列表（至少需要period+1根）
        period: RSI周期（默认14）
    
    Returns:
        当前RSI值（0-100）
    
    Raises:
        ValueError: K线数量不足
    
    Example:
        >>> klines = parse_klines(raw_klines)
        >>> rsi = calculate_rsi(klines, period=14)
        >>> print(f"RSI: {rsi:.2f}")
    """
    if len(klines) < period + 1:
        raise ValueError(f"K线数量不足，至少需要{period + 1}根，当前只有{len(klines)}根")
    
    # 计算价格变化
    price_changes = []
    for i in range(1, len(klines)):
        change = klines[i].close - klines[i-1].close
        price_changes.append(change)
    
    # 分离涨跌
    gains = []
    losses = []
    
    for change in price_changes:
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    # 计算初始平均涨跌幅（使用前period个数据）
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # 使用平滑移动平均（Wilder's smoothing）计算后续值
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    # 计算RSI
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_rsi_series(klines: List[Kline], period: int = 14) -> List[float]:
    """
    计算RSI序列（返回所有K线的RSI值）
    
    Args:
        klines: K线数据列表
        period: RSI周期（默认14）
    
    Returns:
        RSI值列表（前period个值为None）
    
    Example:
        >>> klines = parse_klines(raw_klines)
        >>> rsi_values = calculate_rsi_series(klines, period=14)
        >>> for i, rsi in enumerate(rsi_values):
        ...     if rsi is not None:
        ...         print(f"K线{i}: RSI={rsi:.2f}")
    """
    if len(klines) < period + 1:
        return [None] * len(klines)
    
    rsi_values = [None] * period
    
    # 计算价格变化
    price_changes = []
    for i in range(1, len(klines)):
        change = klines[i].close - klines[i-1].close
        price_changes.append(change)
    
    # 分离涨跌
    gains = []
    losses = []
    
    for change in price_changes:
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    # 计算初始平均涨跌幅
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # 计算第一个RSI值
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
    
    # 计算后续RSI值
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
    
    return rsi_values


if __name__ == "__main__":
    # 测试示例
    from .fib_calculator import Kline
    
    # 创建测试K线数据
    test_klines = []
    prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
              111, 110, 112, 114, 113, 115, 117, 116, 118, 120]
    
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
        test_klines.append(kline)
    
    # 计算RSI
    rsi = calculate_rsi(test_klines, period=14)
    print(f"当前RSI: {rsi:.2f}")
    
    # 计算RSI序列
    rsi_series = calculate_rsi_series(test_klines, period=14)
    print("\nRSI序列:")
    for i, rsi_val in enumerate(rsi_series):
        if rsi_val is not None:
            print(f"K线{i}: RSI={rsi_val:.2f}")
