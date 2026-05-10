# 交易胜率分析器使用说明

**功能**: 统计每个币第1次、第2次、第3次...交易的胜率  
**状态**: ✅ 已实现

---

## 📋 功能说明

### 核心功能
分析多个币的交易数据，统计：
- **第1次交易胜率**：所有币的第1次交易中，盈利的比例
- **第2次交易胜率**：所有币的第2次交易中，盈利的比例  
- **第3次交易胜率**：所有币的第3次交易中，盈利的比例
- ...以此类推

### 使用场景
1. **策略优化**：判断是否应该对同一个币进行多次交易
2. **风险控制**：如果第2次、第3次胜率低，避免重复交易
3. **数据分析**：了解交易策略在不同交易次数下的表现

---

## 🔧 核心函数

### 1. `analyze_token_trades()`
分析单个币的多次交易

```python
from trading.win_rate_analyzer import analyze_token_trades

result = analyze_token_trades(
    ca="token_address",
    raw_klines=klines_data,  # 原始K线数据
    symbol="TOKEN",
    total_capital=2.0,
    min_market_cap=180.0,  # 可选：市值过滤
    max_trades=5  # 最多分析5次交易
)

# 返回结果
{
    "ca": "token_address",
    "symbol": "TOKEN",
    "total_klines": 1000,
    "trades": [
        {
            "trade_number": 1,
            "matched": True,
            "profit_sol": 0.036,
            "profit_rate": 0.60,  # 60%
            "is_win": True,
            "buy_time": 1000000,
            "sell_time": 1005000,
            "market_cap_at_buy": 133.0,
            "market_cap_at_sell": 178.5,
            "buy_count": 1,
            "sell_count": 2
        },
        # ... 更多交易
    ]
}
```

### 2. `calculate_win_rate_stats()`
统计所有币的胜率

```python
from trading.win_rate_analyzer import calculate_win_rate_stats

# 分析多个币
all_trades = []
for token in tokens:
    result = analyze_token_trades(token['ca'], token['klines'])
    all_trades.append(result)

# 统计胜率
stats = calculate_win_rate_stats(
    all_trades,
    min_sample_size=5  # 最小样本量
)

# 返回结果
{
    "total_tokens": 100,
    "total_trades": 165,
    "stats_by_trade_number": {
        1: {
            "total_trades": 100,
            "wins": 65,
            "losses": 35,
            "win_rate": 0.65,  # 65%
            "avg_profit_rate": 0.45,
            "avg_win_profit": 0.80,
            "avg_loss_profit": -0.30,
            "total_profit_sol": 12.5
        },
        2: {
            "total_trades": 50,
            "wins": 20,
            "win_rate": 0.40,  # 40%
            ...
        }
    },
    "summary": {
        "best_trade_number": 1,
        "worst_trade_number": 3,
        "recommendation": "建议只进行第1次交易..."
    }
}
```

### 3. `print_win_rate_report()`
打印胜率报告

```python
from trading.win_rate_analyzer import print_win_rate_report

print_win_rate_report(stats)
```

输出示例：
```
============================================================
📊 交易胜率统计报告
============================================================

总分析币数: 100
总交易数: 165

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第1次交易:
  总交易数: 100
  盈利次数: 65 (65.0%)
  亏损次数: 35 (35.0%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  胜率: 65.0% █████████████
  平均收益率: 🟢 +45.0%
  平均盈利: 🟢 +80.0%
  平均亏损: 🔴 -30.0%
  总利润: 🟢 +12.5000 SOL

第2次交易:
  总交易数: 50
  盈利次数: 20 (40.0%)
  亏损次数: 30 (60.0%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  胜率: 40.0% ████████
  平均收益率: 🔴 -10.0%
  平均盈利: 🟢 +60.0%
  平均亏损: 🔴 -40.0%
  总利润: 🔴 -2.5000 SOL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 建议:
  ✅ 第1次交易表现最佳 (胜率 65.0%)
  ⚠️  第2次交易胜率较低 (40.0%)
  
  建议只进行第1次交易（胜率 65.0%），避免重复交易

============================================================
```

---

## 📖 使用示例

### 示例1：分析单个币

```python
from trading.win_rate_analyzer import analyze_token_trades, print_token_trades_summary

# 获取K线数据（需要足够长的历史数据，建议30-90天）
raw_klines = get_klines("token_address", days=90)

# 分析交易
result = analyze_token_trades(
    ca="token_address",
    raw_klines=raw_klines,
    symbol="TOKEN",
    total_capital=2.0,
    max_trades=5
)

# 打印结果
print_token_trades_summary(result)
```

### 示例2：批量分析多个币

```python
from trading.win_rate_analyzer import (
    analyze_token_trades,
    calculate_win_rate_stats,
    print_win_rate_report
)

# 准备币列表
tokens = [
    {"ca": "addr1", "symbol": "TOKEN1"},
    {"ca": "addr2", "symbol": "TOKEN2"},
    # ... 更多币
]

# 分析所有币
all_trades = []
for token in tokens:
    raw_klines = get_klines(token['ca'], days=90)
    result = analyze_token_trades(
        ca=token['ca'],
        raw_klines=raw_klines,
        symbol=token['symbol'],
        total_capital=2.0,
        max_trades=3
    )
    all_trades.append(result)

# 统计胜率
stats = calculate_win_rate_stats(all_trades)

# 打印报告
print_win_rate_report(stats)
```

### 示例3：使用市值过滤

```python
# 只分析市值达到180k后的交易
result = analyze_token_trades(
    ca="token_address",
    raw_klines=raw_klines,
    min_market_cap=180.0  # 180k过滤
)
```

---

## 🔍 工作原理

### 交易分割逻辑

**基于卖出点分割**：
1. 运行第1次回测，找到卖出点
2. 从卖出点后10根K线开始第2次回测
3. 重复直到没有更多交易或达到max_trades

```python
# 示例：180根K线，3次交易
K线 0-60:   第1次交易（买入#20，卖出#55）
K线 65-120: 第2次交易（买入#80，卖出#115）
K线 125-180: 第3次交易（买入#140，卖出#175）
```

### 胜率计算

```python
# 第1次交易统计
总交易数 = 100个币都有第1次交易 = 100
盈利次数 = 65个币第1次交易盈利 = 65
胜率 = 65 / 100 = 65%

# 第2次交易统计
总交易数 = 只有50个币有第2次交易 = 50
盈利次数 = 20个币第2次交易盈利 = 20
胜率 = 20 / 50 = 40%
```

---

## ⚠️ 注意事项

### 1. 数据要求
- **K线数量**：建议至少30-90天的数据
- **市值数据**：如果使用市值过滤，需要K线包含`market_cap`字段
- **数据质量**：确保K线数据完整、准确

### 2. 样本量
- 默认最小样本量为5
- 样本量太小时统计结果不可靠
- 建议至少分析20-50个币

### 3. 交易识别
- 两次交易之间至少间隔10根K线
- 未完成的交易不计入统计
- 过滤掉异常数据（如收益率过高/过低）

### 4. 性能
- 批量分析时可能需要较长时间
- 建议使用进度条显示进度
- 可以考虑并行处理

---

## 📊 实际应用

### 场景1：验证策略
```python
# 分析100个币，验证策略是否适合重复交易
stats = calculate_win_rate_stats(all_trades)

if stats['stats_by_trade_number'][1]['win_rate'] > 0.6:
    print("✅ 第1次交易胜率高，策略有效")
    
if stats['stats_by_trade_number'].get(2, {}).get('win_rate', 0) < 0.4:
    print("⚠️  第2次交易胜率低，避免重复交易")
```

### 场景2：优化参数
```python
# 对比不同市值阈值的效果
for min_mcap in [100, 150, 180, 200]:
    all_trades = []
    for token in tokens:
        result = analyze_token_trades(
            token['ca'], 
            token['klines'],
            min_market_cap=min_mcap
        )
        all_trades.append(result)
    
    stats = calculate_win_rate_stats(all_trades)
    print(f"市值阈值 {min_mcap}k: 胜率 {stats['stats_by_trade_number'][1]['win_rate']*100:.1f}%")
```

### 场景3：风险控制
```python
# 根据胜率设置交易规则
stats = calculate_win_rate_stats(all_trades)

# 只进行胜率 > 50% 的交易
for trade_num, stat in stats['stats_by_trade_number'].items():
    if stat['win_rate'] > 0.5:
        print(f"✅ 允许第{trade_num}次交易（胜率 {stat['win_rate']*100:.1f}%）")
    else:
        print(f"❌ 禁止第{trade_num}次交易（胜率 {stat['win_rate']*100:.1f}%）")
```

---

## 📁 文件说明

**核心文件**：
- `trading/win_rate_analyzer.py` - 胜率分析器实现
- `example_win_rate_analysis.py` - 使用示例

**相关文件**：
- `trading/trade_checker.py` - 交易检测器（被调用）
- `WIN_RATE_STATS_DESIGN.md` - 设计文档
- `WIN_RATE_ANALYZER_README.md` - 本文件

---

## ✅ 功能清单

- ✅ 分析单个币的多次交易
- ✅ 统计多个币的胜率
- ✅ 按交易次数分组统计
- ✅ 计算平均收益率
- ✅ 生成建议
- ✅ 打印格式化报告
- ✅ 支持市值过滤
- ✅ 记录市值信息

---

## 🚀 快速开始

```python
# 1. 导入模块
from trading.win_rate_analyzer import (
    analyze_token_trades,
    calculate_win_rate_stats,
    print_win_rate_report
)

# 2. 准备数据
tokens = [...]  # 你的币列表
all_trades = []

# 3. 分析每个币
for token in tokens:
    klines = get_klines(token['ca'])  # 获取K线数据
    result = analyze_token_trades(token['ca'], klines)
    all_trades.append(result)

# 4. 统计胜率
stats = calculate_win_rate_stats(all_trades)

# 5. 查看报告
print_win_rate_report(stats)
```

---

**功能已实现，可以开始使用！** 🎉

详细设计请查看：`WIN_RATE_STATS_DESIGN.md`
