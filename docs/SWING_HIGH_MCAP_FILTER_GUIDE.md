# 波峰市值门槛功能使用指南

## 📋 功能概述

波峰市值门槛功能允许你设置一个市值门槛，只有当波峰市值达到该门槛时，才启动fib买入检测。

### 核心逻辑

1. **波峰市值计算**: `market_cap = swing_high_price × supply / 1000`（单位k USD）
2. **首次触发**: 第一次波峰市值 >= 门槛时，启动fib买入检测
3. **买卖周期重置**: 完成一个完整的买卖周期后，重置门槛状态，允许下一次波峰（即使 < 门槛）也能触发买入
4. **可选参数**: `min_swing_high_mcap=None` 时不启用此功能

---

## 🔧 使用方法

### 1. 配置文件方式

```python
from trading.config import TradingConfig

# 启用波峰市值门槛（180k USD）
config = TradingConfig(
    min_swing_high_mcap=180.0  # 单位：k USD
)

# 不启用（默认）
config = TradingConfig(
    min_swing_high_mcap=None
)
```

### 2. 回测使用

```python
from trading.win_rate_analyzer import analyze_token_trades

# 代币总量（从API获取）
supply = 1_000_000_000  # 10亿

result = analyze_token_trades(
    ca='代币地址',
    raw_klines=klines,
    symbol='TOKEN',
    total_capital=2.0,
    supply=supply,                    # 必须传入
    min_swing_high_mcap=180.0,       # 市值门槛（k USD）
    max_trades=5
)
```

### 3. 单次交易检测

```python
from trading.trade_checker import check_single_trade

result = check_single_trade(
    klines=klines,
    total_capital=2.0,
    supply=1_000_000_000,
    min_swing_high_mcap=180.0
)
```

---

## 📊 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `supply` | float | 代币总量（原始单位，如1000000） | None |
| `min_swing_high_mcap` | float | 波峰市值门槛（单位k USD，如180.0表示180k） | None（不启用） |

### 市值计算公式

```python
# 波峰市值（单位：k USD）
swing_high_mcap_k = (swing_high_price * supply) / 1000

# 示例：
# swing_high_price = 0.00020
# supply = 1,000,000,000
# swing_high_mcap_k = (0.00020 * 1,000,000,000) / 1000 = 200k USD
```

---

## 🎯 使用场景

### 场景1: 首次波峰市值不足

```
波峰1: price=0.00015, mcap=150k → 不启动买入（< 180k）
波峰2: price=0.00016, mcap=160k → 不启动买入（< 180k）
波峰3: price=0.00020, mcap=200k → 启动买入 ✅（>= 180k）
  → 买入 → 卖出（完成周期）
波峰4: price=0.00010, mcap=100k → 启动买入 ✅（已重置）
```

### 场景2: 首次波峰市值达标

```
波峰1: price=0.00020, mcap=200k → 启动买入 ✅（>= 180k）
  → 买入 → 卖出（完成周期）
波峰2: price=0.00010, mcap=100k → 启动买入 ✅（已重置）
```

### 场景3: 不启用门槛

```
波峰1: price=0.00015, mcap=150k → 启动买入 ✅（未启用门槛）
波峰2: price=0.00010, mcap=100k → 启动买入 ✅（未启用门槛）
```

---

## 🔍 获取supply的方法

### 方法1: 从LogEarn API获取

```python
from backtester.fetch_klines import get_token_info

info = get_token_info(ca)
if info:
    supply = info['total_supply']
    print(f"Supply: {supply}")
```

### 方法2: 从链上获取

```python
# 使用 solana-py 或其他库从链上获取
# supply = get_supply_from_chain(ca)
```

---

## ⚠️ 注意事项

### 1. supply单位

- **使用原始单位**（例如 1000000），不是除以decimals后的单位
- LogEarn API返回的`total_supply`已经是原始单位

### 2. 市值单位

- `min_swing_high_mcap` 单位是 **k USD**（千美元）
- 180.0 表示 180,000 USD

### 3. 波峰价格

- 使用波峰K线的 `high` 价格
- 不是 `close` 或 `open`

### 4. 重置机制

- 只有完成**完整的买卖周期**（卖出100%仓位）后才重置
- 部分卖出（如Fib卖出30%）不会重置

---

## 🧪 测试验证

运行测试脚本：

```bash
cd /Users/leon/logearn-trading-skills/logearn-traidng-skills
python3 test_swing_high_mcap_filter.py
```

测试覆盖：
- ✅ 波峰市值 < 门槛 → 不触发买入
- ✅ 波峰市值 >= 门槛 → 触发买入
- ✅ 不启用门槛 → 正常交易
- ✅ 多次交易 → 重置机制正常

---

## 📝 代码修改清单

### 修改的文件

1. **`trading/fib_calculator.py`**
   - 添加 `supply`, `min_swing_high_mcap`, `swing_high_mcap_triggered` 参数
   - 在检测到波峰时计算市值并判断是否启动买入

2. **`trading/config.py`**
   - 添加 `min_swing_high_mcap` 配置项

3. **`trading/trade_checker.py`**
   - 添加 `supply`, `min_swing_high_mcap` 参数
   - 添加状态跟踪和重置逻辑

4. **`trading/win_rate_analyzer.py`**
   - 添加 `supply`, `min_swing_high_mcap` 参数传递

---

## 🚀 实际使用示例

### 回测示例

```python
from backtester.fetch_klines import get_token_info, fetch_klines, normalize_klines
from trading.win_rate_analyzer import analyze_token_trades

# 1. 获取代币信息
ca = 'your_token_address'
info = get_token_info(ca)
supply = info['total_supply'] if info else None

# 2. 获取K线数据
raw_klines = fetch_klines(ca)
klines = normalize_klines(raw_klines)

# 3. 运行回测（启用波峰市值门槛）
result = analyze_token_trades(
    ca=ca,
    raw_klines=klines,
    symbol=info['symbol'] if info else 'UNKNOWN',
    total_capital=2.0,
    supply=supply,
    min_swing_high_mcap=180.0,  # 180k USD门槛
    max_trades=5
)

# 4. 查看结果
print(f"交易次数: {len(result['trades'])}")
for trade in result['trades']:
    print(f"  第{trade['trade_number']}次: {trade['profit_rate']*100:+.2f}%")
```

### 实时交易示例（executor.py中）

```python
from trading.config import TradingConfig
from backtester.fetch_klines import get_token_info

# 1. 获取supply
info = get_token_info(ca)
supply = info['total_supply'] if info else None

# 2. 配置
config = TradingConfig(
    min_swing_high_mcap=180.0  # 启用180k门槛
)

# 3. 状态变量
swing_high_mcap_triggered = False

# 4. 交易循环中
signal = fib_signal(
    klines,
    entry_price=avg_price,
    tiers_bought=tiers_bought,
    pending_tiers=pending_tiers,
    skip_ao=False,
    entry_swing_high=entry_swing_high,
    entry_stop_price=entry_stop_price,
    fib_sold_tiers=fib_sold_tiers,
    supply=supply,
    min_swing_high_mcap=config.min_swing_high_mcap,
    swing_high_mcap_triggered=swing_high_mcap_triggered
)

# 5. 更新状态
if signal and signal.get("swing_high_mcap_triggered") is not None:
    swing_high_mcap_triggered = signal.get("swing_high_mcap_triggered")

# 6. 跳过市值不足的波峰
if signal and signal.get("action") == "swing_high_detected":
    if signal.get("mcap_threshold_not_met"):
        mcap = signal.get("swing_high_mcap_k", 0)
        print(f"波峰市值不足: {mcap:.1f}k < 180k，跳过买入")
        continue

# 7. 卖出后重置
if action in ["sell", "stop"] or (action == "fib_sell" and total_sell >= 1.0):
    swing_high_mcap_triggered = False  # 重置
```

---

## 📚 相关文档

- `BACKTEST_MCAP_FILTER_REPORT.md` - K线市值过滤功能
- `MCAP_FILTER_QUICK_CHECK.md` - 市值过滤快速检查
- `test_swing_high_mcap_filter.py` - 波峰市值门槛测试

---

**最后更新**: 2026-05-10  
**功能状态**: ✅ 已实现并测试通过
