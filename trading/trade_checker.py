#!/usr/bin/env python3
"""
交易检测器 - 检测K线是否符合一次完整交易
100% 复用核心交易逻辑，不重新实现任何判断
"""

from typing import List, Dict, Optional
from .fib_calculator import Kline, parse_klines, fib_signal
from .position_manager import PositionManager
from .config import DEFAULT_CONFIG


def _format_market_cap(market_cap: float) -> str:
    """
    格式化市值显示（K/M格式）
    
    Args:
        market_cap: 市值（单位：k，即千美元）
    
    Returns:
        str: 格式化的市值字符串
        
    示例:
        45.4 -> "$45.4K"
        251.5 -> "$251.5K"
        1500.0 -> "$1.5M"
        2500.0 -> "$2.5M"
    """
    if market_cap >= 1000:
        # >= 1000k = >= 1M
        return f"${market_cap/1000:.1f}M"
    else:
        # < 1000k
        return f"${market_cap:.1f}K"


def filter_klines_by_market_cap(
    klines: List[Kline],
    min_market_cap: float = 180.0,
    require_first_touch: bool = True
) -> List[Kline]:
    """
    根据市值过滤K线数据
    
    Args:
        klines: K线数据列表
        min_market_cap: 最小市值阈值（单位：k，即千美元）
        require_first_touch: 是否要求"第一次"达到阈值（当前固定为True）
    
    Returns:
        List[Kline]: 过滤后的K线数据
        
    逻辑：
        1. 找到第一次市值 >= min_market_cap 的K线索引
        2. 从该索引开始返回所有后续K线
        3. 如果从未达到阈值，返回空列表
    
    示例：
        klines = [
            Kline(..., market_cap=150.0),  # 不包含
            Kline(..., market_cap=185.0),  # 第一次达到180k，从这里开始
            Kline(..., market_cap=120.0),  # 回调，仍然包含
            Kline(..., market_cap=200.0),  # 包含
        ]
        filtered = filter_klines_by_market_cap(klines, 180.0)
        # 返回最后3根K线
    """
    if not klines:
        return []
    
    # 找到第一次达到阈值的索引
    first_touch_index = None
    for i, kline in enumerate(klines):
        if kline.market_cap >= min_market_cap:
            first_touch_index = i
            break
    
    # 如果从未达到阈值，返回空列表
    if first_touch_index is None:
        return []
    
    # 从第一次达到阈值开始返回，保留前面50根（fib需要看到完整swing high）
    start = max(0, first_touch_index - 50)
    return klines[start:]


def check_single_trade(klines: List[Kline], 
                       total_capital: float = 2.0,
                       config = None,
                       min_market_cap: float = None) -> Dict:
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
        min_market_cap: 最小市值阈值（单位：k），None表示不过滤
    
    Returns:
        Dict: {
            "matched": True/False,  # 是否匹配到完整交易
            "buy_points": [...],    # 买入点列表
            "sell_points": [{...}], # 卖出点列表（支持多次卖出）
            "profit": {...},        # 利润信息
            "filter_reason": str    # 过滤原因（仅当被过滤时）
        }
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # 市值过滤
    if min_market_cap is not None:
        original_count = len(klines)
        klines = filter_klines_by_market_cap(klines, min_market_cap)
        if not klines:
            return {
                "matched": False,
                "buy_points": [],
                "sell_points": [],
                "profit": None,
                "filter_reason": f"市值未达到{min_market_cap}k（共{original_count}根K线）"
            }
    
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
    sell_records = []  # 支持多次卖出（Fib分批卖出）
    total_sell_percentage = 0.0  # 累计卖出比例
    
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
                "timestamp": klines[i].time,
                "market_cap": klines[i].market_cap  # 记录买入时的市值
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
            sell_records.append({
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": signal.get("ao_reason", "AO卖出信号"),
                "type": "ao_sell",
                "percentage": 1.0,  # AO卖出全部
                "market_cap": klines[i].market_cap  # 记录卖出时的市值
            })
            total_sell_percentage = 1.0
            break  # 一次交易结束
        
        # 止损信号
        elif action == "stop":
            sell_records.append({
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": "触发止损",
                "type": "stop_loss",
                "percentage": 1.0,  # 止损全部卖出
                "market_cap": klines[i].market_cap  # 记录卖出时的市值
            })
            total_sell_percentage = 1.0
            break  # 一次交易结束
        
        # Fib 卖出信号
        elif action == "fib_sell":
            percentage = signal.get("percentage", 0.3)
            tier = signal.get("tier", "")
            
            # 记录 Fib 卖出
            sell_records.append({
                "price": signal.get("price"),
                "kline_index": i,
                "timestamp": klines[i].time,
                "reason": signal.get("reason", "Fib卖出信号"),
                "type": "fib_sell",
                "percentage": percentage,
                "tier": tier,
                "market_cap": klines[i].market_cap  # 记录卖出时的市值
            })
            
            # 标记已卖出档位
            fib_sold_tiers.append(tier)
            
            # 累计卖出比例
            total_sell_percentage += percentage
            
            # 如果累计卖出 >= 100%，结束交易
            if total_sell_percentage >= 1.0:
                break
            # 否则继续（可能还有后续卖出）
    
    # 计算利润
    if buy_records and sell_records:
        profit = _calculate_profit_multi_sell(
            entry_prices, 
            entry_amounts, 
            tiers_bought, 
            sell_records
        )
        
        return {
            "matched": True,
            "buy_points": buy_records,
            "sell_points": sell_records,  # 改为复数
            "profit": profit
        }
    else:
        return {
            "matched": False,
            "buy_points": buy_records,
            "sell_points": [],  # 改为空列表
            "profit": None
        }


def _calculate_profit(entry_prices: Dict[str, float],
                     entry_amounts: Dict[str, float],
                     tiers_bought: List[str],
                     sell_price: float,
                     sell_percentage: float = 1.0) -> Dict:
    """
    计算利润（单次卖出）
    
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
        if entry_prices.get(tier, 0) > 0
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


def _calculate_profit_multi_sell(entry_prices: Dict[str, float],
                                  entry_amounts: Dict[str, float],
                                  tiers_bought: List[str],
                                  sell_records: List[Dict]) -> Dict:
    """
    计算利润（支持多次分批卖出）
    
    Args:
        entry_prices: 各档位买入价格
        entry_amounts: 各档位买入金额
        tiers_bought: 已买入档位
        sell_records: 卖出记录列表，每条记录包含 price 和 percentage
    
    Returns:
        Dict: 利润信息
    """
    # 计算总投入
    total_invested = sum(entry_amounts[tier] for tier in tiers_bought)
    
    # 计算总持仓 tokens
    total_tokens = sum(
        entry_amounts[tier] / entry_prices[tier]
        for tier in tiers_bought
        if entry_prices.get(tier, 0) > 0
    )
    
    # 计算所有卖出的总回报
    total_returned = 0.0
    total_sell_percentage = 0.0
    
    for sell in sell_records:
        sell_price = sell.get("price", 0)
        sell_percentage = sell.get("percentage", 0)
        
        # 计算本次卖出的 tokens 和回报
        tokens_sold = total_tokens * sell_percentage
        returned = tokens_sold * sell_price
        total_returned += returned
        total_sell_percentage += sell_percentage
    
    # 计算利润（基于已卖出部分）
    # 投入成本按卖出比例分摊
    invested_for_sold = total_invested * total_sell_percentage
    profit_sol = total_returned - invested_for_sold
    profit_rate = profit_sol / invested_for_sold if invested_for_sold > 0 else 0.0
    
    return {
        "invested": total_invested,  # 总投入
        "invested_for_sold": invested_for_sold,  # 已卖出部分的投入
        "returned": total_returned,  # 总回报
        "profit_sol": profit_sol,  # 利润
        "profit_rate": profit_rate,  # 收益率
        "sell_percentage": total_sell_percentage  # 总卖出比例
    }


def check_single_trade_from_raw(raw_klines: List[dict],
                                total_capital: float = 2.0,
                                config = None,
                                min_market_cap: float = None) -> Dict:
    """
    从原始K线数据检测交易
    
    Args:
        raw_klines: 原始K线数据（可包含market_cap字段）
        total_capital: 总资金
        config: 交易配置
        min_market_cap: 最小市值阈值（单位：k），None表示不过滤
    
    Returns:
        Dict: 检测结果
    """
    klines = parse_klines(raw_klines)
    return check_single_trade(klines, total_capital, config, min_market_cap)


def print_trade_result(result: Dict):
    """
    打印交易检测结果
    
    Args:
        result: check_single_trade() 返回的结果
    """
    if not result["matched"]:
        print("❌ 未匹配到完整交易")
        if result.get("filter_reason"):
            print(f"   过滤原因: {result['filter_reason']}")
        elif result.get("buy_points"):
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
        # 显示市值（如果有）
        if buy.get('market_cap') and buy['market_cap'] > 0:
            mcap_str = _format_market_cap(buy['market_cap'])
            print(f"     市值: {mcap_str}")
    
    print()
    
    # 卖出点（支持多次卖出）
    sell_points = result.get("sell_points", [])
    if sell_points:
        print("📈 卖出点:")
        for i, sell in enumerate(sell_points, 1):
            print(f"  {i}. {sell['type']}")
            print(f"     价格: {sell['price']:.8f}")
            print(f"     比例: {sell.get('percentage', 1.0)*100:.0f}%")
            print(f"     K线: #{sell['kline_index']}")
            print(f"     原因: {sell['reason']}")
            if sell.get('tier'):
                print(f"     档位: {sell['tier']}")
            # 显示市值（如果有）
            if sell.get('market_cap') and sell['market_cap'] > 0:
                mcap_str = _format_market_cap(sell['market_cap'])
                print(f"     市值: {mcap_str}")
    
    print()
    
    # 利润
    profit = result["profit"]
    profit_emoji = "🟢" if profit["profit_rate"] >= 0 else "🔴"
    print("💰 利润:")
    print(f"  总投入: {profit['invested']:.4f} SOL")
    if profit.get('invested_for_sold'):
        print(f"  已卖出部分投入: {profit['invested_for_sold']:.4f} SOL")
    print(f"  回报: {profit['returned']:.4f} SOL")
    print(f"  利润: {profit_emoji} {profit['profit_sol']:+.4f} SOL")
    print(f"  收益率: {profit_emoji} {profit['profit_rate']*100:+.2f}%")
    if profit.get('sell_percentage'):
        print(f"  卖出比例: {profit['sell_percentage']*100:.0f}%")


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
