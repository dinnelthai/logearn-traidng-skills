# 对外公开接口

## 概述

本项目只对外暴露**2个核心交易接口**，K线获取由内部自动处理。

---

## 🎯 核心接口

### 1. Fibonacci交易（单次交易）

**功能**：在一个代币上执行一次完整的买入-卖出交易，然后停止。

**接口**：`run_fibonacci_trade()`

```python
from trading import run_fibonacci_trade

# 运行Fibonacci交易
run_fibonacci_trade(
    ca="代币地址",
    total_capital=2.0,      # 总资金（SOL）
    check_interval=60       # 检查间隔（秒）
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ca` | str | - | 代币地址（必需） |
| `total_capital` | float | `2.0` | 总资金（SOL） |
| `check_interval` | int | `60` | 检查间隔（秒） |

**特点**：
- ✅ 自动获取5分钟K线
- ✅ Fibonacci回撤买入（61.8%, 78.6%, 86.1%）
- ✅ AO卖出信号
- ✅ 分批买入，分批卖出
- ✅ 全部卖出后自动停止

---

### 2. RSI定投（定投策略）

**功能**：基于RSI指标进行定投，RSI<30时买入，达到最大次数后停止。

**接口**：`run_rsi_dca()`

```python
from trading import run_rsi_dca

# 运行RSI定投
run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,         # 每次定投金额（SOL）
    max_buy_count=10,       # 最大定投次数
    check_interval=300      # 检查间隔（秒）
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ca` | str | - | 代币地址（必需） |
| `dca_amount` | float | - | 每次定投金额（SOL，必需） |
| `max_buy_count` | int | - | 最大定投次数（必需） |
| `check_interval` | int | `300` | 检查间隔（秒） |
| `rsi_period` | int | `14` | RSI周期 |
| `rsi_buy_threshold` | float | `30.0` | RSI买入阈值 |
| `rsi_reset_threshold` | float | `50.0` | RSI重置阈值 |

**特点**：
- ✅ 自动获取1小时K线
- ✅ RSI < 30 时自动买入
- ✅ 买入后等待RSI > 50才能再次买入
- ✅ 固定金额定投
- ✅ 达到最大次数后自动停止

---

## 📝 完整示例

### 示例1: Fibonacci交易

```python
#!/usr/bin/env python3
import os
from trading import run_fibonacci_trade

# 配置
CA = os.getenv("TOKEN_CA", "代币地址")
TOTAL_CAPITAL = 2.0
CHECK_INTERVAL = 60

# 运行
if __name__ == "__main__":
    run_fibonacci_trade(
        ca=CA,
        total_capital=TOTAL_CAPITAL,
        check_interval=CHECK_INTERVAL
    )
```

### 示例2: RSI定投

```python
#!/usr/bin/env python3
import os
from trading import run_rsi_dca

# 配置
CA = os.getenv("TOKEN_CA", "代币地址")
DCA_AMOUNT = 0.1
MAX_BUY_COUNT = 10
CHECK_INTERVAL = 300

# 运行
if __name__ == "__main__":
    run_rsi_dca(
        ca=CA,
        dca_amount=DCA_AMOUNT,
        max_buy_count=MAX_BUY_COUNT,
        check_interval=CHECK_INTERVAL
    )
```

---

## 🔧 命令行使用

### 方式1: 使用示例脚本

```bash
# 设置环境变量
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"

# Fibonacci交易
python example_fibonacci_trade.py

# RSI定投
python example_rsi_dca.py
```

### 方式2: 直接调用

```bash
# Fibonacci交易
python -c "
from trading import run_fibonacci_trade
run_fibonacci_trade(ca='代币地址', total_capital=2.0)
"

# RSI定投
python -c "
from trading import run_rsi_dca
run_rsi_dca(ca='代币地址', dca_amount=0.1, max_buy_count=10)
"
```

---

## 🔑 环境变量

```bash
# 必需
export LOGEARN_API_KEY="你的API Key"

# 可选（可在代码中指定）
export TOKEN_CA="代币地址"
```

---

## ⚙️ 内部实现

### K线获取（内部自动处理）

- **Fibonacci交易**：自动获取5分钟K线
- **RSI定投**：自动获取1小时K线

用户**不需要**关心K线获取的细节，只需要传递CA地址即可。

### 交易执行（内部自动处理）

- 自动调用LogEarn API
- 自动绑定钱包（LogEarn skill与token绑定）
- 自动处理买入卖出

---

## 📊 策略对比

| 特性 | Fibonacci交易 | RSI定投 |
|------|--------------|---------|
| **K线周期** | 5分钟 | 1小时 |
| **买入策略** | Fibonacci回撤 | RSI < 30 |
| **卖出策略** | AO信号 + Fibonacci | 无（只买入） |
| **交易次数** | 1次完整交易 | 多次定投 |
| **适用场景** | 短线交易 | 长期定投 |
| **资金管理** | 分批买入 | 固定金额 |

---

## ❓ 常见问题

### Q1: 如何选择使用哪个接口？

- **短线交易**：使用 `run_fibonacci_trade()`
- **长期定投**：使用 `run_rsi_dca()`

### Q2: 可以修改K线周期吗？

不可以，K线周期由策略内部决定：
- Fibonacci交易固定使用5分钟K线
- RSI定投固定使用1小时K线

### Q3: 如何停止机器人？

按 `Ctrl+C` 手动停止，或等待交易完成后自动停止。

### Q4: 需要指定钱包地址吗？

不需要，LogEarn skill与token绑定，会自动使用绑定的钱包。

### Q5: 如何查看交易日志？

所有接口都会自动输出实时日志到控制台。

---

## 🎉 总结

本项目只对外暴露**2个核心接口**：

1. **`run_fibonacci_trade()`** - Fibonacci交易（5分钟K线）
2. **`run_rsi_dca()`** - RSI定投（1小时K线）

**特点**：
- ✅ 简单易用 - 只需传递CA地址
- ✅ 自动化 - K线获取、交易执行全自动
- ✅ 无需配置 - 策略参数已优化
- ✅ 实时日志 - 完整的交易日志输出

**使用方式**：
```python
from trading import run_fibonacci_trade, run_rsi_dca

# Fibonacci交易
run_fibonacci_trade(ca="代币地址", total_capital=2.0)

# RSI定投
run_rsi_dca(ca="代币地址", dca_amount=0.1, max_buy_count=10)
```

就这么简单！🚀
