#!/usr/bin/env python3
"""
RSI定投机器人 - 基于RSI指标的定投策略
"""

import time
from typing import Callable
from datetime import datetime
from .executor import TradeExecutor
from .indicators import calculate_rsi
from .kline_service import get_klines


class RSIDCABot:
    """RSI定投机器人"""
    
    def __init__(self, ca: str, dca_amount: float, max_buy_count: int, 
                 rsi_period: int = 14, rsi_buy_threshold: float = 30.0,
                 rsi_reset_threshold: float = 50.0):
        """
        初始化RSI定投机器人
        
        Args:
            ca: 代币地址
            dca_amount: 每次定投金额（SOL）
            max_buy_count: 最大定投次数
            rsi_period: RSI周期（默认14）
            rsi_buy_threshold: RSI买入阈值（默认30）
            rsi_reset_threshold: RSI重置阈值（默认50）
        
        Note:
            - RSI < rsi_buy_threshold 时触发买入
            - 买入后等待 RSI > rsi_reset_threshold 才能再次买入
            - 达到 max_buy_count 后停止
        """
        self.ca = ca
        self.dca_amount = dca_amount
        self.max_buy_count = max_buy_count
        self.rsi_period = rsi_period
        self.rsi_buy_threshold = rsi_buy_threshold
        self.rsi_reset_threshold = rsi_reset_threshold
        
        # 初始化交易执行器
        self.executor = TradeExecutor()
        
        # 状态变量
        self.buy_count = 0              # 已买入次数
        self.waiting_for_reset = False  # 是否在等待RSI回到50
        self.last_rsi = None            # 上一次的RSI值
        
    def run(self, interval: str = '1h', check_interval: int = 300):
        """
        运行定投机器人
        
        Args:
            interval: K线周期（'1m', '5m', '15m', '1h', '1d'）
            check_interval: 检查间隔（秒，默认300秒=5分钟）
        
        Example:
            bot = RSIDCABot(
                ca="代币地址",
                dca_amount=0.1,
                max_buy_count=10
            )
            bot.run(interval='1h', check_interval=300)
        """
        print("="*80)
        print("🤖 RSI定投机器人启动")
        print("="*80)
        print(f"代币地址: {self.ca}")
        print(f"定投金额: {self.dca_amount} SOL")
        print(f"最大次数: {self.max_buy_count}")
        print(f"RSI周期: {self.rsi_period}")
        print(f"买入阈值: RSI < {self.rsi_buy_threshold}")
        print(f"重置阈值: RSI > {self.rsi_reset_threshold}")
        print(f"K线周期: {interval}")
        print(f"检查间隔: {check_interval}秒")
        print("="*80)
        print()
        
        while self.buy_count < self.max_buy_count:
            try:
                # 1. 获取K线数据
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取K线数据...")
                klines = get_klines(self.ca, interval, page_size=200)
                
                print(f"  ✅ 获取{len(klines)}根K线")
                
                # 2. 计算RSI
                try:
                    rsi = calculate_rsi(klines, self.rsi_period)
                    self.last_rsi = rsi
                    print(f"  📊 当前RSI: {rsi:.2f}")
                except ValueError as e:
                    print(f"  ⚠️ RSI计算失败: {e}")
                    time.sleep(check_interval)
                    continue
                
                # 3. 状态判断
                if self.waiting_for_reset:
                    # 等待RSI回到重置阈值以上
                    print(f"  ⏳ 等待RSI回到{self.rsi_reset_threshold}以上...")
                    if rsi >= self.rsi_reset_threshold:
                        self.waiting_for_reset = False
                        print(f"  ✅ RSI回到{self.rsi_reset_threshold}以上({rsi:.2f})，可以再次买入")
                else:
                    # 检查是否触发买入
                    if rsi < self.rsi_buy_threshold:
                        print(f"  🎯 触发买入条件: RSI({rsi:.2f}) < {self.rsi_buy_threshold}")
                        self._execute_buy(klines[-1], rsi)
                        self.waiting_for_reset = True
                    else:
                        print(f"  ⏸️  未触发买入: RSI({rsi:.2f}) >= {self.rsi_buy_threshold}")
                
                # 4. 显示进度
                print(f"  📈 定投进度: {self.buy_count}/{self.max_buy_count}")
                print()
                
                # 5. 等待下一次检查
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断，退出...")
                break
            except Exception as e:
                print(f"  ❌ 错误: {e}")
                print(f"  等待{check_interval}秒后重试...")
                time.sleep(check_interval)
        
        print("="*80)
        print(f"🎉 定投完成！总共买入{self.buy_count}次")
        print("="*80)
    
    def _execute_buy(self, current_kline, rsi):
        """执行买入"""
        print(f"\n  📈 RSI定投买入")
        print(f"     RSI: {rsi:.2f}")
        print(f"     价格: {current_kline.close:.8f} SOL")
        print(f"     金额: {self.dca_amount} SOL")
        print(f"     次数: {self.buy_count + 1}/{self.max_buy_count}")
        
        result = self.executor.buy(
            ca=self.ca,
            amount_sol=self.dca_amount,
            current_price=current_kline.close
        )
        
        if result.success:
            self.buy_count += 1
            print(f"     ✅ 买入成功")
        else:
            print(f"     ❌ 买入失败: {result.message}")
    
    def get_status(self) -> dict:
        """
        获取机器人状态
        
        Returns:
            状态信息字典
        """
        return {
            "ca": self.ca,
            "dca_amount": self.dca_amount,
            "max_buy_count": self.max_buy_count,
            "buy_count": self.buy_count,
            "waiting_for_reset": self.waiting_for_reset,
            "last_rsi": self.last_rsi,
            "progress": f"{self.buy_count}/{self.max_buy_count}",
            "completed": self.buy_count >= self.max_buy_count
        }


def run_rsi_dca(ca: str, dca_amount: float, max_buy_count: int,
                interval: str = '1h', check_interval: int = 300,
                rsi_period: int = 14, rsi_buy_threshold: float = 30.0,
                rsi_reset_threshold: float = 50.0):
    """
    运行RSI定投（快捷函数）
    
    Args:
        ca: 代币地址
        dca_amount: 每次定投金额（SOL）
        max_buy_count: 最大定投次数
        interval: K线周期（默认'1h'）
        check_interval: 检查间隔（秒，默认300）
        rsi_period: RSI周期（默认14）
        rsi_buy_threshold: RSI买入阈值（默认30）
        rsi_reset_threshold: RSI重置阈值（默认50）
    
    Example:
        run_rsi_dca(
            ca="代币地址",
            dca_amount=0.1,
            max_buy_count=10,
            interval='1h',
            check_interval=300
        )
    """
    bot = RSIDCABot(
        ca=ca,
        dca_amount=dca_amount,
        max_buy_count=max_buy_count,
        rsi_period=rsi_period,
        rsi_buy_threshold=rsi_buy_threshold,
        rsi_reset_threshold=rsi_reset_threshold
    )
    
    bot.run(interval=interval, check_interval=check_interval)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("用法: python rsi_dca_bot.py <代币地址> <定投金额> <最大次数> [K线周期]")
        print("示例: python rsi_dca_bot.py FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump 0.1 10 1h")
        sys.exit(1)
    
    ca = sys.argv[1]
    dca_amount = float(sys.argv[2])
    max_buy_count = int(sys.argv[3])
    interval = sys.argv[4] if len(sys.argv) > 4 else '1h'
    
    run_rsi_dca(
        ca=ca,
        dca_amount=dca_amount,
        max_buy_count=max_buy_count,
        interval=interval
    )
