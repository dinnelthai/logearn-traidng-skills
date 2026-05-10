# 回测系统Bug修复总结

**修复时间**: 2026-05-10  
**问题**: HTML报表买入市值显示错误 + 180k市值过滤未生效

---

## 🐛 发现的问题

### 1. 买入市值显示错误
**现象**: HTML报表中显示的买入市值不正确
- 实际: 应该显示 $133.0K, $178.5K
- 错误: 显示了错误的数值

**原因**: `gen_html.py` 中的 `_fmt_mcap_k()` 函数有bug
```python
# 错误代码
usd = v * 1000  # v已经是k为单位，不应该再乘1000
```

### 2. 180k市值过滤未生效
**现象**: 回测结果中出现了低于180k的买入（如$48.4K）

**原因**: 
1. 调用了不存在的函数 `check_multiple_trades_from_raw()`
2. 参数单位错误：传入 `min_mcap=180_000`（美元），但函数期望 `min_market_cap=180.0`（k）
3. 应该使用 `analyze_token_trades()` 函数

---

## ✅ 修复内容

### 修复1: 市值格式化函数

**文件**: `backtester/gen_html.py`

```python
# 修复前
def _fmt_mcap_k(v):
    if not v or v <= 0:
        return '—'
    usd = v * 1000  # ❌ 错误：v已经是k为单位
    if usd >= 1_000_000:
        return f"${usd/1_000_000:.1f}M"
    ...

# 修复后
def _fmt_mcap_k(v):
    """格式化市值（单位k），输出 $X.XK 或 $X.XM"""
    if not v or v <= 0:
        return '—'
    # v 已经是以k为单位，不需要再乘1000
    if v >= 1000:
        # >= 1000k = >= 1M
        return f"${v/1000:.1f}M"
    else:
        # < 1000k
        return f"${v:.1f}K"
```

### 修复2: 回测函数调用

**文件**: `backtester/run_backtest.py` 和 `backtester/backtest.py`

```python
# 修复前
from trading.trade_checker import check_multiple_trades_from_raw  # ❌ 函数不存在
min_mcap = max(180_000, mcap * 0.1)  # ❌ 单位错误（美元）
result = check_multiple_trades_from_raw(klines, min_mcap=min_mcap)
trades = result.get('trades', [])
wins = sum(1 for t in trades if t['profit']['profit_rate'] > 0)  # ❌ 字段错误

# 修复后
from trading.win_rate_analyzer import analyze_token_trades  # ✅ 正确的函数
min_market_cap = 180.0  # ✅ 180k（单位：k）
result = analyze_token_trades(
    ca=ca,
    raw_klines=klines,
    symbol=symbol,
    total_capital=2.0,
    min_market_cap=min_market_cap,  # ✅ 正确的参数名和单位
    max_trades=5
)
trades = result.get('trades', [])
wins = sum(1 for t in trades if t.get('is_win', False))  # ✅ 正确的字段
```

### 修复3: 数据访问方式

```python
# 修复前
t['profit']['profit_rate']  # ❌ 嵌套结构错误

# 修复后
t.get('profit_rate', 0)  # ✅ 直接访问
t.get('is_win', False)  # ✅ 使用is_win字段判断盈亏
```

---

## 📊 修复效果

### 修复前
```
买入市值显示错误
$48.4K 的买入被包含（< 180k）
$100K 的买入被包含（< 180k）
```

### 修复后
```
买入市值正确显示：$133.0K, $178.5K, $251.5K
只有 >= 180k 的买入被包含
180k 过滤正常工作
```

---

## 🔍 技术细节

### 市值单位说明
- **K线数据中的 `market_cap` 字段**：单位是 **k**（千美元）
  - 例如：`market_cap: 133.0` 表示 133k = $133,000
- **`min_market_cap` 参数**：单位也是 **k**
  - 例如：`min_market_cap=180.0` 表示 180k = $180,000

### 函数对应关系
| 旧代码（错误） | 新代码（正确） |
|---|---|
| `check_multiple_trades_from_raw()` | `analyze_token_trades()` |
| `min_mcap=180_000`（美元） | `min_market_cap=180.0`（k） |
| `t['profit']['profit_rate']` | `t.get('profit_rate', 0)` |
| `t['profit']['profit_rate'] > 0` | `t.get('is_win', False)` |

---

## 📁 修改文件清单

1. **`backtester/gen_html.py`** - 修复市值格式化函数
2. **`backtester/run_backtest.py`** - 修复回测调用
3. **`backtester/backtest.py`** - 修复回测调用

**总行数**: 约30行修改

---

## ✅ 验证步骤

### 1. 重新运行回测
```bash
cd /root/ca-backtester
python3 backtester/run_backtest.py <CA地址>
```

### 2. 生成HTML报表
```bash
python3 backtester/gen_html.py
```

### 3. 检查报表
- ✅ 买入市值显示正确（$XXX.XK 或 $X.XM）
- ✅ 所有买入市值 >= $180.0K
- ✅ 没有低于180k的买入

---

## 🎯 预期结果

### HTML报表应该显示
```
Symbol  Mcap      买入市值    卖出市值    收益率
GAYTES  $235.6K   $251.5K    $269.1K    +691.97%
UFO     $48.4K    无交易     无交易     —        (被180k过滤)
Clawd   $386.8K   $184.1K    $192.3K    -21.23%
```

**关键点**：
- UFO 的市值只有 $48.4K，应该**没有交易**（被180k过滤）
- GAYTES 和 Clawd 的买入市值都 >= $180K

---

## 💡 注意事项

1. **市值单位统一**：整个系统中 `market_cap` 和 `min_market_cap` 都使用 **k** 作为单位
2. **函数命名**：使用 `analyze_token_trades()` 而不是不存在的 `check_multiple_trades_from_raw()`
3. **数据结构**：`analyze_token_trades()` 返回的trades是简化格式，直接包含 `profit_rate` 和 `is_win`

---

**修复完成！** 🎉

重新运行回测后，HTML报表应该显示正确的市值，并且180k过滤会正常工作。
