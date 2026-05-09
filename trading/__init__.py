"""
交易模块 - 独立的交易逻辑

包含:
- 交易执行 (买入/卖出)
- 仓位管理
- 止盈止损
- Fibonacci计算 (买入/卖出信号)
- 交易统计
"""

from .executor import TradeExecutor
from .position_manager import PositionManager
from .profit_manager import ProfitManager
from .fib_calculator import (
    # 数据类型
    Kline, FibLevel,
    # K线解析
    parse_klines,
    # Fibonacci计算
    fib_entry_levels, fib_sell_levels, fib_signal,
    # AO计算
    calc_ao, ao_sell_signal,
    # ZIGZAG
    zigzag_pivots,
    # 仓位配置
    ENTRY_TIERS, BUY_RATIOS, SELL_RATIOS, SELL_PERCENTAGES,
    MAX_POSITION_RATIO, MIN_POSITION_SOL,
    position_size,
)

__all__ = [
    # 核心模块
    'TradeExecutor',
    'PositionManager',
    'ProfitManager',
    
    # Fibonacci计算
    'Kline',
    'FibLevel',
    'parse_klines',
    'fib_entry_levels',
    'fib_sell_levels',
    'fib_signal',
    'calc_ao',
    'ao_sell_signal',
    'zigzag_pivots',
    
    # 仓位配置
    'ENTRY_TIERS',
    'BUY_RATIOS',
    'SELL_RATIOS',
    'SELL_PERCENTAGES',
    'MAX_POSITION_RATIO',
    'MIN_POSITION_SOL',
    'position_size',
]
