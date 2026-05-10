#!/usr/bin/env python3
"""
验证实际交易点与策略检测结果
"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from backtester.fetch_klines import get_token_info, fetch_klines, normalize_klines
from trading.win_rate_analyzer import analyze_token_trades
from datetime import datetime, timezone

# 实际交易点（北京时间 UTC+8）
ACTUAL_TRADES = [
    {
        'trade_number': 1,
        'buy_time_beijing': '2026-05-09 09:25:00',
        'sell_time_beijing': '2026-05-09 19:55:00',
    },
    {
        'trade_number': 2,
        'buy_time_beijing': '2026-05-09 22:05:00',
        'sell_time_beijing': '2026-05-09 22:45:00',
    },
    {
        'trade_number': 3,
        'buy_time_beijing': '2026-05-08 23:55:00',
        'sell_time_beijing': '2026-05-09 00:05:00',
    },
]

def beijing_to_timestamp(beijing_str):
    """北京时间字符串转时间戳（UTC+8）"""
    from datetime import timedelta
    dt = datetime.strptime(beijing_str, '%Y-%m-%d %H:%M:%S')
    # 北京时间 = UTC+8，所以减去8小时得到UTC
    dt_utc = dt - timedelta(hours=8)
    dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return int(dt_utc.timestamp())

def find_closest_kline(klines, target_time, tolerance=600):
    """
    找到最接近目标时间的K线
    
    Args:
        klines: K线列表
        target_time: 目标时间戳
        tolerance: 容差（秒），默认10分钟
    
    Returns:
        dict: 最接近的K线，或None
    """
    closest = None
    min_diff = float('inf')
    
    for k in klines:
        diff = abs(k['time'] - target_time)
        if diff < min_diff and diff <= tolerance:
            min_diff = diff
            closest = k
    
    return closest, min_diff if closest else None

def verify_trades(ca, min_swing_high_mcap=180.0):
    """验证实际交易点"""
    
    print(f"=" * 80)
    print(f"验证实际交易点")
    print(f"=" * 80)
    print(f"CA: {ca}\n")
    
    # 获取数据
    info = get_token_info(ca)
    if not info:
        print("❌ 无法获取代币信息")
        return
    
    supply = info['total_supply']
    symbol = info['symbol']
    print(f"代币: {symbol}")
    print(f"总量: {supply:,.0f}\n")
    
    raw_klines = fetch_klines(ca)
    klines = normalize_klines(raw_klines, supply)
    print(f"K线数量: {len(klines)}\n")
    
    # 运行策略检测
    print("=" * 80)
    print("运行策略检测...")
    print("=" * 80)
    
    result = analyze_token_trades(
        ca=ca,
        raw_klines=klines,
        symbol=symbol,
        total_capital=2.0,
        supply=supply,
        min_swing_high_mcap=min_swing_high_mcap,
        max_trades=5
    )
    
    detected_trades = result['trades']
    print(f"\n策略检测到 {len(detected_trades)} 次交易\n")
    
    # 对比实际交易点
    print("=" * 80)
    print("对比实际交易点与策略检测结果")
    print("=" * 80)
    
    for actual in ACTUAL_TRADES:
        trade_num = actual['trade_number']
        buy_time = beijing_to_timestamp(actual['buy_time_beijing'])
        sell_time = beijing_to_timestamp(actual['sell_time_beijing'])
        
        print(f"\n【交易 {trade_num}】")
        print(f"实际买入时间: {actual['buy_time_beijing']} 北京 (时间戳: {buy_time})")
        print(f"实际卖出时间: {actual['sell_time_beijing']} 北京 (时间戳: {sell_time})")
        
        # 找到最接近的K线
        buy_kline, buy_diff = find_closest_kline(klines, buy_time)
        sell_kline, sell_diff = find_closest_kline(klines, sell_time)
        
        if buy_kline:
            print(f"\n最接近的买入K线:")
            print(f"  时间: {datetime.fromtimestamp(buy_kline['time'], tz=timezone.utc)}")
            print(f"  价格: {buy_kline['close']:.8f}")
            print(f"  时间差: {buy_diff}秒 ({buy_diff/60:.1f}分钟)")
        else:
            print(f"\n❌ 未找到接近的买入K线")
        
        if sell_kline:
            print(f"\n最接近的卖出K线:")
            print(f"  时间: {datetime.fromtimestamp(sell_kline['time'], tz=timezone.utc)}")
            print(f"  价格: {sell_kline['close']:.8f}")
            print(f"  时间差: {sell_diff}秒 ({sell_diff/60:.1f}分钟)")
        else:
            print(f"\n❌ 未找到接近的卖出K线")
        
        # 检查策略是否检测到这次交易
        matched = False
        for detected in detected_trades:
            if detected['trade_number'] == trade_num:
                matched = True
                print(f"\n✅ 策略检测到此交易:")
                print(f"  收益率: {detected['profit_rate']*100:+.2f}%")
                print(f"  买入点数: {len(detected.get('buy_points', []))}")
                print(f"  卖出点数: {len(detected.get('sell_points', []))}")
                
                # 显示买入点
                for bp in detected.get('buy_points', []):
                    print(f"    买入 {bp['tier']}: {bp['price']:.8f}")
                
                # 显示卖出点
                for sp in detected.get('sell_points', []):
                    print(f"    卖出 {sp['type']}: {sp['price']:.8f}")
                break
        
        if not matched:
            print(f"\n❌ 策略未检测到此交易")
        
        print("-" * 80)
    
    # 显示策略检测到但实际没有的交易
    print(f"\n" + "=" * 80)
    print("策略额外检测到的交易（实际未交易）")
    print("=" * 80)
    
    actual_nums = {t['trade_number'] for t in ACTUAL_TRADES}
    for detected in detected_trades:
        if detected['trade_number'] not in actual_nums:
            print(f"\n交易 {detected['trade_number']}:")
            print(f"  收益率: {detected['profit_rate']*100:+.2f}%")
            print(f"  买入点数: {len(detected.get('buy_points', []))}")
            print(f"  卖出点数: {len(detected.get('sell_points', []))}")


if __name__ == '__main__':
    ca = sys.argv[1] if len(sys.argv) > 1 else 'HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump'
    min_mcap = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    
    verify_trades(ca, min_mcap)
