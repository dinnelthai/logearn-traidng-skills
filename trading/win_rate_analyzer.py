#!/usr/bin/env python3
"""
交易胜率分析器
统计每个币第N次交易的胜率
"""

from typing import List, Dict, Optional
from .fib_calculator import Kline, parse_klines
from .trade_checker import check_single_trade, _format_market_cap


def split_trades_by_sell_points(
    klines: List[Kline],
    total_capital: float = 2.0,
    min_market_cap: float = None,
    max_trades: int = 5
) -> List[Dict]:
    """
    基于卖出点分割多次交易
    
    Args:
        klines: K线数据列表
        total_capital: 总资金
        min_market_cap: 最小市值阈值
        max_trades: 最多分析几次交易
    
    Returns:
        List[Dict]: 每次交易的结果
        [
            {
                "trade_number": 1,
                "klines_used": 50,  # 使用了多少根K线
                "result": {...}  # check_single_trade的结果
            },
            ...
        ]
    """
    trades = []
    remaining_klines = klines
    trade_number = 1
    
    while trade_number <= max_trades and len(remaining_klines) > 0:
        # 运行回测
        result = check_single_trade(
            remaining_klines,
            total_capital=total_capital,
            min_market_cap=min_market_cap
        )
        
        # 如果没有匹配到交易，结束
        if not result["matched"]:
            break
        
        # 记录这次交易
        trades.append({
            "trade_number": trade_number,
            "klines_used": len(remaining_klines),
            "result": result
        })
        
        # 找到最后一个卖出点的K线索引
        sell_points = result.get("sell_points", [])
        if not sell_points:
            break
        
        last_sell_index = max(sell["kline_index"] for sell in sell_points)
        
        # 从卖出点后的K线开始下一次交易
        # 留出至少10根K线的间隔，避免立即重新买入
        next_start_index = last_sell_index + 10
        
        if next_start_index >= len(remaining_klines):
            break
        
        remaining_klines = klines[next_start_index:]
        trade_number += 1
    
    return trades


def analyze_token_trades(
    ca: str,
    raw_klines: List[dict],
    symbol: str = None,
    total_capital: float = 2.0,
    min_market_cap: float = None,
    max_trades: int = 5
) -> Dict:
    """
    分析单个币的多次交易
    
    Args:
        ca: 币地址
        raw_klines: 原始K线数据
        symbol: 币符号
        total_capital: 总资金
        min_market_cap: 最小市值阈值
        max_trades: 最多分析几次交易
    
    Returns:
        {
            "ca": "...",
            "symbol": "...",
            "total_klines": 1000,
            "trades": [
                {
                    "trade_number": 1,
                    "matched": True,
                    "profit_sol": 0.036,
                    "profit_rate": 0.60,
                    "is_win": True,
                    "buy_time": 1000000,
                    "sell_time": 1005000,
                    "market_cap_at_buy": 133.0,
                    "market_cap_at_sell": 178.5,
                    "buy_count": 1,
                    "sell_count": 2
                },
                ...
            ]
        }
    """
    # 解析K线
    klines = parse_klines(raw_klines)
    
    # 分割交易
    trades_raw = split_trades_by_sell_points(
        klines,
        total_capital=total_capital,
        min_market_cap=min_market_cap,
        max_trades=max_trades
    )
    
    # 处理每次交易的数据
    trades = []
    for trade_raw in trades_raw:
        result = trade_raw["result"]
        
        if not result["matched"]:
            continue
        
        # 提取买入和卖出信息
        buy_points = result.get("buy_points", [])
        sell_points = result.get("sell_points", [])
        profit = result.get("profit", {})
        
        # 买入时间和市值
        buy_time = buy_points[0]["timestamp"] if buy_points else None
        buy_market_cap = buy_points[0].get("market_cap", 0) if buy_points else 0
        
        # 卖出时间和市值（取最后一次卖出）
        sell_time = sell_points[-1]["timestamp"] if sell_points else None
        sell_market_cap = sell_points[-1].get("market_cap", 0) if sell_points else 0
        
        # 判断是否盈利
        profit_sol = profit.get("profit_sol", 0)
        profit_rate = profit.get("profit_rate", 0)
        is_win = profit_sol > 0
        
        trades.append({
            "trade_number": trade_raw["trade_number"],
            "matched": True,
            "profit_sol": profit_sol,
            "profit_rate": profit_rate,
            "is_win": is_win,
            "buy_time": buy_time,
            "sell_time": sell_time,
            "market_cap_at_buy": buy_market_cap,
            "market_cap_at_sell": sell_market_cap,
            "buy_count": len(buy_points),
            "sell_count": len(sell_points)
        })
    
    return {
        "ca": ca,
        "symbol": symbol or ca[:8],
        "total_klines": len(klines),
        "trades": trades
    }


def calculate_win_rate_stats(
    tokens_trades: List[Dict],
    min_sample_size: int = 5  # 最小样本量，少于此数量不统计
) -> Dict:
    """
    统计所有币的胜率
    
    Args:
        tokens_trades: 所有币的交易记录列表
        min_sample_size: 最小样本量
    
    Returns:
        {
            "total_tokens": 100,
            "total_trades": 165,
            "stats_by_trade_number": {
                1: {
                    "total_trades": 100,
                    "wins": 65,
                    "losses": 35,
                    "win_rate": 0.65,
                    "avg_profit_rate": 0.45,
                    "avg_win_profit": 0.80,
                    "avg_loss_profit": -0.30,
                    "total_profit_sol": 12.5
                },
                ...
            },
            "summary": {
                "best_trade_number": 1,
                "worst_trade_number": 3,
                "recommendation": "..."
            }
        }
    """
    # 按交易次数分组
    trades_by_number = {}
    
    for token_data in tokens_trades:
        for trade in token_data.get("trades", []):
            trade_number = trade["trade_number"]
            
            if trade_number not in trades_by_number:
                trades_by_number[trade_number] = []
            
            trades_by_number[trade_number].append(trade)
    
    # 统计每个交易次数的数据
    stats_by_trade_number = {}
    
    for trade_number, trades in sorted(trades_by_number.items()):
        total_trades = len(trades)
        
        # 样本量太小，不统计
        if total_trades < min_sample_size:
            continue
        
        wins = sum(1 for t in trades if t["is_win"])
        losses = total_trades - wins
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # 平均收益率
        avg_profit_rate = sum(t["profit_rate"] for t in trades) / total_trades
        
        # 盈利交易的平均收益率
        win_trades = [t for t in trades if t["is_win"]]
        avg_win_profit = sum(t["profit_rate"] for t in win_trades) / len(win_trades) if win_trades else 0
        
        # 亏损交易的平均收益率
        loss_trades = [t for t in trades if not t["is_win"]]
        avg_loss_profit = sum(t["profit_rate"] for t in loss_trades) / len(loss_trades) if loss_trades else 0
        
        # 总利润
        total_profit_sol = sum(t["profit_sol"] for t in trades)
        
        stats_by_trade_number[trade_number] = {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_profit_rate": avg_profit_rate,
            "avg_win_profit": avg_win_profit,
            "avg_loss_profit": avg_loss_profit,
            "total_profit_sol": total_profit_sol
        }
    
    # 生成总结
    summary = {}
    if stats_by_trade_number:
        # 找出胜率最高和最低的交易次数
        best_trade_number = max(stats_by_trade_number.keys(), 
                               key=lambda x: stats_by_trade_number[x]["win_rate"])
        worst_trade_number = min(stats_by_trade_number.keys(), 
                                key=lambda x: stats_by_trade_number[x]["win_rate"])
        
        best_win_rate = stats_by_trade_number[best_trade_number]["win_rate"]
        
        # 生成建议
        if best_trade_number == 1 and best_win_rate > 0.5:
            recommendation = f"建议只进行第1次交易（胜率 {best_win_rate*100:.1f}%），避免重复交易"
        elif best_win_rate < 0.5:
            recommendation = "所有交易次数的胜率都低于50%，建议优化策略"
        else:
            recommendation = f"第{best_trade_number}次交易表现最佳（胜率 {best_win_rate*100:.1f}%）"
        
        summary = {
            "best_trade_number": best_trade_number,
            "worst_trade_number": worst_trade_number,
            "recommendation": recommendation
        }
    
    # 统计总数
    total_tokens = len(tokens_trades)
    total_trades = sum(len(t.get("trades", [])) for t in tokens_trades)
    
    return {
        "total_tokens": total_tokens,
        "total_trades": total_trades,
        "stats_by_trade_number": stats_by_trade_number,
        "summary": summary
    }


def print_win_rate_report(stats: Dict):
    """
    打印胜率统计报告
    
    Args:
        stats: calculate_win_rate_stats() 返回的统计结果
    """
    print()
    print("=" * 60)
    print("📊 交易胜率统计报告")
    print("=" * 60)
    print()
    
    print(f"总分析币数: {stats['total_tokens']}")
    print(f"总交易数: {stats['total_trades']}")
    print()
    
    stats_by_number = stats.get("stats_by_trade_number", {})
    
    if not stats_by_number:
        print("⚠️  没有足够的数据进行统计")
        return
    
    print("━" * 60)
    print()
    
    # 打印每个交易次数的统计
    for trade_number in sorted(stats_by_number.keys()):
        stat = stats_by_number[trade_number]
        
        print(f"第{trade_number}次交易:")
        print(f"  总交易数: {stat['total_trades']}")
        print(f"  盈利次数: {stat['wins']} ({stat['wins']/stat['total_trades']*100:.1f}%)")
        print(f"  亏损次数: {stat['losses']} ({stat['losses']/stat['total_trades']*100:.1f}%)")
        print(f"  ━" * 30)
        
        # 胜率条形图
        win_rate_pct = stat['win_rate'] * 100
        bar_length = int(win_rate_pct / 5)  # 每5%一个字符
        bar = "█" * bar_length
        print(f"  胜率: {win_rate_pct:.1f}% {bar}")
        
        # 收益率
        profit_emoji = "🟢" if stat['avg_profit_rate'] >= 0 else "🔴"
        print(f"  平均收益率: {profit_emoji} {stat['avg_profit_rate']*100:+.1f}%")
        
        if stat['wins'] > 0:
            print(f"  平均盈利: 🟢 {stat['avg_win_profit']*100:+.1f}%")
        if stat['losses'] > 0:
            print(f"  平均亏损: 🔴 {stat['avg_loss_profit']*100:+.1f}%")
        
        profit_sol_emoji = "🟢" if stat['total_profit_sol'] >= 0 else "🔴"
        print(f"  总利润: {profit_sol_emoji} {stat['total_profit_sol']:+.4f} SOL")
        print()
    
    # 打印总结和建议
    summary = stats.get("summary", {})
    if summary:
        print("━" * 60)
        print()
        print("💡 建议:")
        
        best_num = summary.get("best_trade_number")
        worst_num = summary.get("worst_trade_number")
        
        if best_num:
            best_stat = stats_by_number[best_num]
            print(f"  ✅ 第{best_num}次交易表现最佳 (胜率 {best_stat['win_rate']*100:.1f}%)")
        
        # 标记胜率低于50%的交易
        for trade_number, stat in stats_by_number.items():
            if stat['win_rate'] < 0.5 and trade_number != best_num:
                print(f"  ⚠️  第{trade_number}次交易胜率较低 ({stat['win_rate']*100:.1f}%)")
        
        if worst_num and worst_num != best_num:
            worst_stat = stats_by_number[worst_num]
            if worst_stat['win_rate'] < 0.35:
                print(f"  ❌ 避免第{worst_num}次交易 (胜率仅 {worst_stat['win_rate']*100:.1f}%)")
        
        print()
        print(f"  {summary.get('recommendation', '')}")
    
    print()
    print("=" * 60)
    print()


def print_token_trades_summary(token_data: Dict):
    """
    打印单个币的交易总结
    
    Args:
        token_data: analyze_token_trades() 返回的结果
    """
    print()
    print("=" * 60)
    print(f"📈 {token_data['symbol']} 交易分析")
    print("=" * 60)
    print()
    
    print(f"币地址: {token_data['ca']}")
    print(f"总K线数: {token_data['total_klines']}")
    print(f"交易次数: {len(token_data['trades'])}")
    print()
    
    if not token_data['trades']:
        print("⚠️  未检测到任何交易")
        return
    
    for trade in token_data['trades']:
        print(f"第{trade['trade_number']}次交易:")
        
        result_emoji = "✅" if trade['is_win'] else "❌"
        print(f"  结果: {result_emoji} {'盈利' if trade['is_win'] else '亏损'}")
        
        profit_emoji = "🟢" if trade['profit_rate'] >= 0 else "🔴"
        print(f"  收益率: {profit_emoji} {trade['profit_rate']*100:+.2f}%")
        print(f"  利润: {profit_emoji} {trade['profit_sol']:+.4f} SOL")
        
        # 市值信息
        if trade['market_cap_at_buy'] > 0:
            buy_mcap = _format_market_cap(trade['market_cap_at_buy'])
            print(f"  买入市值: {buy_mcap}")
        
        if trade['market_cap_at_sell'] > 0:
            sell_mcap = _format_market_cap(trade['market_cap_at_sell'])
            print(f"  卖出市值: {sell_mcap}")
        
        print(f"  买入次数: {trade['buy_count']}")
        print(f"  卖出次数: {trade['sell_count']}")
        print()
    
    # 总结
    total_profit = sum(t['profit_sol'] for t in token_data['trades'])
    wins = sum(1 for t in token_data['trades'] if t['is_win'])
    win_rate = wins / len(token_data['trades']) if token_data['trades'] else 0
    
    print("━" * 60)
    print("总结:")
    print(f"  总利润: {total_profit:+.4f} SOL")
    print(f"  胜率: {win_rate*100:.1f}% ({wins}/{len(token_data['trades'])})")
    print()
