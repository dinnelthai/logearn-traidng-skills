# AO监控机器人使用文档

## 📖 概述

AO监控机器人是一个自动化交易工具，用于接管现有持仓并根据AO（Awesome Oscillator）指标自动卖出。

### 核心功能
- ✅ 接管现有持仓（无需系统买入）
- ✅ 监控AO绿转红信号
- ✅ 自动执行卖出操作
- ✅ 支持多代币同时监控
- ✅ 灵活的卖出策略配置

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/leon/logearn-trading-skills/logearn-traidng-skills
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
export LOGEARN_API_KEY="your_api_key_here"
```

### 3. 创建监控脚本

创建文件 `my_ao_monitor.py`：

```python
#!/usr/bin/env python3
import os
from trading import run_ao_monitor_multi, AOMonitorConfig

# 设置API Key
os.environ["LOGEARN_API_KEY"] = "your_api_key"

# 配置要监控的代币
configs = [
    AOMonitorConfig(
        ca="你的代币地址",
        entry_price=0.00004,  # 你的买入均价
        sell_percentage=1.0   # 卖出100%
    ),
]

# 启动监控
run_ao_monitor_multi(configs)
```

### 4. 运行

```bash
python3 my_ao_monitor.py
```

---

## 📊 卖出逻辑说明

### 模式1: 提供买入价（推荐）

```python
AOMonitorConfig(
    ca="代币地址",
    entry_price=0.00004,  # 提供买入均价
    sell_percentage=1.0
)
```

**卖出条件**：
- ✅ **AO >= 35k 绿转红** → 立即卖出
- ✅ **AO < 35k 绿转红 + 收益率 > 50%** → 卖出
- ❌ **AO < 35k 绿转红 + 收益率 < 50%** → 不卖出（保护你不亏损）

**优点**：
- 有收益率保护
- 更灵活的卖出策略
- AO < 35k 时如果盈利足够也能卖出

---

### 模式2: 不提供买入价（保守模式）

```python
AOMonitorConfig(
    ca="代币地址",
    entry_price=None,  # 不提供买入价
    sell_percentage=1.0
)
```

**卖出条件**：
- ✅ **AO >= 35k 绿转红** → 立即卖出
- ❌ **AO < 35k 绿转红** → 不卖出（无法判断收益率）

**优点**：
- 更保守
- 只在强信号时卖出
- 不需要知道买入价

---

## 🎯 使用场景

### 场景1: 监控单个代币

```python
from trading import run_ao_monitor

run_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,
    sell_percentage=1.0,
    interval='5m',
    check_interval=60
)
```

---

### 场景2: 监控多个代币

```python
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(ca="CA1", entry_price=0.00004),
    AOMonitorConfig(ca="CA2", entry_price=0.00005),
    AOMonitorConfig(ca="CA3", entry_price=None),
]

run_ao_monitor_multi(configs, interval='5m', check_interval=60)
```

---

### 场景3: 部分卖出

```python
AOMonitorConfig(
    ca="代币地址",
    entry_price=0.00004,
    sell_percentage=0.5  # 只卖50%
)
```

---

## ⚙️ 参数说明

### AOMonitorConfig

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ca` | str | ✅ | - | 代币地址 |
| `entry_price` | float | ❌ | None | 买入均价（可选） |
| `sell_percentage` | float | ❌ | 1.0 | 卖出比例（0-1） |

### run_ao_monitor_multi

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `configs` | List[AOMonitorConfig] | - | 监控配置列表 |
| `interval` | str | '5m' | K线周期（5m/15m/1h） |
| `check_interval` | int | 60 | 检查间隔（秒） |

---

## 📋 运行效果示例

```bash
================================================================================
🔍 验证持仓...
================================================================================
✅ [FDBjQdN4...] 持仓: 1234567.89 tokens
✅ [另一个代币...] 持仓: 9876543.21 tokens

================================================================================
🤖 开始监控 2 个代币的AO信号
K线周期: 5m
检查间隔: 60秒
================================================================================

[每60秒检查一次...]

🔔 [FDBjQdN4...] AO卖出信号触发！
   原因: ao≥35k绿转红
   AO值: 0.00003800
   当前价: 0.00006
   收益率: 50.00%

📉 执行卖出 100%...
   ✅ 卖出成功！
   进度: 1/2

[继续监控...]

🔔 [另一个代币...] AO卖出信号触发！
   原因: ao<35k但收益率>50%(60.0%)
   AO值: 0.00002500
   当前价: 0.00008
   收益率: 60.00%

📉 执行卖出 100%...
   ✅ 卖出成功！
   进度: 2/2

================================================================================
✅ 所有监控完成！已卖出 2/2 个代币
================================================================================
```

---

## ⚠️ 重要说明

### 1. 关于"绿转红"逻辑

AO监控**只在AO从绿变红的那一刻触发**：

- ✅ 如果启动时AO正在绿转红 → 会触发卖出
- ❌ 如果启动时AO已经红了3根 → **不会触发卖出**
- ℹ️ 需要等待下一次绿转红信号

**建议**：启动监控前先检查当前AO状态

---

### 2. 如何获取买入价

```bash
# 方法1: 查看LogEarn持仓
python3 logearn-cli.py log-get-positions

# 方法2: 查看交易历史，计算平均买入价

# 方法3: 不提供买入价（使用保守模式）
entry_price=None
```

---

### 3. 配置建议

- ✅ `check_interval=60` - 每分钟检查一次（推荐）
- ✅ `interval='5m'` - 5分钟K线（推荐）
- ⚠️ 不要设置太短的检查间隔（避免API限流）
- ✅ 提供买入价以获得更灵活的策略

---

## 🔧 高级用法

### 自定义AO阈值

修改 `trading/config.py`：

```python
@dataclass
class AOConfig:
    threshold_normal: float = 0.00003500  # 35k（默认）
    profit_threshold: float = 0.50         # 50%收益率要求
```

---

### 监控日志

系统会自动输出详细日志：
- 持仓验证信息
- AO信号检测
- 卖出执行结果
- 进度统计

---

## ❓ 常见问题

### Q1: 为什么AO < 35k时不卖出？

**A**: 如果没有提供买入价（`entry_price=None`），系统无法判断收益率，为了保护你不会在AO < 35k时卖出。

**解决方案**：提供买入价，系统会在收益率 > 50% 时卖出。

---

### Q2: 如何停止监控？

**A**: 按 `Ctrl+C` 即可随时停止。

---

### Q3: 可以同时监控多少个代币？

**A**: 理论上无限制，但建议不超过10个，避免API限流。

---

### Q4: 卖出失败怎么办？

**A**: 系统会输出失败原因，常见原因：
- 持仓不足
- 网络问题
- API限流

系统会继续监控，下次信号触发时会重试。

---

## 📚 相关文档

- [主README](./README.md) - 完整交易系统文档
- [Fibonacci交易](./trading/README.md) - Fibonacci策略说明
- [RSI定投](./trading/rsi_dca_bot.py) - RSI定投策略

---

## 🎉 总结

AO监控机器人提供了一个简单而强大的方式来管理你的持仓：

1. ✅ **简单易用** - 只需配置CA和买入价
2. ✅ **自动化** - 无需手动盯盘
3. ✅ **灵活** - 支持多种卖出策略
4. ✅ **安全** - 有收益率保护（提供买入价时）

**立即开始使用，让AO监控机器人帮你自动管理持仓！** 🚀
