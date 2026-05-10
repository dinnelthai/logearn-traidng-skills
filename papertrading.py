#!/usr/bin/env python3
"""
纸上交易（回测）入口
用法: python papertrading.py <CA地址> [市值门槛]
"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from backtester.fetch_klines import get_token_info, fetch_klines, normalize_klines
from trading.win_rate_analyzer import analyze_token_trades


def papertrading(ca: str, min_swing_high_mcap: float = 180.0):
    """
    纸上交易（回测）
    
    Args:
        ca: 代币地址
        min_swing_high_mcap: 波峰市值门槛（单位k USD），默认180k
    
    Returns:
        dict: 回测结果
    """
    print(f"=" * 80)
    print(f"纸上交易 (Paper Trading)")
    print(f"=" * 80)
    print(f"CA: {ca}")
    print(f"波峰市值门槛: {min_swing_high_mcap}k USD\n")
    
    # 1. 获取代币信息
    print("📊 获取代币信息...")
    info = get_token_info(ca)
    if not info:
        print("❌ 无法获取代币信息")
        return None
    
    supply = info['total_supply']
    symbol = info['symbol']
    print(f"   代币: {symbol}")
    print(f"   总量: {supply:,.0f}\n")
    
    # 2. 获取K线数据
    print("📈 获取K线数据...")
    raw_klines = fetch_klines(ca)
    klines = normalize_klines(raw_klines, supply)
    print(f"   K线数量: {len(klines)}\n")
    
    # 3. 运行回测
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
    
    # 4. 显示结果
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
        sys.exit(1)
    
    ca = sys.argv[1]
    min_mcap = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    
    papertrading(ca, min_mcap)


if __name__ == '__main__':
    main()
