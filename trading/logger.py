#!/usr/bin/env python3
"""
交易日志系统 - 记录所有关键交易决策和执行过程
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class TradeLogger:
    """交易日志记录器"""
    
    def __init__(self, name: str = "trading", log_dir: str = None):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_dir: 日志目录路径
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 设置日志目录
        if log_dir is None:
            log_dir = Path.home() / ".logearn" / "logs"
        else:
            log_dir = Path(log_dir)
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = log_dir / f"trading_{today}.log"
        self.trade_log_file = log_dir / f"trades_{today}.jsonl"
        
        # 清除已有的handlers
        self.logger.handlers.clear()
        
        # 文件Handler - 详细日志
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # 控制台Handler - 简洁输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_trade(self, trade_data: Dict[str, Any]):
        """
        记录交易数据到JSONL文件
        
        Args:
            trade_data: 交易数据字典
        """
        trade_data['timestamp'] = datetime.now().isoformat()
        
        with open(self.trade_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trade_data, ensure_ascii=False) + '\n')
    
    # ========== 交易执行日志 ==========
    
    def log_buy_attempt(self, ca: str, amount_sol: float, price: float):
        """记录买入尝试"""
        self.logger.info(f"🔵 买入尝试 | CA: {ca[:8]}... | 金额: {amount_sol} SOL | 价格: {price:.8f}")
        self.log_trade({
            'action': 'buy_attempt',
            'ca': ca,
            'amount_sol': amount_sol,
            'price': price
        })
    
    def log_buy_success(self, ca: str, amount_sol: float, price: float, tokens_received: float):
        """记录买入成功"""
        self.logger.info(f"✅ 买入成功 | CA: {ca[:8]}... | 花费: {amount_sol} SOL | 获得: {tokens_received:.2f} tokens")
        self.log_trade({
            'action': 'buy_success',
            'ca': ca,
            'amount_sol': amount_sol,
            'price': price,
            'tokens_received': tokens_received
        })
    
    def log_buy_failed(self, ca: str, amount_sol: float, reason: str):
        """记录买入失败"""
        self.logger.error(f"❌ 买入失败 | CA: {ca[:8]}... | 金额: {amount_sol} SOL | 原因: {reason}")
        self.log_trade({
            'action': 'buy_failed',
            'ca': ca,
            'amount_sol': amount_sol,
            'reason': reason
        })
    
    def log_sell_attempt(self, ca: str, percentage: float, price: float):
        """记录卖出尝试"""
        self.logger.info(f"🔴 卖出尝试 | CA: {ca[:8]}... | 比例: {percentage*100:.0f}% | 价格: {price:.8f}")
        self.log_trade({
            'action': 'sell_attempt',
            'ca': ca,
            'percentage': percentage,
            'price': price
        })
    
    def log_sell_success(self, ca: str, percentage: float, price: float, sol_received: float, profit_rate: float = None):
        """记录卖出成功"""
        profit_msg = f" | 收益率: {profit_rate*100:.2f}%" if profit_rate is not None else ""
        self.logger.info(f"✅ 卖出成功 | CA: {ca[:8]}... | 比例: {percentage*100:.0f}% | 获得: {sol_received:.4f} SOL{profit_msg}")
        self.log_trade({
            'action': 'sell_success',
            'ca': ca,
            'percentage': percentage,
            'price': price,
            'sol_received': sol_received,
            'profit_rate': profit_rate
        })
    
    def log_sell_failed(self, ca: str, percentage: float, reason: str):
        """记录卖出失败"""
        self.logger.error(f"❌ 卖出失败 | CA: {ca[:8]}... | 比例: {percentage*100:.0f}% | 原因: {reason}")
        self.log_trade({
            'action': 'sell_failed',
            'ca': ca,
            'percentage': percentage,
            'reason': reason
        })
    
    # ========== 信号检测日志 ==========
    
    def log_fib_signal(self, ca: str, signal_type: str, tier: str, price: float, fib_price: float):
        """记录Fibonacci信号"""
        self.logger.info(f"📊 FIB信号 | CA: {ca[:8]}... | 类型: {signal_type} | 档位: {tier} | 当前价: {price:.8f} | FIB价: {fib_price:.8f}")
        self.log_trade({
            'action': 'fib_signal',
            'ca': ca,
            'signal_type': signal_type,
            'tier': tier,
            'price': price,
            'fib_price': fib_price
        })
    
    def log_ao_signal(self, ca: str, ao_value: float, threshold: float, reason: str, price: float):
        """记录AO信号"""
        self.logger.info(f"📈 AO信号 | CA: {ca[:8]}... | AO: {ao_value:.8f} | 阈值: {threshold:.8f} | 原因: {reason} | 价格: {price:.8f}")
        self.log_trade({
            'action': 'ao_signal',
            'ca': ca,
            'ao_value': ao_value,
            'threshold': threshold,
            'reason': reason,
            'price': price
        })
    
    def log_rsi_signal(self, ca: str, rsi_value: float, signal_type: str, price: float):
        """记录RSI信号"""
        self.logger.info(f"📉 RSI信号 | CA: {ca[:8]}... | RSI: {rsi_value:.2f} | 类型: {signal_type} | 价格: {price:.8f}")
        self.log_trade({
            'action': 'rsi_signal',
            'ca': ca,
            'rsi_value': rsi_value,
            'signal_type': signal_type,
            'price': price
        })
    
    def log_stop_loss(self, ca: str, current_price: float, stop_price: float, reason: str):
        """记录止损触发"""
        self.logger.warning(f"⚠️ 止损触发 | CA: {ca[:8]}... | 当前价: {current_price:.8f} | 止损价: {stop_price:.8f} | 原因: {reason}")
        self.log_trade({
            'action': 'stop_loss',
            'ca': ca,
            'current_price': current_price,
            'stop_price': stop_price,
            'reason': reason
        })
    
    # ========== 仓位管理日志 ==========
    
    def log_position_check(self, ca: str, position_value: float, max_allowed: float, can_buy: bool):
        """记录仓位检查"""
        status = "✅ 可买入" if can_buy else "❌ 超限"
        self.logger.debug(f"💼 仓位检查 | CA: {ca[:8]}... | 当前: {position_value:.2f} SOL | 上限: {max_allowed:.2f} SOL | {status}")
        self.log_trade({
            'action': 'position_check',
            'ca': ca,
            'position_value': position_value,
            'max_allowed': max_allowed,
            'can_buy': can_buy
        })
    
    def log_capital_check(self, ca: str, invested: float, total_capital: float, can_buy: bool):
        """记录资金检查"""
        status = "✅ 可买入" if can_buy else "❌ 资金不足"
        self.logger.debug(f"💰 资金检查 | CA: {ca[:8]}... | 已投入: {invested:.2f} SOL | 总资金: {total_capital:.2f} SOL | {status}")
        self.log_trade({
            'action': 'capital_check',
            'ca': ca,
            'invested': invested,
            'total_capital': total_capital,
            'can_buy': can_buy
        })
    
    def log_weighted_avg_price(self, ca: str, avg_price: float, total_amount: float):
        """记录加权均价计算"""
        self.logger.debug(f"📊 加权均价 | CA: {ca[:8]}... | 均价: {avg_price:.8f} | 总量: {total_amount:.2f}")
        self.log_trade({
            'action': 'weighted_avg_price',
            'ca': ca,
            'avg_price': avg_price,
            'total_amount': total_amount
        })
    
    # ========== K线数据日志 ==========
    
    def log_kline_fetch(self, ca: str, interval: str, count: int, from_cache: bool):
        """记录K线获取"""
        source = "缓存" if from_cache else "API"
        self.logger.debug(f"📊 K线获取 | CA: {ca[:8]}... | 周期: {interval} | 数量: {count} | 来源: {source}")
    
    def log_kline_cache_update(self, ca: str, interval: str, new_count: int, total_count: int):
        """记录K线缓存更新"""
        self.logger.debug(f"🔄 缓存更新 | CA: {ca[:8]}... | 周期: {interval} | 新增: {new_count} | 总计: {total_count}")
    
    # ========== 策略执行日志 ==========
    
    def log_strategy_start(self, strategy: str, ca: str, params: Dict[str, Any]):
        """记录策略启动"""
        self.logger.info(f"🚀 策略启动 | 策略: {strategy} | CA: {ca[:8]}... | 参数: {params}")
        self.log_trade({
            'action': 'strategy_start',
            'strategy': strategy,
            'ca': ca,
            'params': params
        })
    
    def log_strategy_stop(self, strategy: str, ca: str, reason: str, summary: Dict[str, Any] = None):
        """记录策略停止"""
        self.logger.info(f"🛑 策略停止 | 策略: {strategy} | CA: {ca[:8]}... | 原因: {reason}")
        if summary:
            self.logger.info(f"📊 交易总结 | {summary}")
        self.log_trade({
            'action': 'strategy_stop',
            'strategy': strategy,
            'ca': ca,
            'reason': reason,
            'summary': summary
        })
    
    def log_check_cycle(self, strategy: str, ca: str, cycle_num: int):
        """记录检查周期"""
        self.logger.debug(f"🔄 检查周期 #{cycle_num} | 策略: {strategy} | CA: {ca[:8]}...")
    
    # ========== 错误日志 ==========
    
    def log_error(self, context: str, error: Exception, ca: str = None):
        """记录错误"""
        ca_info = f" | CA: {ca[:8]}..." if ca else ""
        self.logger.error(f"❌ 错误 | 上下文: {context}{ca_info} | 错误: {str(error)}")
        self.log_trade({
            'action': 'error',
            'context': context,
            'ca': ca,
            'error': str(error),
            'error_type': type(error).__name__
        })
    
    def log_warning(self, message: str, ca: str = None):
        """记录警告"""
        ca_info = f" | CA: {ca[:8]}..." if ca else ""
        self.logger.warning(f"⚠️ 警告 | {message}{ca_info}")
    
    # ========== 通用日志方法 ==========
    
    def info(self, message: str):
        """记录信息"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def error(self, message: str):
        """记录错误"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """记录警告"""
        self.logger.warning(message)


# 全局日志实例
_global_logger: Optional[TradeLogger] = None


def get_logger(name: str = "trading", log_dir: str = None) -> TradeLogger:
    """
    获取全局日志实例（单例模式）
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录路径
    
    Returns:
        TradeLogger实例
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = TradeLogger(name, log_dir)
    
    return _global_logger


def reset_logger():
    """重置全局日志实例（主要用于测试）"""
    global _global_logger
    _global_logger = None
