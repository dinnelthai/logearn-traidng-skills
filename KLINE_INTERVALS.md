# K线周期配置说明

## 📊 各功能的K线周期

### 1️⃣ Fibonacci自动交易
- **默认周期**: `5m` (5分钟)
- **是否可配置**: ❌ 不可配置（硬编码）
- **位置**: `trading/fibonacci_trade.py`
- **说明**: 使用5分钟K线进行Fibonacci回撤分析

```python
from trading import run_fibonacci_trade

# 固定使用5分钟K线
run_fibonacci_trade(ca="代币地址", total_capital=2.0)
```

---

### 2️⃣ RSI定投
- **默认周期**: `1h` (1小时)
- **是否可配置**: ✅ 可配置
- **参数名**: `interval`
- **位置**: `trading/rsi_dca_bot.py`
- **说明**: 使用1小时K线计算RSI指标

```python
from trading import run_rsi_dca

# 默认1小时K线
run_rsi_dca(ca="代币地址", total_capital=10.0, buy_amount=0.1)

# 自定义K线周期（不推荐修改）
run_rsi_dca(
    ca="代币地址", 
    total_capital=10.0, 
    buy_amount=0.1,
    interval='15m'  # 可选：5m, 15m, 1h, 4h, 1d
)
```

---

### 3️⃣ AO监控
- **默认周期**: `5m` (5分钟) ⭐
- **是否可配置**: ✅ 可配置
- **参数名**: `interval`
- **位置**: `trading/ao_monitor.py`
- **说明**: 使用5分钟K线计算AO指标

```python
from trading import run_ao_monitor

# 默认5分钟K线
run_ao_monitor(ca="代币地址", entry_price=0.00004)

# 自定义K线周期
run_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,
    interval='15m'  # 可选：5m, 15m, 1h
)
```

---

### 4️⃣ AO监控管理器
- **默认周期**: `5m` (5分钟)
- **是否可配置**: ✅ 可配置
- **参数名**: `interval`
- **位置**: `trading/ao_monitor_manager.py`

```python
from trading import add_ao_monitor

# 默认5分钟K线
add_ao_monitor(ca="代币地址", entry_price=0.00004)

# 自定义K线周期
add_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,
    interval='15m'  # 可选：5m, 15m, 1h
)
```

---

## 🎯 支持的K线周期

LogEarn API支持以下K线周期：

| 周期代码 | 说明 | 适用场景 |
|---------|------|---------|
| `5m` | 5分钟 | 短线交易、快速反应 |
| `15m` | 15分钟 | 中短线交易 |
| `1h` | 1小时 | 中线交易、RSI定投 |
| `4h` | 4小时 | 中长线交易 |
| `1d` | 1天 | 长线交易 |

---

## 📋 功能对比表

| 功能 | 默认周期 | 可配置 | 推荐周期 | 说明 |
|------|---------|--------|---------|------|
| **Fibonacci交易** | 5m | ❌ | 5m | 固定5分钟，适合短线 |
| **RSI定投** | 1h | ✅ | 1h | 1小时更稳定 |
| **AO监控** | 5m | ✅ | 5m 或 15m | 可根据需求调整 |
| **AO管理器** | 5m | ✅ | 5m 或 15m | 可根据需求调整 |

---

## 🔧 如何修改默认周期

### 方法1: 在调用时指定（推荐）

```python
# AO监控 - 使用15分钟K线
run_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,
    interval='15m'  # 修改周期
)

# RSI定投 - 使用15分钟K线
run_rsi_dca(
    ca="代币地址",
    total_capital=10.0,
    buy_amount=0.1,
    interval='15m'  # 修改周期
)
```

### 方法2: 修改源码默认值（不推荐）

如果想永久修改默认值，可以编辑源码：

```python
# trading/ao_monitor.py
def run_ao_monitor(ca: str,
                   entry_price: Optional[float] = None,
                   interval: str = '15m',  # 改为15分钟
                   check_interval: int = 60,
                   sell_percentage: float = 1.0):
```

---

## ⚠️ 注意事项

### 1. K线周期对AO值的影响

**不同周期的AO值不同！**

- `5m` K线: AO值变化快，更敏感
- `15m` K线: AO值变化慢，更稳定
- `1h` K线: AO值变化很慢，适合长线

**示例**:
```
同一时刻，同一代币：
- 5m K线 AO:  0.00003800 (快速波动)
- 15m K线 AO: 0.00003500 (较稳定)
- 1h K线 AO:  0.00003200 (很稳定)
```

### 2. 与LogEarn页面对比

**确保周期一致！**

如果你在LogEarn页面看到的AO值和程序计算的不一样：

1. ✅ 检查LogEarn页面使用的K线周期（5m/15m/1h）
2. ✅ 确保程序使用相同的周期
3. ✅ 确认时间对齐（最新K线的时间）

**调试工具**:
```bash
# 查看5分钟K线的AO计算
python tools/debug_ao.py CA地址 --interval 5m

# 查看15分钟K线的AO计算
python tools/debug_ao.py CA地址 --interval 15m

# 对比LogEarn显示的值
python tools/debug_ao.py CA地址 --interval 5m --logearn-ao 0.00003800
```

### 3. 推荐配置

#### 短线交易（快速进出）
```python
run_ao_monitor(ca="代币地址", interval='5m')
```

#### 中线交易（稳健持有）
```python
run_ao_monitor(ca="代币地址", interval='15m')
```

#### 长线交易（长期持有）
```python
run_ao_monitor(ca="代币地址", interval='1h')
```

---

## 🎯 TradingView标准

我们的AO计算完全符合TradingView标准：

```
AO = SMA(HL2, 5) - SMA(HL2, 34)
其中: HL2 = (High + Low) / 2
```

**无论使用哪个K线周期，计算公式都相同！**

---

## 📊 实际使用示例

### 示例1: 对比不同周期的AO值

```python
from trading import run_ao_monitor

# 5分钟K线（快速反应）
run_ao_monitor(ca="代币地址", entry_price=0.00004, interval='5m')

# 15分钟K线（较稳定）
run_ao_monitor(ca="代币地址", entry_price=0.00004, interval='15m')
```

### 示例2: 多币监控使用不同周期

```python
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(ca="CA1", entry_price=0.00004),  # 使用默认5m
    AOMonitorConfig(ca="CA2", entry_price=0.00005),
]

# 所有代币使用15分钟K线
run_ao_monitor_multi(configs, interval='15m')
```

### 示例3: 管理器使用不同周期

```python
from trading import add_ao_monitor

# CA1使用5分钟
add_ao_monitor(ca="CA1", entry_price=0.00004, interval='5m')

# CA2使用15分钟
add_ao_monitor(ca="CA2", entry_price=0.00005, interval='15m')
```

---

## ✅ 总结

1. **AO监控默认使用5分钟K线** ⭐
2. **可以通过 `interval` 参数修改**
3. **不同周期的AO值不同，需要对比时确保周期一致**
4. **推荐短线用5m，中线用15m**
5. **使用调试工具验证计算正确性**

---

**根据你的交易风格选择合适的K线周期！** 🎉
