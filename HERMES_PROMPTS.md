# Hermes Agent 提示语指南

## 🤖 如何让Hermes执行AO监控

### 基础提示语模板

#### 1. 启动单个代币监控

```
帮我启动AO监控，监控这个代币：
- 代币地址: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump
- 买入价: 0.00004
- 卖出比例: 100%
```

或者简化版：
```
监控这个CA的AO信号: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，买入价0.00004
```

---

#### 2. 启动多个代币监控

```
帮我同时监控这些代币的AO信号：
1. CA: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，买入价 0.00004
2. CA: 另一个代币地址，买入价 0.00005
3. CA: 第三个代币地址，买入价未知（保守模式）
```

---

#### 3. 不提供买入价（保守模式）

```
监控这个代币的AO信号，不提供买入价：
CA: 代币地址
```

---

#### 4. 部分卖出

```
监控这个代币，AO触发时只卖出50%：
- CA: 代币地址
- 买入价: 0.00004
- 卖出比例: 50%
```

---

### 高级提示语

#### 5. 自定义检查间隔

```
启动AO监控，每30秒检查一次：
- CA: 代币地址
- 买入价: 0.00004
- 检查间隔: 30秒
```

---

#### 6. 使用不同K线周期

```
用15分钟K线监控这个代币的AO：
- CA: 代币地址
- 买入价: 0.00004
- K线周期: 15m
```

---

### 管理提示语

#### 7. 查看监控状态

```
检查AO监控是否在运行
```

或：
```
显示当前监控的代币列表
```

---

#### 8. 停止监控

```
停止AO监控
```

或：
```
停止监控这个代币: 代币地址
```

---

## 📋 完整对话示例

### 示例1: 简单启动

**你**:
```
帮我监控这个代币的AO信号: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，买入价0.00004
```

**Hermes应该执行**:
```python
from trading import run_ao_monitor

run_ao_monitor(
    ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
    entry_price=0.00004,
    sell_percentage=1.0
)
```

---

### 示例2: 多代币监控

**你**:
```
同时监控这3个代币：
1. FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump，买入价0.00004
2. 另一个CA，买入价0.00005
3. 第三个CA，不知道买入价
```

**Hermes应该执行**:
```python
from trading import run_ao_monitor_multi, AOMonitorConfig

configs = [
    AOMonitorConfig(
        ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
        entry_price=0.00004,
        sell_percentage=1.0
    ),
    AOMonitorConfig(
        ca="另一个CA",
        entry_price=0.00005,
        sell_percentage=1.0
    ),
    AOMonitorConfig(
        ca="第三个CA",
        entry_price=None,
        sell_percentage=1.0
    ),
]

run_ao_monitor_multi(configs)
```

---

### 示例3: 查询持仓后启动监控

**你**:
```
查看我的持仓，然后对所有持仓启动AO监控
```

**Hermes应该执行**:
```python
from trading import TradeExecutor, run_ao_monitor_multi, AOMonitorConfig

# 1. 获取持仓
executor = TradeExecutor()
positions = executor.get_positions()

# 2. 为每个持仓创建监控配置
configs = []
for pos in positions:
    ca = pos.get("token_address")
    # 可以从持仓信息中获取last_price作为参考
    configs.append(AOMonitorConfig(
        ca=ca,
        entry_price=None,  # 如果不知道买入价
        sell_percentage=1.0
    ))

# 3. 启动监控
run_ao_monitor_multi(configs)
```

---

## 🎯 关键词触发

Hermes应该在检测到以下关键词时触发AO监控skill：

### 中文关键词
- `AO监控`
- `监控AO`
- `AO信号`
- `自动卖出`
- `接管持仓`
- `绿转红`
- `AO卖出`

### 英文关键词
- `ao monitor`
- `monitor ao`
- `ao signal`
- `auto sell`
- `take over position`

### 组合关键词
- `监控 + 代币地址`
- `AO + 卖出`
- `自动 + 卖出`

---

## ⚙️ 参数提取规则

Hermes应该从用户输入中提取以下参数：

### 1. 代币地址 (ca)
**识别模式**:
- `CA: xxx`
- `代币地址: xxx`
- `token: xxx`
- 直接的Solana地址（44个字符）

### 2. 买入价 (entry_price)
**识别模式**:
- `买入价: 0.00004`
- `entry price: 0.00004`
- `成本价: 0.00004`
- `买入均价: 0.00004`
- `不知道买入价` → `None`
- `买入价未知` → `None`

### 3. 卖出比例 (sell_percentage)
**识别模式**:
- `卖出100%` → `1.0`
- `卖出50%` → `0.5`
- `全部卖出` → `1.0`
- `部分卖出` → 需要询问具体比例
- 默认 → `1.0`

### 4. K线周期 (interval)
**识别模式**:
- `5分钟` → `'5m'`
- `15分钟` → `'15m'`
- `1小时` → `'1h'`
- 默认 → `'5m'`

### 5. 检查间隔 (check_interval)
**识别模式**:
- `每30秒` → `30`
- `每1分钟` → `60`
- `每2分钟` → `120`
- 默认 → `60`

---

## 🔍 错误处理提示

### 缺少必需参数

**用户**:
```
帮我启动AO监控
```

**Hermes应该回复**:
```
好的，我需要以下信息来启动AO监控：
1. 代币地址（CA）
2. 买入价（可选，不提供则使用保守模式）
3. 卖出比例（默认100%）

请提供代币地址。
```

---

### 确认参数

**Hermes应该确认**:
```
我将为您启动AO监控：
- 代币: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump
- 买入价: 0.00004
- 卖出比例: 100%
- K线周期: 5分钟
- 检查间隔: 60秒

卖出条件：
- AO >= 35k 绿转红 → 立即卖出
- AO < 35k 绿转红 + 收益率 > 50% → 卖出

确认启动吗？
```

---

## 📝 状态反馈

### 启动成功

**Hermes应该输出**:
```
✅ AO监控已启动！

监控信息：
- 代币数量: 2个
- 检查间隔: 60秒
- K线周期: 5分钟

监控中的代币：
1. FDBjQdN4... (买入价: 0.00004)
2. 另一个CA... (保守模式)

按 Ctrl+C 可随时停止监控
```

---

### 监控运行中

**Hermes应该输出**:
```
🔍 正在监控...

[60秒后]
✅ 检查完成，未触发卖出信号

[继续监控...]
```

---

### 触发卖出

**Hermes应该输出**:
```
🔔 AO卖出信号触发！

代币: FDBjQdN4...
原因: ao≥35k绿转红
AO值: 0.00003800
当前价: 0.00006
收益率: 50.00%

📉 执行卖出 100%...
✅ 卖出成功！

进度: 1/2
```

---

## 🚀 快速参考

### 最简单的启动方式

```
监控这个CA: 代币地址，买入价0.00004
```

### 最完整的启动方式

```
启动AO监控：
- CA: 代币地址
- 买入价: 0.00004
- 卖出比例: 100%
- K线周期: 5分钟
- 检查间隔: 60秒
```

### 批量启动

```
监控这些代币：
CA1, 买入价0.00004
CA2, 买入价0.00005
CA3, 买入价未知
```

---

**使用这些提示语，Hermes就能正确理解并执行AO监控功能！** 🎉
