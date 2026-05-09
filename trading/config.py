#!/usr/bin/env python3
"""
交易策略配置文件
集中管理所有策略参数，便于调整和优化
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FibonacciConfig:
    """Fibonacci 回撤配置"""
    
    # 买入档位配置 (label, ratio)
    buy_ratios: list = None
    
    # 止损比例
    stop_ratio: float = 0.920
    
    # 卖出档位配置 (label, ratio)
    sell_ratios: list = None
    
    # 卖出比例配置 {label: percentage}
    sell_percentages: Dict[str, float] = None
    
    # ZIGZAG 参数
    zigzag_deviation: float = 5.0  # 最小波动百分比
    zigzag_depth: int = 10         # 最小K线根数
    zigzag_lookback: int = 5       # 右侧确认根数
    
    # 穿透容差配置
    shallow_penetration_threshold: float = 0.03  # 浅插针阈值 3%
    shallow_tolerance: float = 0.02              # 浅插针容差 2%
    deep_tolerance: float = 0.05                 # 深插针容差 5%
    
    def __post_init__(self):
        if self.buy_ratios is None:
            self.buy_ratios = [
                ("buy_618", 0.618),
                ("buy_786", 0.786),
                ("buy_861", 0.861),
            ]
        
        if self.sell_ratios is None:
            self.sell_ratios = [
                ("sell_100", 1.000),   # 100% 回撤（回到波峰）
                ("sell_1272", 1.272),  # 127.2% 扩展位
            ]
        
        if self.sell_percentages is None:
            self.sell_percentages = {
                "sell_100": 0.30,   # 卖出 30%
                "sell_1272": 0.50,  # 卖出 50%
            }


@dataclass
class AOConfig:
    """AO (Awesome Oscillator) 配置"""
    
    # AO 计算参数
    fast_period: int = 5
    slow_period: int = 34
    
    # AO 卖出阈值
    threshold_normal: float = 0.00003500  # 35k
    
    # AO < 阈值时的收益率要求
    profit_threshold: float = 0.50  # 50%
    
    # AO 启动检测参数
    min_length: int = 34           # 最小数据长度
    min_value_threshold: float = 0.000001  # 最小波动阈值


@dataclass
class PositionConfig:
    """仓位管理配置"""
    
    # 单币最大仓位比例
    max_position_ratio: float = 0.30  # 30%
    
    # 最小买入金额 (SOL)
    min_position_sol: float = 0.005
    
    # 仓位档位配置 {tier: ratio}
    tier_sizes: Dict[str, float] = None
    
    # 交易时间限制（北京时间）
    trading_start_hour: int = 0
    trading_end_hour: int = 13
    
    def __post_init__(self):
        if self.tier_sizes is None:
            self.tier_sizes = {
                "buy_618": 0.03,  # 3%
                "buy_786": 0.02,  # 2%
                "buy_861": 0.01,  # 1%
            }


@dataclass
class ProfitConfig:
    """止盈止损配置"""
    
    # 固定止盈目标（AO 未启动时使用）
    profit_target_50: float = 0.50   # 50%
    profit_target_100: float = 1.00  # 100%
    
    # 止盈卖出比例
    profit_50_sell_percentage: float = 0.50  # 50% 止盈时卖出 50%
    profit_100_sell_percentage: float = 1.00  # 100% 止盈时全部卖出


@dataclass
class TradingConfig:
    """完整交易配置"""
    
    fibonacci: FibonacciConfig = None
    ao: AOConfig = None
    position: PositionConfig = None
    profit: ProfitConfig = None
    
    def __post_init__(self):
        if self.fibonacci is None:
            self.fibonacci = FibonacciConfig()
        if self.ao is None:
            self.ao = AOConfig()
        if self.position is None:
            self.position = PositionConfig()
        if self.profit is None:
            self.profit = ProfitConfig()


# 默认配置实例
DEFAULT_CONFIG = TradingConfig()


def get_default_config() -> TradingConfig:
    """获取默认配置"""
    return DEFAULT_CONFIG


def create_custom_config(**kwargs) -> TradingConfig:
    """
    创建自定义配置
    
    示例:
        config = create_custom_config(
            fibonacci=FibonacciConfig(stop_ratio=0.95),
            ao=AOConfig(threshold_normal=0.00005000)
        )
    """
    return TradingConfig(**kwargs)
