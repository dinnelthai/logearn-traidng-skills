#!/usr/bin/env python3
"""
止盈止损管理器 - 负责止盈止损逻辑
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ProfitAction:
    """止盈动作"""
    should_sell: bool
    percentage: float  # 卖出比例（0-1）
    reason: str
    profit_rate: float = 0.0


class ProfitManager:
    """止盈止损管理器"""
    
    def __init__(self,
                 profit_target_50: float = 0.50,
                 profit_target_100: float = 1.00,
                 ao_threshold_normal: float = 0.00003500,
                 ao_profit_threshold: float = 0.50):
        """
        初始化止盈止损管理器
        
        Args:
            profit_target_50: 50%止盈目标
            profit_target_100: 100%止盈目标
            ao_threshold_normal: AO正常阈值（35k）
            ao_profit_threshold: AO低于阈值时的收益率要求
        """
        self.profit_target_50 = profit_target_50
        self.profit_target_100 = profit_target_100
        self.ao_threshold_normal = ao_threshold_normal
        self.ao_profit_threshold = ao_profit_threshold
    
    def check_profit_target(self,
                           current_price: float,
                           avg_price: float,
                           profit_50_sold: bool = False,
                           ao_active: bool = False) -> ProfitAction:
        """
        检查止盈目标（仅在AO未启动时）
        
        Args:
            current_price: 当前价格
            avg_price: 平均买入价
            profit_50_sold: 是否已卖出50%
            ao_active: AO是否启动
        
        Returns:
            ProfitAction: 止盈动作
        """
        if avg_price <= 0:
            return ProfitAction(
                should_sell=False,
                percentage=0,
                reason="平均价格无效"
            )
        
        # 如果AO已启动，不使用固定止盈
        if ao_active:
            return ProfitAction(
                should_sell=False,
                percentage=0,
                reason="AO已启动，使用AO卖出信号"
            )
        
        # 计算收益率
        profit_rate = (current_price - avg_price) / avg_price
        
        # 100%收益 → 全部卖出
        if profit_rate >= self.profit_target_100:
            return ProfitAction(
                should_sell=True,
                percentage=1.0,
                reason=f"AO未启动，收益率 {profit_rate*100:.1f}% >= 100%",
                profit_rate=profit_rate
            )
        
        # 50%收益 → 卖出50%（如果还没卖过）
        if profit_rate >= self.profit_target_50 and not profit_50_sold:
            return ProfitAction(
                should_sell=True,
                percentage=0.5,
                reason=f"AO未启动，收益率 {profit_rate*100:.1f}% >= 50%",
                profit_rate=profit_rate
            )
        
        return ProfitAction(
            should_sell=False,
            percentage=0,
            reason=f"收益率 {profit_rate*100:.1f}% 未达到止盈目标",
            profit_rate=profit_rate
        )
    
    def check_ao_sell_signal(self,
                            ao_values: list,
                            entry_price: float = None,
                            current_price: float = None) -> Tuple[bool, str]:
        """
        检查AO卖出信号
        
        Args:
            ao_values: AO值列表
            entry_price: 买入价格
            current_price: 当前价格
        
        Returns:
            Tuple[bool, str]: (是否卖出, 原因)
        """
        # 过滤有效AO值
        valid = [(i, v) for i, v in enumerate(ao_values) if v is not None]
        
        if len(valid) < 3:
            return False, "AO数据不足"
        
        # 获取最近3个AO值
        ao_n2 = valid[-3][1]
        ao_n1 = valid[-2][1]
        ao_0 = valid[-1][1]
        
        # 判断颜色
        color_n1 = "green" if ao_n1 >= ao_n2 else "red"
        color_0 = "green" if ao_0 >= ao_n1 else "red"
        
        # 绿转红：n1绿且n0红，且当前AO在0轴上方
        if not (color_n1 == "green" and color_0 == "red" and ao_0 > 0):
            return False, "未触发绿转红"
        
        # AO >= 35k → 直接卖出
        if ao_0 >= self.ao_threshold_normal:
            return True, f"AO≥{self.ao_threshold_normal*1e6:.0f}k绿转红"
        
        # AO < 35k → 需收益率 > 50%
        if entry_price and entry_price > 0 and current_price:
            profit_rate = (current_price - entry_price) / entry_price
            if profit_rate >= self.ao_profit_threshold:
                return True, (
                    f"AO<{self.ao_threshold_normal*1e6:.0f}k但"
                    f"收益率>{self.ao_profit_threshold*100:.0f}%"
                    f"({profit_rate*100:.1f}%)"
                )
        
        return False, "AO绿转红但收益率不足"
    
    def check_stop_loss(self,
                       current_price: float,
                       stop_price: float) -> Tuple[bool, str]:
        """
        检查止损
        
        Args:
            current_price: 当前价格
            stop_price: 止损价格
        
        Returns:
            Tuple[bool, str]: (是否止损, 原因)
        """
        if stop_price <= 0:
            return False, "止损价格无效"
        
        if current_price <= stop_price:
            return True, f"价格 {current_price:.8f} <= 止损价 {stop_price:.8f}"
        
        return False, "未触发止损"
    
    def is_ao_active(self, ao_values: list, min_length: int = 34) -> bool:
        """
        检查AO是否启动
        
        Args:
            ao_values: AO值列表
            min_length: 最小长度要求
        
        Returns:
            bool: AO是否启动
        """
        if not ao_values:
            return False
        
        # 过滤有效值
        valid_ao = [v for v in ao_values if v is not None]
        
        # 需要足够的数据
        if len(valid_ao) < min_length:
            return False
        
        # 检查最近10个AO值是否有波动
        recent_ao = valid_ao[-10:]
        
        # 如果所有值都接近0，说明AO未启动
        if all(abs(v) < 0.000001 for v in recent_ao):
            return False
        
        return True
    
    def calculate_profit_rate(self,
                             current_price: float,
                             avg_price: float) -> float:
        """
        计算收益率
        
        Args:
            current_price: 当前价格
            avg_price: 平均买入价
        
        Returns:
            float: 收益率
        """
        if avg_price <= 0:
            return 0.0
        
        return (current_price - avg_price) / avg_price
