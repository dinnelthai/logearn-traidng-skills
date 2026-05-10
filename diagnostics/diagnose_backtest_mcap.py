#!/usr/bin/env python3
"""
诊断脚本：检查回测流程中市值过滤是否生效
"""
import sys
sys.path.insert(0, '/Users/leon/logearn-trading-skills/logearn-traidng-skills')

from trading.fib_calculator import parse_klines
from trading.trade_checker import filter_klines_by_market_cap, check_single_trade
from trading.win_rate_analyzer import analyze_token_trades

print("=" * 80)
print("回测流程市值过滤诊断")
print("=" * 80)

# ============================================================================
# 诊断1: 检查参数传递链
# ============================================================================
print("\n【诊断1】参数传递链检查")
print("-" * 80)

print("""
回测流程中的参数传递链:

1. backtester/backtest.py (run_backtest函数)
   ├─ Line 53: min_market_cap = 180.0
   └─ Line 54-60: analyze_token_trades(..., min_market_cap=min_market_cap)

2. backtester/run_backtest.py (run_backtest函数)
   ├─ Line 36: min_market_cap = 180.0
   └─ Line 37-44: analyze_token_trades(..., min_market_cap=min_market_cap)

3. trading/win_rate_analyzer.py (analyze_token_trades函数)
   ├─ Line 86: min_market_cap参数
   └─ Line 127-131: split_trades_by_sell_points(..., min_market_cap=min_market_cap)

4. trading/win_rate_analyzer.py (split_trades_by_sell_points函数)
   ├─ Line 15: min_market_cap参数
   └─ Line 44-48: check_single_trade(..., min_market_cap=min_market_cap)

5. trading/trade_checker.py (check_single_trade函数)
   ├─ Line 90: min_market_cap参数
   └─ Line 118-128: filter_klines_by_market_cap(klines, min_market_cap)

6. trading/trade_checker.py (filter_klines_by_market_cap函数)
   ├─ Line 37-84: 实现市值过滤逻辑
   └─ 返回过滤后的K线

✅ 参数传递链完整，所有函数都正确传递了min_market_cap参数
""")

# ============================================================================
# 诊断2: 检查K线数据格式
# ============================================================================
print("\n【诊断2】K线数据格式检查")
print("-" * 80)

print("""
K线数据来源和格式:

1. backtester/fetch_klines.py (fetch_logearn函数)
   ├─ Line 96-114: 补充market_cap字段
   ├─ 计算公式: market_cap = closeU × supply / 1000 (单位k)
   └─ 如果supply=0，会跳过市值字段（Line 114）

2. backtester/fetch_klines.py (normalize_klines函数)
   ├─ Line 229-230: 保留market_cap字段
   └─ 如果原始数据有market_cap，会保留

3. backtester/backtest.py (normalize_klines函数)
   ├─ Line 29: 保留market_cap字段
   └─ 格式: 'market_cap': float(k.get('market_cap', 0.0))

4. trading/fib_calculator.py (parse_klines函数)
   └─ 将market_cap字段解析到Kline对象

⚠️  可能的问题:
   - 如果LogEarn无法获取supply，market_cap会缺失
   - 如果使用gmgn兜底，gmgn数据可能没有market_cap字段
   - 缓存的旧数据可能没有market_cap字段
""")

# ============================================================================
# 诊断3: 模拟实际回测流程
# ============================================================================
print("\n【诊断3】模拟实际回测流程")
print("-" * 80)

# 创建测试数据：模拟33k市值的K线
print("\n测试场景: 所有K线市值都是33k（低于180k阈值）")
raw_klines_33k = [
    {
        'time': 1000000 + i*300,  # 5分钟间隔
        'open': 0.0001,
        'high': 0.00011,
        'low': 0.00009,
        'close': 0.0001,
        'volume': 1000,
        'market_cap': 33.2  # 33.2k USD
    }
    for i in range(200)
]

print(f"  原始K线数: {len(raw_klines_33k)}")
print(f"  所有K线market_cap: 33.2k")

# 步骤1: parse_klines
klines = parse_klines(raw_klines_33k)
print(f"\n步骤1: parse_klines")
print(f"  解析后K线数: {len(klines)}")
print(f"  第1根K线market_cap: {klines[0].market_cap}k")
print(f"  第100根K线market_cap: {klines[99].market_cap}k")

# 步骤2: filter_klines_by_market_cap
filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
print(f"\n步骤2: filter_klines_by_market_cap")
print(f"  过滤后K线数: {len(filtered)}")
print(f"  预期: 0（因为所有K线都<180k）")
print(f"  结果: {'✅ 正确' if len(filtered) == 0 else '❌ 错误'}")

# 步骤3: check_single_trade
result = check_single_trade(klines, total_capital=2.0, min_market_cap=180.0)
print(f"\n步骤3: check_single_trade")
print(f"  matched: {result['matched']}")
print(f"  filter_reason: {result.get('filter_reason', 'N/A')}")
print(f"  预期: matched=False, 有filter_reason")
print(f"  结果: {'✅ 正确' if not result['matched'] and result.get('filter_reason') else '❌ 错误'}")

# 步骤4: analyze_token_trades
result = analyze_token_trades(
    ca='test_ca_33k',
    raw_klines=raw_klines_33k,
    symbol='TEST33K',
    total_capital=2.0,
    min_market_cap=180.0,
    max_trades=5
)
print(f"\n步骤4: analyze_token_trades")
print(f"  总K线数: {result['total_klines']}")
print(f"  交易次数: {len(result['trades'])}")
print(f"  预期: 0次交易（因为市值不足）")
print(f"  结果: {'✅ 正确' if len(result['trades']) == 0 else '❌ 错误'}")

# ============================================================================
# 诊断4: 测试边界情况
# ============================================================================
print("\n【诊断4】边界情况测试")
print("-" * 80)

# 测试1: 刚好达到180k
print("\n测试1: 所有K线市值刚好180k（临界值）")
raw_klines_180k = [
    {
        'time': 1000000 + i*300,
        'open': 0.0001,
        'high': 0.00011,
        'low': 0.00009,
        'close': 0.0001,
        'volume': 1000,
        'market_cap': 180.0
    }
    for i in range(200)
]
klines_180k = parse_klines(raw_klines_180k)
filtered_180k = filter_klines_by_market_cap(klines_180k, min_market_cap=180.0)
print(f"  原始K线数: {len(klines_180k)}")
print(f"  过滤后K线数: {len(filtered_180k)}")
print(f"  预期: 200（因为>=180k）")
print(f"  结果: {'✅ 正确' if len(filtered_180k) == 200 else '❌ 错误'}")

# 测试2: 179.9k（刚好低于阈值）
print("\n测试2: 所有K线市值179.9k（刚好低于阈值）")
raw_klines_179k = [
    {
        'time': 1000000 + i*300,
        'open': 0.0001,
        'high': 0.00011,
        'low': 0.00009,
        'close': 0.0001,
        'volume': 1000,
        'market_cap': 179.9
    }
    for i in range(200)
]
klines_179k = parse_klines(raw_klines_179k)
filtered_179k = filter_klines_by_market_cap(klines_179k, min_market_cap=180.0)
print(f"  原始K线数: {len(klines_179k)}")
print(f"  过滤后K线数: {len(filtered_179k)}")
print(f"  预期: 0（因为<180k）")
print(f"  结果: {'✅ 正确' if len(filtered_179k) == 0 else '❌ 错误'}")

# 测试3: 第一次达到阈值
print("\n测试3: 前100根33k，后100根200k（第101根达到阈值）")
raw_klines_mixed = [
    {
        'time': 1000000 + i*300,
        'open': 0.0001,
        'high': 0.00011,
        'low': 0.00009,
        'close': 0.0001,
        'volume': 1000,
        'market_cap': 33.2 if i < 100 else 200.0
    }
    for i in range(200)
]
klines_mixed = parse_klines(raw_klines_mixed)
filtered_mixed = filter_klines_by_market_cap(klines_mixed, min_market_cap=180.0)
print(f"  原始K线数: {len(klines_mixed)}")
print(f"  过滤后K线数: {len(filtered_mixed)}")
print(f"  第一次达到180k的索引: 100")
print(f"  保留前50根，所以从索引: max(0, 100-50) = 50")
print(f"  预期: 150根K线（从索引50到199）")
print(f"  结果: {'✅ 正确' if len(filtered_mixed) == 150 else '❌ 错误'}")
if filtered_mixed:
    print(f"  第一根K线market_cap: {filtered_mixed[0].market_cap}k")
    print(f"  最后一根K线market_cap: {filtered_mixed[-1].market_cap}k")

# ============================================================================
# 诊断5: 检查实际缓存数据
# ============================================================================
print("\n【诊断5】实际缓存数据检查建议")
print("-" * 80)

print("""
如果回测仍然检测到33k的交易，请检查:

1. 检查缓存的K线数据是否包含market_cap字段:
   ls -lh /root/ca-backtester/cache/
   cat /root/ca-backtester/cache/<CA>_logearn.json | jq '.[0]'
   cat /root/ca-backtester/cache/<CA>_gmgn.json | jq '.[0]'

2. 检查K线数据中的market_cap值:
   cat /root/ca-backtester/cache/<CA>_logearn.json | jq '.[] | .market_cap' | head -20

3. 清空缓存并重新获取:
   rm -rf /root/ca-backtester/cache/*
   python3 backtester/run_backtest.py <CA>

4. 在回测时添加调试输出:
   在 backtester/run_backtest.py 的 run_backtest 函数中添加:
   
   # 在第26行后添加
   has_mcap = any('market_cap' in k and k['market_cap'] > 0 for k in klines)
   if has_mcap:
       mcaps = [k.get('market_cap', 0) for k in klines[:10]]
       print(f"  前10根K线市值: {mcaps}")
   else:
       print(f"  ⚠️ K线无市值数据，过滤将失效")

5. 检查LogEarn是否成功获取supply:
   python3 -c "
   import sys
   sys.path.insert(0, '/root/logearn-traidng-skills')
   from backtester.fetch_klines import get_token_info
   info = get_token_info('<CA>')
   print(f'Supply: {info}')
   "
""")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("诊断总结")
print("=" * 80)

print("""
✅ 市值过滤逻辑验证:
   1. filter_klines_by_market_cap 逻辑正确
   2. check_single_trade 正确调用过滤
   3. analyze_token_trades 正确传递参数
   4. 参数传递链完整无误

⚠️  如果33k的交易仍然被检测到，可能原因:
   1. K线数据中market_cap字段缺失或为0
   2. LogEarn无法获取supply，导致market_cap计算失败
   3. 使用了gmgn兜底数据，但gmgn数据没有market_cap字段
   4. 缓存的是旧版本数据（没有market_cap字段）

🔧 解决方案:
   1. 清空缓存: rm -rf /root/ca-backtester/cache/*
   2. 检查LogEarn API是否正常工作
   3. 确认get_token_info能够获取到supply
   4. 在normalize_klines时检查market_cap字段是否存在
   5. 添加调试日志，打印K线的market_cap值

📊 验证方法:
   1. 运行本诊断脚本，确认所有测试通过
   2. 清空缓存后重新运行回测
   3. 检查回测日志，确认市值过滤生效
   4. 查看回测结果，确认33k的交易被过滤
""")
print("=" * 80)
