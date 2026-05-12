#!/usr/bin/env python3
"""
交易执行器 - 负责买入和卖出操作
"""

import os
import subprocess
import json
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TradeResult:
    """交易结果"""
    success: bool
    code: int
    message: str
    data: Optional[Dict] = None
    error: Optional[str] = None


class TradeExecutor:
    """交易执行器"""
    
    SOL_ADDRESS = "So11111111111111111111111111111111111111112"
    
    def __init__(self, logearn_cli_path: str = None):
        """
        初始化交易执行器
        
        Args:
            logearn_cli_path: LogEarn CLI路径
        
        Note:
            LogEarn skill与token绑定，不需要手动指定钱包
        """
        
        if logearn_cli_path is None:
            # 默认路径
            from pathlib import Path
            root = Path(__file__).parent.parent
            self.logearn_cli = str(root / "../.hermes/skills/logearn/logearn-cli.py")
        else:
            self.logearn_cli = logearn_cli_path
        
        self.api_key = os.getenv("LOGEARN_API_KEY", "")
        if not self.api_key:
            raise ValueError("LOGEARN_API_KEY not set")
    
    def _logearn_swap(self, action: str, token_in: str, token_out: str, 
                      amount_in: str) -> Dict:
        """
        调用LogEarn swap接口
        
        Args:
            action: buy/sell
            token_in: 输入token地址
            token_out: 输出token地址
            amount_in: 输入数量（lamports或token最小单位）
        
        Returns:
            Dict: 交易结果
        """
        try:
            result = subprocess.run(
                [
                    "python3", self.logearn_cli,
                    "log-swap",
                    "--token-in", token_in,
                    "--token-out", token_out,
                    "--amount-in", amount_in,
                    "--slippage", "0.02",
                    "--raw"
                ],
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "LOGEARN_API_KEY": self.api_key}
            )
            
            if result.returncode != 0:
                return {
                    "code": -1,
                    "error": f"CLI调用失败: {result.stderr}"
                }
            
            data = json.loads(result.stdout)
            return data
            
        except subprocess.TimeoutExpired:
            return {"code": -1, "error": "交易超时"}
        except json.JSONDecodeError as e:
            return {"code": -1, "error": f"JSON解析失败: {e}"}
        except Exception as e:
            return {"code": -1, "error": f"交易异常: {e}"}
    
    def buy(self, ca: str, amount_sol: float, limit_price: float = None,
            current_price: float = None, slippage: float = 0.02) -> TradeResult:
        """
        买入token
        
        Args:
            ca: token地址
            amount_sol: 买入金额（SOL）
            limit_price: 限价（可选）
            current_price: 当前价格（用于限价检查）
            slippage: 滑点容忍度
        
        Returns:
            TradeResult: 交易结果
        """
        # 限价检查
        if limit_price and current_price:
            max_price = limit_price * (1 + slippage)
            if current_price > max_price:
                return TradeResult(
                    success=False,
                    code=-1,
                    message=f"当前价 {current_price:.8f} 超出限价 {limit_price:.8f}",
                    error="price_exceeded"
                )
        
        # 转换为lamports
        lamports = int(amount_sol * 1e9)
        
        # 执行交易
        resp = self._logearn_swap(
            action="buy",
            token_in=self.SOL_ADDRESS,
            token_out=ca,
            amount_in=str(lamports)
        )
        
        success = resp.get("code") == 200
        return TradeResult(
            success=success,
            code=resp.get("code", -1),
            message=resp.get("message", ""),
            data=resp.get("data"),
            error=resp.get("error")
        )
    
    def sell(self, ca: str, amount: float = None, percentage: float = 1.0) -> TradeResult:
        """
        卖出token
        
        Args:
            ca: token地址
            amount: 卖出数量（None=全部）
            percentage: 卖出比例（0-1，默认1.0=全部）
        
        Returns:
            TradeResult: 交易结果
        """
        # 获取持仓
        positions = self.get_positions()
        
        # 查找对应持仓
        position = None
        for p in positions:
            if p.get("token_address", "").lower() == ca.lower():
                position = p
                break
        
        if not position:
            return TradeResult(
                success=False,
                code=-1,
                message=f"未找到持仓 {ca}",
                error="position_not_found"
            )
        
        hold_amount = float(position.get("hold_amount", 0))
        decimals = int(position.get("decimals", 6))
        
        if hold_amount <= 0:
            return TradeResult(
                success=False,
                code=-1,
                message="持仓为0",
                error="zero_position"
            )
        
        # 计算卖出数量
        if amount is None:
            sell_amount = hold_amount * percentage
        else:
            sell_amount = min(amount, hold_amount)
        
        # 转换为最小单位
        amount_in = str(int(sell_amount * (10 ** decimals)))
        
        # 执行交易
        resp = self._logearn_swap(
            action="sell",
            token_in=ca,
            token_out=self.SOL_ADDRESS,
            amount_in=amount_in
        )
        
        success = resp.get("code") == 200
        return TradeResult(
            success=success,
            code=resp.get("code", -1),
            message=resp.get("message", ""),
            data=resp.get("data"),
            error=resp.get("error")
        )
    
    def get_positions(self) -> list:
        """
        获取当前持仓
        
        Returns:
            list: 持仓列表
        """
        try:
            result = subprocess.run(
                [
                    "python3", self.logearn_cli,
                    "log-get-positions",
                    "--raw"
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "LOGEARN_API_KEY": self.api_key}
            )
            
            data = json.loads(result.stdout)
            
            # 处理不同的返回格式
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            
            return []
            
        except Exception as e:
            print(f"获取持仓失败: {e}")
            return []
