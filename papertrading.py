#!/usr/bin/env python3
"""
纸上交易（回测）入口
用法: 
  python papertrading.py <CA地址> [市值门槛]           # 单个回测
  python papertrading.py --batch [--db <path>]        # 批量回测
  python papertrading.py --batch --save-db [--html]   # 批量回测+入库+生成报表
"""
import sys
import os
import json
import sqlite3
import subprocess
from typing import Optional, Dict, Any

sys.path.insert(0, '/root/logearn-trading-skills')

from backtester.fetch_klines import get_token_info, fetch_klines, normalize_klines
from trading.win_rate_analyzer import analyze_token_trades

# 数据库和缓存路径
DB = os.getenv('BACKTEST_DB', '/root/ca-backtester/data/backtest.db')
CACHE = os.getenv('BACKTEST_CACHE', '/root/ca-backtester/cache')


def papertrading(ca: str, min_swing_high_mcap: float = 180.0, verbose: bool = True) -> Optional[Dict[str, Any]]:
    """
    纸上交易（回测）单个CA
    
    Args:
        ca: 代币地址
        min_swing_high_mcap: 波峰市值门槛（单位k USD），默认180k
        verbose: 是否显示详细输出
    
    Returns:
        dict: 回测结果，包含 trades, win_rate, symbol, supply 等
    """
    if verbose:
        print(f"=" * 80)
        print(f"纸上交易 (Paper Trading)")
        print(f"=" * 80)
        print(f"CA: {ca}")
        print(f"波峰市值门槛: {min_swing_high_mcap}k USD\n")
    
    # 1. 获取代币信息
    if verbose:
        print("📊 获取代币信息...")
    info = get_token_info(ca)
    if not info:
        if verbose:
            print("❌ 无法获取代币信息")
        return None
    
    supply = info.get('total_supply')
    symbol = info.get('symbol', 'UNKNOWN')
    
    if not supply or supply <= 0:
        if verbose:
            print(f"❌ 无效的supply: {supply}")
        return None
    
    if verbose:
        print(f"   代币: {symbol}")
        print(f"   总量: {supply:,.0f}\n")
    
    # 2. 获取K线数据
    if verbose:
        print("📈 获取K线数据...")
    raw_klines = fetch_klines(ca)
    if not raw_klines:
        if verbose:
            print("❌ 无K线数据")
        return None
    
    klines = normalize_klines(raw_klines)
    if len(klines) < 10:
        if verbose:
            print(f"❌ K线不足({len(klines)}条)")
        return None
    
    if verbose:
        print(f"   K线数量: {len(klines)}\n")
    
    # 3. 运行回测
    if verbose:
        print("🔄 运行回测...\n")
    
    result = analyze_token_trades(
        ca=ca,
        raw_klines=klines,
        symbol=symbol,
        total_capital=2.0,
        supply=supply,
        min_swing_high_mcap=min_swing_high_mcap,
        max_trades=5
    )
    
    # 添加额外信息
    result['ca'] = ca
    result['symbol'] = symbol
    result['supply'] = supply
    result['klines_count'] = len(klines)
    
    # 4. 显示结果
    if verbose:
        print("=" * 80)
        print("📊 回测结果")
        print("=" * 80)
        print(f"总K线数: {result['total_klines']}")
        print(f"交易次数: {len(result['trades'])}")
        
        if result['trades']:
            print(f"胜率: {result.get('win_rate', 0)*100:.1f}%")
            print(f"平均收益: {result.get('avg_profit_rate', 0)*100:+.2f}%")
            print(f"最大收益: {result.get('max_profit_rate', 0)*100:+.2f}%")
            print(f"最小收益: {result.get('min_profit_rate', 0)*100:+.2f}%")
            
            print("\n" + "-" * 80)
            print("交易明细:")
            print("-" * 80)
            
            for trade in result['trades']:
                print(f"\n第{trade['trade_number']}次交易:")
                print(f"  收益率: {trade['profit_rate']*100:+.2f}%")
                print(f"  买入点: {len(trade.get('buy_points', []))}个")
                print(f"  卖出点: {len(trade.get('sell_points', []))}个")
                
                # 显示买入详情
                for bp in trade.get('buy_points', []):
                    print(f"    买入 {bp['tier']}: {bp['price']:.8f}")
                
                # 显示卖出详情
                for sp in trade.get('sell_points', []):
                    print(f"    卖出 {sp['type']}: {sp['price']:.8f} ({sp['percentage']*100:.0f}%)")
        else:
            print("⚠️  未检测到交易")
        
        print("=" * 80)
    
    return result


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: papertrading <CA地址> [市值门槛]")
        print("示例: papertrading ABC123... 180")
        print("       papertrading ABC123... 180k")
        sys.exit(1)
    
    ca = sys.argv[1]
    
    # 解析市值门槛（支持 180 或 180k 格式）
    if len(sys.argv) > 2:
        mcap_str = sys.argv[2].lower()
        if mcap_str.endswith('k'):
            min_mcap = float(mcap_str[:-1])
        else:
            min_mcap = float(mcap_str)
    else:
        min_mcap = 180.0
    
    papertrading(ca, min_mcap)


if __name__ == '__main__':
    main()
