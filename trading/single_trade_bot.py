#!/usr/bin/env python3
"""
单次交易机器人 - 只在一个币上开仓关仓交易一次就停止
"""

import time
from typing import Dict, Optional
from .executor import TradeExecutor
from .fib_calculator import parse_klines, fib_signal
from .position_manager import PositionManager
from .config import DEFAULT_CONFIG


class SingleTradeBot:
    """单次交易机器人"""
    
    def __init__(self, wallet: str, ca: str, total_capital: float = 2.0, 
                 logearn_cli_path: str = None):
        """
        初始化单次交易机器人
        
        Args:
            wallet: 钱包地址
            ca: 代币地址
            total_capital: 总资金（SOL）
            logearn_cli_path: LogEarn CLI路径
        """
        self.wallet = wallet
        self.ca = ca
        self.total_capital = total_capital
        
        # 初始化交易执行器
        self.executor = TradeExecutor(wallet, logearn_cli_path)
        
        # 初始化仓位管理器
        self.position_manager = PositionManager(
            max_position_ratio=DEFAULT_CONFIG.position.max_position_ratio,
            min_position_sol=DEFAULT_CONFIG.position.min_position_sol,
            trading_end_hour=24  # 全天交易
        )
        
        # 交易状态
        self.tiers_bought = []
        self.entry_prices = {}
        self.entry_amounts = {}
        self.pending_tiers = []
        self.entry_swing_high = None
        self.entry_stop_price = None
        self.fib_sold_tiers = []
        
        # 交易完成标志
        self.trade_completed = False
        
    def run(self, klines_provider, check_interval: int = 60):
        """
        运行单次交易机器人
        
        Args:
            klines_provider: K线数据提供函数，返回 List[dict]
            check_interval: 检查间隔（秒）
        """
        print(f"🤖 单次交易机器人启动")
        print(f"钱包: {self.wallet}")
        print(f"代币: {self.ca}")
        print(f"总资金: {self.total_capital} SOL")
        print(f"检查间隔: {check_interval}秒")
        print("="*80)
        
        while not self.trade_completed:
            try:
                # 获取最新K线
                raw_klines = klines_provider()
                if not raw_klines:
                    print("⚠️ 未获取到K线数据，等待下次检查...")
                    time.sleep(check_interval)
                    continue
                
                # 解析K线
                klines = parse_klines(raw_klines)
                
                # 计算加权均价
                avg_price = self.position_manager.calculate_weighted_avg_price(
                    self.entry_prices, self.entry_amounts, self.tiers_bought
                ) if self.tiers_bought else None
                
                # 检测信号
                signal = fib_signal(
                    klines,
                    entry_price=avg_price,
                    tiers_bought=self.tiers_bought,
                    pending_tiers=self.pending_tiers,
                    skip_ao=False,
                    entry_swing_high=self.entry_swing_high,
                    entry_stop_price=self.entry_stop_price,
                    fib_sold_tiers=self.fib_sold_tiers
                )
                
                if not signal:
                    time.sleep(check_interval)
                    continue
                
                action = signal.get("action")
                
                # 处理买入信号
                if action in ["buy_618", "buy_786", "buy_861"]:
                    self._handle_buy(action, signal, klines[-1])
                
                # 处理卖出信号
                elif action in ["sell", "fib_sell", "stop"]:
                    self._handle_sell(action, signal, klines[-1])
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断，退出...")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(check_interval)
        
        print("\n" + "="*80)
        print("✅ 交易完成，机器人停止")
    
    def _handle_buy(self, action: str, signal: Dict, current_kline):
        """处理买入信号"""
        # 检查是否可以买入
        can_buy, reason = self.position_manager.check_can_buy(
            tier=action,
            tiers_bought=self.tiers_bought,
            total_capital=self.total_capital,
            api_price=current_kline.close
        )
        
        if not can_buy:
            print(f"⚠️ 无法买入 {action}: {reason}")
            return
        
        # 计算买入金额
        buy_amount = self.position_manager.calculate_position_size(
            tier=action,
            total_capital=self.total_capital
        )
        
        if buy_amount < self.position_manager.min_position_sol:
            print(f"⚠️ 买入金额 {buy_amount:.4f} SOL < 最小金额 {self.position_manager.min_position_sol} SOL")
            return
        
        # 执行买入
        print(f"\n📈 买入信号: {action}")
        print(f"   价格: {current_kline.close:.8f} SOL")
        print(f"   金额: {buy_amount:.4f} SOL")
        
        result = self.executor.buy(
            ca=self.ca,
            amount_sol=buy_amount,
            current_price=current_kline.close
        )
        
        if result.success:
            print(f"   ✅ 买入成功")
            
            # 更新状态
            self.tiers_bought.append(action)
            self.entry_prices[action] = current_kline.close
            self.entry_amounts[action] = buy_amount / current_kline.close
            
            # 锁定波峰和止损
            if self.entry_swing_high is None:
                self.entry_swing_high = signal.get("swing_high")
                self.entry_stop_price = signal.get("stop_price")
            
            # 更新待买档位
            self.pending_tiers = signal.get("pending", [])
        else:
            print(f"   ❌ 买入失败: {result.message}")
    
    def _handle_sell(self, action: str, signal: Dict, current_kline):
        """处理卖出信号"""
        if not self.tiers_bought:
            print("⚠️ 无持仓，跳过卖出")
            return
        
        # 确定卖出比例
        if action == "sell":
            # AO卖出 - 全部卖出
            sell_percentage = 1.0
            reason = "AO卖出"
        elif action == "stop":
            # 止损 - 全部卖出
            sell_percentage = 1.0
            reason = "止损"
        elif action == "fib_sell":
            # Fib卖出 - 部分卖出
            tier = signal.get("tier")
            sell_percentage = signal.get("percentage", 0.3)
            reason = f"Fib卖出 {tier}"
        else:
            return
        
        # 执行卖出
        print(f"\n📉 卖出信号: {reason}")
        print(f"   价格: {current_kline.close:.8f} SOL")
        print(f"   比例: {sell_percentage*100:.0f}%")
        
        result = self.executor.sell(
            ca=self.ca,
            percentage=sell_percentage
        )
        
        if result.success:
            print(f"   ✅ 卖出成功")
            
            # 更新状态
            if action == "fib_sell":
                tier = signal.get("tier")
                self.fib_sold_tiers.append(tier)
            
            # 如果全部卖出，标记交易完成
            if sell_percentage >= 1.0:
                self.trade_completed = True
                print("\n🎉 交易完成！")
        else:
            print(f"   ❌ 卖出失败: {result.message}")


def run_single_trade(wallet: str, ca: str, klines_provider, 
                     total_capital: float = 2.0, check_interval: int = 60):
    """
    运行单次交易
    
    Args:
        wallet: 钱包地址
        ca: 代币地址
        klines_provider: K线数据提供函数
        total_capital: 总资金（SOL）
        check_interval: 检查间隔（秒）
    
    Example:
        def get_klines():
            # 从API获取K线数据
            return fetch_klines(ca)
        
        run_single_trade(
            wallet="你的钱包地址",
            ca="代币地址",
            klines_provider=get_klines,
            total_capital=2.0,
            check_interval=60
        )
    """
    bot = SingleTradeBot(wallet, ca, total_capital)
    bot.run(klines_provider, check_interval)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python single_trade_bot.py <钱包地址> <代币地址>")
        sys.exit(1)
    
    wallet = sys.argv[1]
    ca = sys.argv[2]
    
    # 示例：需要实现 get_klines 函数
    def get_klines():
        # TODO: 从API获取K线数据
        # 例如：从 GMGN 或其他数据源获取
        raise NotImplementedError("请实现 get_klines 函数")
    
    run_single_trade(wallet, ca, get_klines)
