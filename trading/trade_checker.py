#!/usr/bin/env python3
"""
交易检测器 - 检测K线是否符合一次完整交易
100% 复用核心交易逻辑，不重新实现任何判断
"""

from typing import List, Dict, Optional
from .fib_calculator import Kline, parse_klines, fib_signal
from .position_manager import PositionManager
from .config import DEFAULT_CONFIG


def check_single_trade(klines: List[Kline], 
                       total_capital: float = 2.0,
                       config = None) -> Dict:
    """
    检测K线是否符合一次完整交易（买入→卖出）
    
    核心逻辑：
    1. 100% 复用 fib_signal() 判断买卖信号
    2. 100% 复用 PositionManager 计算仓位
    3. 只记录交易过程，不改变任何逻辑
    
    Args:
        klines: K线数据列表
        total_capital: 总资金（SOL）
        config: 交易配置
    
    Returns:
        Dict: {
            "matched": True/False,  # 是否匹配到完整交易
            "buy_points": [...],    # 买入点列表
            "sell_point": {...},    # 卖出点
            "profit": {...}         # 利润信息
        }
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 初始化 PositionManager（100% 复用）
    position_manager = PositionManager(
        max_position_ratio=config.position.max_position_ratio,
        min_position_sol=config.position.min_position_sol,
        trading_end_hour=24  # 检测器允许全天
    )
    
    # 状态变量（与实际交易逻辑完全一致）
    tiers_bought = []
    entry_prices = {}
    entry_amounts = {}
    pending_tiers = []
    entry_swing_high = None
    entry_stop_price = None
    fib_sold_tiers = []
    
    # 记录变量
    buy_records = []
    sell_record = None
    
    # 逐根K线遍历
    for i in range(len(klines)):
        current_klines = klines[:i+1]
        
        # 计算加权均价（100% 复用 PositionManager 逻辑）
        avg_price = position_manager.calculate_weighted_avg_price(
            entry_prices, entry_amounts, tiers_bought
        ) if tiers_bought else None
        
        # 调用核心信号函数（100% 复用）
        signal = fib_signal(
            current_klines,
            entry_price=avg_price,
            tiers_bought=tiers_bought,
            pending_tiers=pending_tiers,
            skip_ao=False,
            entry_swing_high=entry_swing_high,
            entry_stop_price=entry_stop_price,
            fib_sold_tiers=fib_sold_tiers
        )
        
        if not signal:
            continue
        
        action = signal.get("action")
        
        # 买入信号
        if action in ["buy_618", "buy_786", "buy_861"]:
            tier = action
            price = signal.get("price")
            
            # 使用 PositionManager 计算仓位（100% 复用）
            amount = position_manager.calculate_position_size(total_capital, tier)
            
            # 记录买入
            buy_records.append({
                "tier": tier,
                "price": price,
                "amount": amount,
                "kline_index": i,
                "timestamp": klines[i].time
            })
            
            # 更新状态（与实际交易完全一致）
            tiers_bought.append(tier)
            entry_prices[tier] = price
            entry_amounts[tier] = amount
            
            # 首次买入时记录波峰和止损价
            if entry_swing_high is None:
                entry_swing_high = signal.get("swing_high")
                entry_stop_price = signal.get("stop_price")
            
            # 更新 pending
            pending_tiers = signal.get("pending", [])
        
        # 卖出信号（AO 卖出）
        elif action == "sell":
            sell_record = {
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": signal.get("ao_reason", "AO卖出信号"),
                "type": "ao_sell"
            }
            break  # 一次交易结束
        
        # 止损信号
        elif action == "stop":
            sell_record = {
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": "触发止损",
                "type": "stop_loss"
            }
            break  # 一次交易结束
        
        # Fib 卖出信号
        elif action == "fib_sell":
            percentage = signal.get("percentage", 0.3)
            tier = signal.get("tier", "")
            
            # 记录 Fib 卖出
            sell_record = {
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": signal.get("reason", "Fib卖出信号"),
                "type": "fib_sell",
                "percentage": percentage,
                "tier": tier
            }
            
            # 标记已卖出档位
            fib_sold_tiers.append(tier)
            
            # 如果是全部卖出，结束交易
            if percentage >= 1.0:
                break
            # 否则继续（可能还有后续卖出）
    
    # 计算利润
    if buy_records and sell_record:
        profit = _calculate_profit(
            entry_prices, 
            entry_amounts, 
            tiers_bought, 
            sell_record["price"],
            sell_record.get("percentage", 1.0)
        )
        
        return {
            "matched": True,
            "buy_points": buy_records,
            "sell_point": sell_record,
            "profit": profit
        }
    else:
        return {
            "matched": False,
            "buy_points": buy_records,
            "sell_point": None,
            "profit": None
        }


def _calculate_profit(entry_prices: Dict[str, float],
                     entry_amounts: Dict[str, float],
                     tiers_bought: List[str],
                     sell_price: float,
                     sell_percentage: float = 1.0) -> Dict:
    """
    计算利润
    
    Args:
        entry_prices: 各档位买入价格
        entry_amounts: 各档位买入金额
        tiers_bought: 已买入档位
        sell_price: 卖出价格
        sell_percentage: 卖出比例
    
    Returns:
        Dict: 利润信息
    """
    # 计算总投入
    total_invested = sum(entry_amounts[tier] for tier in tiers_bought)
    
    # 计算总持仓 tokens
    total_tokens = sum(
        entry_amounts[tier] / entry_prices[tier]
        for tier in tiers_bought
    )
    
    # 计算卖出 tokens 和回报
    tokens_sold = total_tokens * sell_percentage
    total_returned = tokens_sold * sell_price
    
    # 计算利润
    profit_sol = total_returned - total_invested
    profit_rate = profit_sol / total_invested if total_invested > 0 else 0.0
    
    return {
        "invested": total_invested,
        "returned": total_returned,
        "profit_sol": profit_sol,
        "profit_rate": profit_rate
    }


def check_single_trade_from_raw(raw_klines: List[dict],
                                total_capital: float = 2.0,
                                config = None) -> Dict:
    """
    从原始K线数据检测交易
    
    Args:
        raw_klines: 原始K线数据
        total_capital: 总资金
        config: 交易配置
    
    Returns:
        Dict: 检测结果
    """
    klines = parse_klines(raw_klines)
    return check_single_trade(klines, total_capital, config)


def print_trade_result(result: Dict):
    """
    打印交易检测结果
    
    Args:
        result: check_single_trade() 返回的结果
    """
    if not result["matched"]:
        print("❌ 未匹配到完整交易")
        if result.get("buy_points"):
            print(f"   已有 {len(result['buy_points'])} 个买入点，但未触发卖出")
        return
    
    print("✅ 匹配到完整交易")
    print()
    
    # 买入点
    print("📊 买入点:")
    for i, buy in enumerate(result["buy_points"], 1):
        print(f"  {i}. {buy['tier']}")
        print(f"     价格: {buy['price']:.8f}")
        print(f"     金额: {buy['amount']:.4f} SOL")
        print(f"     K线: #{buy['kline_index']}")
    
    print()
    
    # 卖出点
    sell = result["sell_point"]
    print("📈 卖出点:")
    print(f"  价格: {sell['price']:.8f}")
    print(f"  K线: #{sell['kline_index']}")
    print(f"  原因: {sell['reason']}")
    print(f"  类型: {sell['type']}")
    
    print()
    
    # 利润
    profit = result["profit"]
    profit_emoji = "🟢" if profit["profit_rate"] >= 0 else "🔴"
    print("💰 利润:")
    print(f"  投入: {profit['invested']:.4f} SOL")
    print(f"  回报: {profit['returned']:.4f} SOL")
    print(f"  利润: {profit_emoji} {profit['profit_sol']:+.4f} SOL")
    print(f"  收益率: {profit_emoji} {profit['profit_rate']*100:+.2f}%")


if __name__ == "__main__":
    # 示例：创建测试K线数据
    print("交易检测器示例\n")
    
    raw_klines = []
    base_time = 1000000
    
    # 下跌阶段
    for i in range(20):
        high = 0.0001 - i * 0.000002
        low = high - 0.000005
        close = (high + low) / 2
        raw_klines.append({
            "time": base_time + i * 3600,
            "open": high,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 反弹阶段
    for i in range(30):
        low = 0.00005 + i * 0.000003
        high = low + 0.000005
        close = (high + low) / 2
        raw_klines.append({
            "time": base_time + (20 + i) * 3600,
            "open": low,
            "high": high,
            "low": low,
            "close": close,
            "volume": "1000000"
        })
    
    # 检测交易
    result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
    
    # 打印结果
    print_trade_result(result)
