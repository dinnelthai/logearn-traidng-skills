#!/usr/bin/env python3
"""
为回测流程添加调试输出
在 backtester/run_backtest.py 中添加市值检查日志
"""

print("""
建议在 backtester/run_backtest.py 的 run_backtest 函数中添加以下调试代码:

在第26行（has_mcap = any...）后添加:

    # 检查市值字段
    has_mcap = any('market_cap' in k and k['market_cap'] > 0 for k in klines)
    if not has_mcap:
        print(f"  ⚠️ K线无市值数据，跳过市值过滤")
    else:
        # 打印前10根K线的市值
        mcaps = [k.get('market_cap', 0) for k in klines[:10]]
        print(f"  📊 前10根K线市值: {mcaps}")
        
        # 统计市值分布
        all_mcaps = [k.get('market_cap', 0) for k in klines if k.get('market_cap', 0) > 0]
        if all_mcaps:
            min_mcap = min(all_mcaps)
            max_mcap = max(all_mcaps)
            avg_mcap = sum(all_mcaps) / len(all_mcaps)
            print(f"  📊 市值范围: {min_mcap:.1f}k ~ {max_mcap:.1f}k (平均: {avg_mcap:.1f}k)")
            
            # 检查是否有K线达到180k阈值
            above_threshold = sum(1 for m in all_mcaps if m >= 180.0)
            print(f"  📊 达到180k阈值的K线数: {above_threshold}/{len(klines)}")

这样可以在回测时看到:
1. K线是否包含市值数据
2. 市值的分布范围
3. 有多少K线达到了180k阈值

示例输出:
  ✅ 交易0笔 | 胜率0% | 盈亏+0.00%
  📊 前10根K线市值: [33.2, 33.2, 33.2, 33.2, 33.2, 33.2, 33.2, 33.2, 33.2, 33.2]
  📊 市值范围: 33.2k ~ 33.2k (平均: 33.2k)
  📊 达到180k阈值的K线数: 0/200

或者:
  ✅ 交易2笔 | 胜率50% | 盈亏+5.23%
  📊 前10根K线市值: [45.3, 52.1, 89.4, 123.5, 185.2, 201.3, 198.7, 205.4, 210.1, 215.3]
  📊 市值范围: 45.3k ~ 350.2k (平均: 187.5k)
  📊 达到180k阈值的K线数: 150/200
""")

print("\n" + "=" * 80)
print("或者直接运行以下命令来检查某个CA的K线数据:")
print("=" * 80)
print("""
# 检查缓存的K线数据
cat /root/ca-backtester/cache/<CA>_logearn.json | jq '.[0:5] | .[] | {time, market_cap}'

# 统计市值分布
cat /root/ca-backtester/cache/<CA>_logearn.json | jq '.[] | .market_cap' | sort -n | uniq -c

# 检查有多少K线达到180k
cat /root/ca-backtester/cache/<CA>_logearn.json | jq '.[] | select(.market_cap >= 180) | .market_cap' | wc -l

# 检查supply是否正确获取
python3 -c "
import sys
sys.path.insert(0, '/root/logearn-traidng-skills')
from backtester.fetch_klines import get_token_info
info = get_token_info('<CA>')
print(f'Token Info: {info}')
"
""")
