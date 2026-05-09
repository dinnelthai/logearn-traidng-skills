"""
交易模块 - 独立的交易逻辑

包含:
- 交易执行 (买入/卖出)
- 仓位管理
- 止盈止损
- 交易统计
"""

from .executor import TradeExecutor
from .position_manager import PositionManager
from .profit_manager import ProfitManager

__all__ = [
    'TradeExecutor',
    'PositionManager',
    'ProfitManager',
]
