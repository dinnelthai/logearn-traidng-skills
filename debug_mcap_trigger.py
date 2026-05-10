#!/usr/bin/env python3
"""
调试市值门槛触发时间
"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from backtester.fetch_klines import get_token_info, fetch_klines, normalize_klines
from datetime import datetime, timezone

def debug_mcap_trigger(ca, min_swing_high_mcap=180.0):
    """调试市值门槛触发"""
    
    print(f"=" * 80)
    print(f"调试市值门槛触发时间")
    print(f"=" * 80)
    print(f"CA: {ca}")
    print(f"门槛: {min_swing_high_mcap}k\n")
    
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
    
    # 找到第一次市值 >= 门槛的K线
    print("=" * 80)
    print("扫描K线，查找第一次市值 >= 180k 的时间点")
    print("=" * 80)
    
    trigger_index = None
    for i, k in enumerate(klines):
        mcap_k = 0
        if 'market_cap' in k and k['market_cap'] > 0:
            mcap_k = k['market_cap']
        else:
            # 如果没有market_cap字段，用收盘价 * supply 计算（与 closeU 一致）
            mcap_k = (k['close'] * supply) / 1000
        
        # 显示前10根和触发点附近的K线
        if i < 10 or (trigger_index is None and mcap_k >= min_swing_high_mcap - 50):
            time_str = datetime.fromtimestamp(k['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"K线 {i:4d}: {time_str} UTC | 市值: {mcap_k:8.2f}k | 价格: {k['close']:.8f}")
        
        if mcap_k >= min_swing_high_mcap and trigger_index is None:
            trigger_index = i
            time_str = datetime.fromtimestamp(k['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{'='*80}")
            print(f"✅ 找到触发点！")
            print(f"{'='*80}")
            print(f"索引: {trigger_index}")
            print(f"时间: {time_str} UTC")
            print(f"市值: {mcap_k:.2f}k")
            print(f"价格: {k['close']:.8f}")
            print(f"{'='*80}\n")
            
            # 显示触发点后的几根K线
            print("触发点后的K线:")
            for j in range(i+1, min(i+6, len(klines))):
                k2 = klines[j]
                mcap_k2 = k2.get('market_cap', 0)
                if mcap_k2 == 0:
                    mcap_k2 = (k2['close'] * supply) / 1000
                time_str2 = datetime.fromtimestamp(k2['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                print(f"K线 {j:4d}: {time_str2} UTC | 市值: {mcap_k2:8.2f}k | 价格: {k2['close']:.8f}")
            break
    
    if trigger_index is None:
        print(f"\n❌ 未找到市值 >= {min_swing_high_mcap}k 的K线")
        print(f"\n最高市值:")
        max_mcap = 0
        max_index = 0
        for i, k in enumerate(klines):
            mcap_k = k.get('market_cap', 0)
            if mcap_k == 0:
                mcap_k = (k['close'] * supply) / 1000
            if mcap_k > max_mcap:
                max_mcap = mcap_k
                max_index = i
        
        time_str = datetime.fromtimestamp(klines[max_index]['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print(f"索引: {max_index}")
        print(f"时间: {time_str} UTC")
        print(f"市值: {max_mcap:.2f}k")
        print(f"价格: {klines[max_index]['close']:.8f}")
    
    # 显示 Trade #3 的时间点
    print(f"\n{'='*80}")
    print("Trade #3 的时间点")
    print(f"{'='*80}")
    
    # Trade #3: 2026-05-08 23:55 北京 = 2026-05-08 15:55 UTC
    trade3_utc = datetime(2026, 5, 8, 15, 55, 0, tzinfo=timezone.utc)
    trade3_timestamp = int(trade3_utc.timestamp())
    
    print(f"Trade #3 买入时间: 2026-05-08 23:55 北京 (15:55 UTC)")
    print(f"时间戳: {trade3_timestamp}\n")
    
    # 找到最接近的K线
    closest_index = None
    min_diff = float('inf')
    for i, k in enumerate(klines):
        diff = abs(k['time'] - trade3_timestamp)
        if diff < min_diff:
            min_diff = diff
            closest_index = i
    
    if closest_index is not None:
        k = klines[closest_index]
        mcap_k = k.get('market_cap', 0)
        if mcap_k == 0:
            mcap_k = (k['close'] * supply) / 1000
        time_str = datetime.fromtimestamp(k['time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"最接近的K线:")
        print(f"索引: {closest_index}")
        print(f"时间: {time_str} UTC")
        print(f"市值: {mcap_k:.2f}k")
        print(f"价格: {k['close']:.8f}")
        print(f"时间差: {min_diff}秒 ({min_diff/60:.1f}分钟)")
        
        if trigger_index is not None:
            print(f"\n相对于触发点:")
            print(f"触发点索引: {trigger_index}")
            print(f"Trade #3 索引: {closest_index}")
            if closest_index >= trigger_index:
                print(f"✅ Trade #3 在触发点之后 (索引差: {closest_index - trigger_index})")
            else:
                print(f"❌ Trade #3 在触发点之前 (索引差: {trigger_index - closest_index})")


if __name__ == '__main__':
    ca = sys.argv[1] if len(sys.argv) > 1 else 'HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump'
    min_mcap = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    
    debug_mcap_trigger(ca, min_mcap)
