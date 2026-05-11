#!/usr/bin/env python3
"""
仓位管理器 - 负责仓位计算和限制检查
"""

from typing import Dict, Tuple, Optional
from datetime import datetime, timezone, timedelta


class PositionManager:
    """仓位管理器"""
    
    def __init__(self, 
                 max_position_ratio: float = 0.30,
                 min_position_sol: float = 0.005,
                 trading_start_hour: int = 0,
                 trading_end_hour: int = 24):
        """
        初始化仓位管理器
        
        Args:
            max_position_ratio: 单币最大仓位比例（默认30%）
            min_position_sol: 最小买入金额（默认0.005 SOL）
            trading_start_hour: 交易开始时间（北京时间，默认0点）
            trading_end_hour: 交易结束时间（北京时间，默认24点=全天交易）
        """
        self.max_position_ratio = max_position_ratio
        self.min_position_sol = min_position_sol
        self.trading_start_hour = trading_start_hour
        self.trading_end_hour = trading_end_hour
        
        # 仓位档位配置
        self.tier_sizes = {
            "buy_618": 0.03,  # 3%
            "buy_786": 0.02,  # 2%
            "buy_861": 0.01,  # 1%
        }
    
    def is_trading_time_allowed(self) -> Tuple[bool, str]:
        """
        检查是否在允许的交易时间内
        
        Returns:
            Tuple[bool, str]: (是否允许, 原因)
        """
        # 北京时间 = UTC+8
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        hour = now_beijing.hour
        
        if hour >= self.trading_end_hour:
            return False, f"北京时间{hour}点 >= {self.trading_end_hour}点，禁止开仓"
        
        return True, "允许交易"
    
    def calculate_position_size(self, total_capital: float, tier: str) -> float:
        """
        计算买入金额
        
        Args:
            total_capital: 总资金
            tier: 买入档位（buy_618/buy_786/buy_861）
        
        Returns:
            float: 买入金额（SOL）
        """
        ratio = self.tier_sizes.get(tier, 0.01)
        return total_capital * ratio
    
    def can_buy(self, 
                ca: str,
                amount_sol: float,
                total_capital: float,
                positions: list,
                current_price: float = None) -> Tuple[bool, str]:
        """
        检查是否可以买入
        
        Args:
            ca: token地址
            amount_sol: 买入金额（SOL）
            total_capital: 总资金
            positions: 当前持仓列表
            current_price: 当前价格（可选）
        
        Returns:
            Tuple[bool, str]: (是否可以买入, 原因)
        """
        # 1. 时间锁检查
        allowed, reason = self.is_trading_time_allowed()
        if not allowed:
            return False, reason
        
        # 2. 最小金额检查
        if amount_sol < self.min_position_sol:
            return False, f"金额 {amount_sol} < 最低 {self.min_position_sol} SOL"
        
        # 3. 仓位上限检查
        limit = total_capital * self.max_position_ratio
        
        # 查找当前持仓
        for p in positions:
            if p.get("token_address", "").lower() == ca.lower():
                hold_amount = float(p.get("hold_amount", 0))
                
                if hold_amount > 0:
                    # 使用API价格计算当前市值
                    api_price = float(p.get("last_price", 0))
                    
                    if api_price <= 0:
                        return False, f"API价格无效（{api_price}）"
                    
                    current_val = hold_amount * api_price
                    new_total = current_val + amount_sol
                    
                    if new_total > limit:
                        return False, (
                            f"超仓: 持仓 {current_val:.4f} SOL + "
                            f"本次 {amount_sol:.4f} SOL = "
                            f"{new_total:.4f} SOL > 上限 {limit:.4f} SOL"
                        )
                break
        
        return True, "允许买入"
    
    def get_position_value(self, positions: list, ca: str = None) -> float:
        """
        获取持仓市值
        
        Args:
            positions: 持仓列表
            ca: token地址（None=所有持仓）
        
        Returns:
            float: 持仓市值（SOL）
        """
        total_value = 0.0
        
        for p in positions:
            # 如果指定了ca，只计算该ca的持仓
            if ca and p.get("token_address", "").lower() != ca.lower():
                continue
            
            hold_amount = float(p.get("hold_amount", 0))
            if hold_amount > 0:
                api_price = float(p.get("last_price", 0))
                if api_price > 0:
                    total_value += hold_amount * api_price
        
        return total_value
    
    def get_position_ratio(self, positions: list, total_capital: float, 
                          ca: str = None) -> float:
        """
        获取持仓比例
        
        Args:
            positions: 持仓列表
            total_capital: 总资金
            ca: token地址（None=所有持仓）
        
        Returns:
            float: 持仓比例（0-1）
        """
        if total_capital <= 0:
            return 0.0
        
        value = self.get_position_value(positions, ca)
        return value / total_capital
    
    def calculate_weighted_avg_price(self, 
                                     entry_prices: Dict[str, float],
                                     entry_amounts: Dict[str, float],
                                     tiers_bought: list) -> float:
        """
        计算加权平均买入价
        
        Args:
            entry_prices: 各档位买入价格 {tier: price}
            entry_amounts: 各档位买入金额 {tier: amount_sol}
            tiers_bought: 已买入档位列表
        
        Returns:
            float: 加权平均价格
        """
        total_sol = 0.0
        total_tokens = 0.0
        
        for tier in tiers_bought:
            price = entry_prices.get(tier, 0)
            sol = entry_amounts.get(tier, 0)
            
            if price > 0 and sol > 0:
                tokens = sol / price
                total_sol += sol
                total_tokens += tokens
        
        if total_tokens <= 0:
            return 0.0
        
        return total_sol / total_tokens
