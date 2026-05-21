"""
交易模块 - 对外公开接口

对外暴露核心交易接口:
1. run_fibonacci_trade() - Fibonacci交易（5分钟K线，自动缓存）
2. run_rsi_dca() - RSI定投（单个代币，1小时K线）
3. run_rsi_dca_multi() - RSI定投（多个代币，内部轮询）

K线获取、缓存、技术指标计算等均为内部实现，不对外暴露。
"""

# ========== 对外公开接口 ==========
from .fibonacci_trade import run_fibonacci_trade
from .rsi_dca_bot import run_rsi_dca
from .rsi_dca_manager import run_rsi_dca_multi, DCAConfig
from .ao_monitor import run_ao_monitor, run_ao_monitor_multi, AOMonitorConfig

# ========== 内部实现（不对外暴露） ==========
from .executor import TradeExecutor
from .position_manager import PositionManager
from .profit_manager import ProfitManager
from .fib_calculator import (
    Kline, FibLevel, parse_klines,
    fib_entry_levels, fib_sell_levels, fib_signal,
    calc_ao, ao_sell_signal, zigzag_pivots,
    ENTRY_TIERS, BUY_RATIOS, SELL_RATIOS, SELL_PERCENTAGES,
    MAX_POSITION_RATIO, MIN_POSITION_SOL, position_size,
)
from .kline_service import (
    KlineService, get_kline_service,
    get_klines, get_klines_raw
)
from .indicators import calculate_rsi, calculate_rsi_series
from .rsi_dca_bot import RSIDCABot
from .single_trade_bot import SingleTradeBot

__all__ = [
    # ========== 对外公开接口 ==========
    'run_fibonacci_trade',   # Fibonacci交易（5分钟K线，自动缓存）
    'run_rsi_dca',           # RSI定投（单个代币，1小时K线）
    'run_rsi_dca_multi',     # RSI定投（多个代币，内部轮询）
    'run_ao_monitor',        # AO监控（单个代币，接管持仓）
    'run_ao_monitor_multi',  # AO监控（多个代币，接管持仓）
    'DCAConfig',             # 定投配置类
    'AOMonitorConfig',       # AO监控配置类
]
