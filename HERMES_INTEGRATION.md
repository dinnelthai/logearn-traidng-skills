# Hermes Agent 集成指南

## 🎯 Hermes如何调用我们的接口

### 核心原理

Hermes通过识别用户意图，调用对应的Python接口来执行交易策略。

```
用户输入 → Hermes理解意图 → 提取参数 → 调用Python接口 → 执行交易
```

---

## 📋 三大核心接口

### 1️⃣ Fibonacci自动交易接口

**接口定义**:
```python
from trading import run_fibonacci_trade

run_fibonacci_trade(
    ca: str,                    # 代币地址（必需）
    total_capital: float,       # 总资金SOL（必需）
    check_interval: int = 60    # 检查间隔秒（可选）
)
```

**Hermes调用示例**:
```python
# 用户说："帮我用Fibonacci策略交易这个代币，投入2个SOL"
from trading import run_fibonacci_trade

run_fibonacci_trade(
    ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
    total_capital=2.0,
    check_interval=60
)
```

---

### 2️⃣ RSI定投接口

#### 单币定投
**接口定义**:
```python
from trading import run_rsi_dca

run_rsi_dca(
    ca: str,                    # 代币地址（必需）
    total_capital: float,       # 总资金SOL（必需）
    buy_amount: float,          # 每次买入SOL（必需）
    check_interval: int = 300   # 检查间隔秒（可选）
)
```

**Hermes调用示例**:
```python
# 用户说："用RSI策略定投这个代币，总共10个SOL，每次买0.1"
from trading import run_rsi_dca

run_rsi_dca(
    ca="代币地址",
    total_capital=10.0,
    buy_amount=0.1,
    check_interval=300
)
```

#### 多币定投
**接口定义**:
```python
from trading import run_rsi_dca_multi, DCAConfig

configs = [
    DCAConfig(
        ca: str,                    # 代币地址
        total_capital: float,       # 总资金SOL
        buy_amount: float           # 每次买入SOL
    ),
    # ... 更多配置
]

run_rsi_dca_multi(
    configs: List[DCAConfig],       # 配置列表（必需）
    check_interval: int = 300       # 检查间隔秒（可选）
)
```

**Hermes调用示例**:
```python
# 用户说："同时定投这3个代币，每个10 SOL，每次买0.1"
from trading import run_rsi_dca_multi, DCAConfig

configs = [
    DCAConfig(ca="CA1", total_capital=10.0, buy_amount=0.1),
    DCAConfig(ca="CA2", total_capital=10.0, buy_amount=0.1),
    DCAConfig(ca="CA3", total_capital=10.0, buy_amount=0.1),
]

run_rsi_dca_multi(configs, check_interval=300)
```

---

### 3️⃣ AO监控接口

#### 单币监控
**接口定义**:
```python
from trading import run_ao_monitor

run_ao_monitor(
    ca: str,                        # 代币地址（必需）
    entry_price: float = None,      # 买入均价（可选）
    sell_percentage: float = 1.0,   # 卖出比例（可选）
    interval: str = '5m',           # K线周期（可选）
    check_interval: int = 60        # 检查间隔秒（可选）
)
```

**Hermes调用示例**:
```python
# 用户说："监控这个代币的AO信号，买入价0.00004，触发时全部卖出"
from trading import run_ao_monitor

run_ao_monitor(
    ca="代币地址",
    entry_price=0.00004,
    sell_percentage=1.0,
    check_interval=60
)
```

#### 多币监控
**接口定义**:
```python
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(
        ca: str,                        # 代币地址
        entry_price: float = None,      # 买入均价（可选）
        sell_percentage: float = 1.0    # 卖出比例（可选）
    ),
    # ... 更多配置
]

run_ao_monitor_multi(
    configs: List[AOMonitorConfig],     # 配置列表（必需）
    interval: str = '5m',               # K线周期（可选）
    check_interval: int = 60            # 检查间隔秒（可选）
)
```

**Hermes调用示例**:
```python
# 用户说："监控这3个代币的AO信号"
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(ca="CA1", entry_price=0.00004, sell_percentage=1.0),
    AOMonitorConfig(ca="CA2", entry_price=0.00005, sell_percentage=0.5),
    AOMonitorConfig(ca="CA3", entry_price=None, sell_percentage=1.0),
]

run_ao_monitor_multi(configs, check_interval=60)
```

---

## 🎨 Hermes提示词模板

### 模板1: Fibonacci交易

**用户输入**:
```
帮我用Fibonacci策略交易这个代币：[CA地址]，投入[X]个SOL
```

**Hermes应该生成**:
```python
import os
from trading import run_fibonacci_trade

# 确保API Key已设置
if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

# 启动Fibonacci交易
run_fibonacci_trade(
    ca="[CA地址]",
    total_capital=[X],
    check_interval=60
)
```

**变体提示词**:
- "用FIB策略交易这个币"
- "Fibonacci自动交易"
- "分批买入这个代币"
- "用回撤策略交易"

---

### 模板2: RSI定投（单币）

**用户输入**:
```
用RSI策略定投这个代币：[CA地址]，总共[X] SOL，每次买[Y] SOL
```

**Hermes应该生成**:
```python
import os
from trading import run_rsi_dca

# 确保API Key已设置
if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

# 启动RSI定投
run_rsi_dca(
    ca="[CA地址]",
    total_capital=[X],
    buy_amount=[Y],
    check_interval=300
)
```

**变体提示词**:
- "RSI定投这个币"
- "超卖时买入这个代币"
- "用RSI策略建仓"
- "定投这个代币"

---

### 模板3: RSI定投（多币）

**用户输入**:
```
同时定投这些代币：
1. [CA1]，投入[X1] SOL，每次[Y1]
2. [CA2]，投入[X2] SOL，每次[Y2]
3. [CA3]，投入[X3] SOL，每次[Y3]
```

**Hermes应该生成**:
```python
import os
from trading import run_rsi_dca_multi, DCAConfig

# 确保API Key已设置
if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

# 配置多个代币
configs = [
    DCAConfig(ca="[CA1]", total_capital=[X1], buy_amount=[Y1]),
    DCAConfig(ca="[CA2]", total_capital=[X2], buy_amount=[Y2]),
    DCAConfig(ca="[CA3]", total_capital=[X3], buy_amount=[Y3]),
]

# 启动多币定投
run_rsi_dca_multi(configs, check_interval=300)
```

**变体提示词**:
- "批量定投这些代币"
- "同时监控多个代币的RSI"
- "多币定投"

---

### 模板4: AO监控（单币）

**用户输入**:
```
监控这个代币的AO信号：[CA地址]，买入价[X]
```

**Hermes应该生成**:
```python
import os
from trading import run_ao_monitor

# 确保API Key已设置
if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

# 启动AO监控
run_ao_monitor(
    ca="[CA地址]",
    entry_price=[X],
    sell_percentage=1.0,
    check_interval=60
)
```

**变体提示词**:
- "AO监控这个币"
- "监控AO信号自动卖出"
- "绿转红时卖出"
- "接管这个持仓"

---

### 模板5: AO监控（多币）

**用户输入**:
```
监控这些代币的AO信号：
1. [CA1]，买入价[X1]
2. [CA2]，买入价[X2]
3. [CA3]，买入价未知
```

**Hermes应该生成**:
```python
import os
from trading import run_ao_monitor_multi, AOMonitorConfig

# 确保API Key已设置
if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

# 配置多个代币
configs = [
    AOMonitorConfig(ca="[CA1]", entry_price=[X1], sell_percentage=1.0),
    AOMonitorConfig(ca="[CA2]", entry_price=[X2], sell_percentage=1.0),
    AOMonitorConfig(ca="[CA3]", entry_price=None, sell_percentage=1.0),
]

# 启动多币监控
run_ao_monitor_multi(configs, check_interval=60)
```

**变体提示词**:
- "批量监控AO信号"
- "同时监控多个代币"
- "多币AO监控"

---

## 🔍 参数提取规则

### Hermes需要从用户输入中提取的参数

#### 1. 代币地址 (ca)
**识别模式**:
```
- "CA: xxx"
- "代币地址: xxx"
- "token: xxx"
- "这个代币: xxx"
- 直接的44字符Solana地址
```

**提取示例**:
```
用户: "监控这个代币 FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump"
提取: ca = "FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump"
```

---

#### 2. 资金金额 (total_capital, buy_amount)
**识别模式**:
```
- "投入X个SOL" → total_capital = X
- "总共X SOL" → total_capital = X
- "每次买Y SOL" → buy_amount = Y
- "每次Y" → buy_amount = Y
```

**提取示例**:
```
用户: "投入10个SOL，每次买0.1"
提取: total_capital = 10.0, buy_amount = 0.1
```

---

#### 3. 买入价 (entry_price)
**识别模式**:
```
- "买入价X" → entry_price = X
- "成本价X" → entry_price = X
- "买入均价X" → entry_price = X
- "不知道买入价" → entry_price = None
- "买入价未知" → entry_price = None
```

**提取示例**:
```
用户: "买入价0.00004"
提取: entry_price = 0.00004

用户: "不知道买入价"
提取: entry_price = None
```

---

#### 4. 卖出比例 (sell_percentage)
**识别模式**:
```
- "卖出100%" → sell_percentage = 1.0
- "卖出50%" → sell_percentage = 0.5
- "全部卖出" → sell_percentage = 1.0
- "卖一半" → sell_percentage = 0.5
- 默认 → sell_percentage = 1.0
```

**提取示例**:
```
用户: "触发时卖出50%"
提取: sell_percentage = 0.5
```

---

#### 5. 检查间隔 (check_interval)
**识别模式**:
```
- "每X秒检查" → check_interval = X
- "每X分钟" → check_interval = X * 60
- "每小时" → check_interval = 3600
- 默认 → check_interval = 60 (Fibonacci/AO) 或 300 (RSI)
```

**提取示例**:
```
用户: "每5分钟检查一次"
提取: check_interval = 300
```

---

## 🎯 意图识别规则

### Hermes如何判断用户想用哪个功能？

#### 识别Fibonacci交易
**关键词**:
- `fibonacci`, `fib`, `FIB`
- `回撤`, `分批买入`
- `自动交易`

**判断逻辑**:
```python
if any(keyword in user_input.lower() for keyword in ['fibonacci', 'fib', '回撤', '分批买入']):
    return "fibonacci_trade"
```

---

#### 识别RSI定投
**关键词**:
- `rsi`, `RSI`
- `定投`, `建仓`
- `超卖`, `超买`
- `每次买`

**判断逻辑**:
```python
if any(keyword in user_input.lower() for keyword in ['rsi', '定投', '超卖', '每次买']):
    # 检查是否多币
    if '同时' in user_input or '批量' in user_input or user_input.count('CA') > 1:
        return "rsi_dca_multi"
    else:
        return "rsi_dca"
```

---

#### 识别AO监控
**关键词**:
- `ao`, `AO`, `监控`
- `绿转红`, `卖出信号`
- `接管`, `持仓`
- `买入价` (通常伴随监控)

**判断逻辑**:
```python
if any(keyword in user_input.lower() for keyword in ['ao', '监控', '绿转红', '接管']):
    # 检查是否多币
    if '同时' in user_input or '批量' in user_input or user_input.count('CA') > 1:
        return "ao_monitor_multi"
    else:
        return "ao_monitor"
```

---

## 📝 完整对话示例

### 示例1: Fibonacci交易

**用户**:
```
帮我用Fibonacci策略交易这个代币：FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，投入2个SOL
```

**Hermes识别**:
- 意图: `fibonacci_trade`
- 参数: `ca="FDBjQdN4...", total_capital=2.0`

**Hermes生成代码**:
```python
import os
from trading import run_fibonacci_trade

if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

print("🚀 启动Fibonacci自动交易...")
print(f"代币: FDBjQdN4...")
print(f"总资金: 2.0 SOL")
print(f"策略: FIB回撤买入 + AO信号卖出")

run_fibonacci_trade(
    ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
    total_capital=2.0,
    check_interval=60
)
```

**Hermes输出**:
```
✅ Fibonacci交易已启动！
- 代币: FDBjQdN4...
- 总资金: 2.0 SOL
- 买入档位: 61.8%, 78.6%, 86.1%
- 卖出信号: AO绿转红
- 止损: 92%回撤

正在监控中...
```

---

### 示例2: RSI定投（多币）

**用户**:
```
同时定投这3个代币：
1. CA1，投入10 SOL，每次0.1
2. CA2，投入5 SOL，每次0.05
3. CA3，投入8 SOL，每次0.08
```

**Hermes识别**:
- 意图: `rsi_dca_multi`
- 参数: 3个DCAConfig

**Hermes生成代码**:
```python
import os
from trading import run_rsi_dca_multi, DCAConfig

if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

configs = [
    DCAConfig(ca="CA1", total_capital=10.0, buy_amount=0.1),
    DCAConfig(ca="CA2", total_capital=5.0, buy_amount=0.05),
    DCAConfig(ca="CA3", total_capital=8.0, buy_amount=0.08),
]

print("🚀 启动RSI多币定投...")
print(f"代币数量: {len(configs)}")
print(f"总资金: {sum(c.total_capital for c in configs)} SOL")

run_rsi_dca_multi(configs, check_interval=300)
```

**Hermes输出**:
```
✅ RSI多币定投已启动！
- 代币数量: 3个
- 总资金: 23.0 SOL
- 策略: RSI<30买入, RSI>70卖出
- 检查间隔: 5分钟

正在监控中...
```

---

### 示例3: AO监控（单币）

**用户**:
```
监控这个代币的AO信号：FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，买入价0.00004
```

**Hermes识别**:
- 意图: `ao_monitor`
- 参数: `ca="FDBjQdN4...", entry_price=0.00004`

**Hermes生成代码**:
```python
import os
from trading import run_ao_monitor

if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 请先设置 LOGEARN_API_KEY 环境变量")
    exit(1)

print("🚀 启动AO监控...")
print(f"代币: FDBjQdN4...")
print(f"买入价: 0.00004")
print(f"卖出策略:")
print(f"  - AO >= 35k 绿转红 → 立即卖出")
print(f"  - AO < 35k 绿转红 + 收益率 > 50% → 卖出")

run_ao_monitor(
    ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
    entry_price=0.00004,
    sell_percentage=1.0,
    check_interval=60
)
```

**Hermes输出**:
```
✅ AO监控已启动！
- 代币: FDBjQdN4...
- 买入价: 0.00004
- 卖出比例: 100%
- 检查间隔: 60秒

正在监控中...
```

---

## 🔧 错误处理

### Hermes应该处理的错误情况

#### 1. 缺少必需参数

**用户**:
```
帮我用Fibonacci交易
```

**Hermes应该回复**:
```
好的，我需要以下信息来启动Fibonacci交易：
1. 代币地址（CA）- 必需
2. 总资金（SOL）- 必需

请提供代币地址和投入金额。

示例：
"用Fibonacci交易这个代币：[CA地址]，投入2个SOL"
```

---

#### 2. 参数格式错误

**用户**:
```
监控这个代币：abc123，买入价xxx
```

**Hermes应该回复**:
```
❌ 参数格式错误：
- 代币地址应该是44个字符的Solana地址
- 买入价应该是数字（例如：0.00004）

请提供正确的参数。
```

---

#### 3. API Key未设置

**Hermes应该在代码中检查**:
```python
import os

if not os.getenv("LOGEARN_API_KEY"):
    print("❌ 错误：未设置 LOGEARN_API_KEY 环境变量")
    print("\n请先设置API Key：")
    print("export LOGEARN_API_KEY='your_api_key'")
    exit(1)
```

---

## 📊 总结

### Hermes调用流程
```
1. 用户输入
   ↓
2. 意图识别（Fibonacci/RSI/AO）
   ↓
3. 参数提取（CA/金额/买入价等）
   ↓
4. 参数验证（必需参数/格式检查）
   ↓
5. 生成Python代码
   ↓
6. 执行代码
   ↓
7. 输出结果
```

### 三大接口对应关系

| 用户意图 | 接口函数 | 关键参数 |
|---------|---------|---------|
| Fibonacci交易 | `run_fibonacci_trade()` | ca, total_capital |
| RSI定投（单币） | `run_rsi_dca()` | ca, total_capital, buy_amount |
| RSI定投（多币） | `run_rsi_dca_multi()` | configs[] |
| AO监控（单币） | `run_ao_monitor()` | ca, entry_price |
| AO监控（多币） | `run_ao_monitor_multi()` | configs[] |

---

**Hermes集成完整指南，让AI助手轻松调用交易接口！** 🎉
