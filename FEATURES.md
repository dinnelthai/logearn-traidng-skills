# LogEarn Trading Skills - 主要功能

## 🎯 三大核心功能

### 1️⃣ Fibonacci自动交易 🤖

**功能**: 基于Fibonacci回撤自动买入，AO信号自动卖出

**使用场景**: 
- 全自动交易单个代币
- 从信号触发到完成一次完整交易

**核心逻辑**:
```
信号触发 → 计算FIB档位 → 分批买入(61.8%/78.6%/86.1%) → AO绿转红卖出
```

**使用方法**:
```python
from trading import run_fibonacci_trade

run_fibonacci_trade(
    ca="代币地址",
    total_capital=2.0,      # 总资金2 SOL
    check_interval=60       # 每60秒检查一次
)
```

**特点**:
- ✅ 自动K线缓存（首次全量，后续增量）
- ✅ 分批买入（降低风险）
- ✅ AO信号卖出（捕捉顶部）
- ✅ 止损保护（92%回撤）

**文件**: `trading/fibonacci_trade.py`

---

### 2️⃣ RSI定投机器人 📊

**功能**: 基于RSI超卖信号自动定投，支持单币和多币

**使用场景**:
- 长期定投策略
- 同时监控多个代币（支持15K+代币）

**核心逻辑**:
```
RSI < 30 → 超卖 → 买入 → RSI > 70 → 超买 → 卖出
```

**使用方法**:

#### 单币定投
```python
from trading import run_rsi_dca

run_rsi_dca(
    ca="代币地址",
    total_capital=10.0,     # 总资金10 SOL
    buy_amount=0.1,         # 每次买入0.1 SOL
    check_interval=300      # 每5分钟检查
)
```

#### 多币定投
```python
from trading import run_rsi_dca_multi, DCAConfig

configs = [
    DCAConfig(ca="CA1", total_capital=10.0, buy_amount=0.1),
    DCAConfig(ca="CA2", total_capital=5.0, buy_amount=0.05),
    DCAConfig(ca="CA3", total_capital=8.0, buy_amount=0.08),
]

run_rsi_dca_multi(configs, check_interval=300)
```

**特点**:
- ✅ RSI指标判断（1小时K线）
- ✅ 分批建仓（降低成本）
- ✅ 自动止盈（RSI>70卖出）
- ✅ 支持15K+代币并发监控

**文件**: 
- 单币: `trading/rsi_dca_bot.py`
- 多币: `trading/rsi_dca_manager.py`

---

### 3️⃣ AO监控机器人 🔔

**功能**: 接管现有持仓，监控AO信号自动卖出

**使用场景**:
- 已经持有代币，想要自动卖出
- 不需要系统买入，只监控卖出信号

**核心逻辑**:
```
接管持仓 → 监控AO → 绿转红 → 自动卖出
```

**使用方法**:

#### 单币监控
```python
from trading import run_ao_monitor

run_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,    # 买入均价（可选）
    sell_percentage=1.0,    # 卖出100%
    check_interval=60       # 每60秒检查
)
```

#### 多币监控
```python
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(ca="CA1", entry_price=0.00004, sell_percentage=1.0),
    AOMonitorConfig(ca="CA2", entry_price=0.00005, sell_percentage=0.5),
    AOMonitorConfig(ca="CA3", entry_price=None, sell_percentage=1.0),
]

run_ao_monitor_multi(configs, check_interval=60)
```

**卖出策略**:
- ✅ **AO >= 35k 绿转红** → 立即卖出
- ✅ **AO < 35k 绿转红 + 收益率 > 50%** → 卖出（需提供买入价）
- ❌ **AO < 35k 绿转红 + 无买入价** → 不卖出（保守模式）

**特点**:
- ✅ 接管现有持仓（无需系统买入）
- ✅ 只监控卖出信号
- ✅ 支持有/无买入价两种模式
- ✅ 收益率保护（避免亏损卖出）

**文件**: `trading/ao_monitor.py`

---

## 📊 功能对比

| 功能 | Fibonacci交易 | RSI定投 | AO监控 |
|------|--------------|---------|--------|
| **买入** | ✅ 自动 | ✅ 自动 | ❌ 不买入 |
| **卖出** | ✅ 自动 | ✅ 自动 | ✅ 自动 |
| **K线周期** | 5分钟 | 1小时 | 5分钟 |
| **策略** | Fibonacci | RSI | AO |
| **适用场景** | 单次交易 | 长期定投 | 接管持仓 |
| **多币支持** | ❌ 单币 | ✅ 多币 | ✅ 多币 |

---

## 🔧 核心模块

### 交易执行
- **TradeExecutor** - 执行买入/卖出操作
- **PositionManager** - 管理仓位和资金
- **ProfitManager** - 止盈止损管理

### 数据获取
- **KlineService** - 获取K线数据
- **KlineCache** - K线缓存（增量更新）

### 技术分析
- **fib_calculator** - Fibonacci计算、AO计算
- **indicators** - RSI等技术指标

---

## 🎯 使用建议

### 场景1: 想要全自动交易
→ 使用 **Fibonacci交易**
```python
run_fibonacci_trade(ca="代币地址", total_capital=2.0)
```

### 场景2: 想要长期定投
→ 使用 **RSI定投**
```python
run_rsi_dca(ca="代币地址", total_capital=10.0, buy_amount=0.1)
```

### 场景3: 已有持仓，想自动卖出
→ 使用 **AO监控**
```python
run_ao_monitor(ca="代币地址", entry_price=0.00004)
```

### 场景4: 同时监控多个代币
→ 使用 **多币版本**
```python
# RSI定投多币
run_rsi_dca_multi(configs)

# AO监控多币
run_ao_monitor_multi(configs)
```

---

## 📚 相关文档

- **完整文档**: [README.md](./README.md)
- **快速开始**: [QUICK_START.md](./QUICK_START.md)
- **AO监控**: [AO_MONITOR_README.md](./AO_MONITOR_README.md)
- **Hermes提示语**: [HERMES_PROMPTS.md](./HERMES_PROMPTS.md)
- **安装指南**: [INSTALL.md](./INSTALL.md)

---

## 🚀 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 设置API Key
export LOGEARN_API_KEY="your_api_key"

# 3. 运行示例
python example_fibonacci_trade.py
python example_rsi_dca.py
python example_ao_monitor.py
```

---

## ⚙️ 环境要求

- Python 3.8+
- LogEarn API Key
- LogEarn CLI

---

**三大核心功能，满足所有交易需求！** 🎉
