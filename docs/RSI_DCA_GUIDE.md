# RSI定投机器人使用指南

## 概述

RSI定投机器人是一个基于RSI（相对强弱指标）的自动定投工具。当RSI跌破30时自动买入，买入后等待RSI回到50以上才能再次买入，达到最大次数后自动停止。

## 核心逻辑

```
初始状态
  ↓
RSI < 30 → 买入（1/10）→ 等待RSI > 50
  ↓
RSI = 35 < 50 → 继续等待
  ↓
RSI = 52 > 50 → 重置状态，可再次买入
  ↓
RSI < 30 → 买入（2/10）→ 等待RSI > 50
  ↓
...
  ↓
买入（10/10）→ 停止
```

## 特点

1. ✅ **简单直接**：只监控RSI，无需复杂信号
2. ✅ **定投策略**：固定金额，降低风险
3. ✅ **状态控制**：买入后等待RSI回到50
4. ✅ **灵活周期**：支持1分钟、5分钟、15分钟、1小时、1天K线
5. ✅ **次数限制**：达到最大次数后自动停止
6. ✅ **无卖出**：只买入，不管卖出

## 使用方式

### 方法1: 命令行运行

```bash
# 设置环境变量
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"

# 运行
python example_rsi_dca.py
```

### 方法2: Python调用

```python
from trading.rsi_dca_bot import run_rsi_dca

run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,      # 每次定投0.1 SOL
    max_buy_count=10,    # 最多定投10次
    interval='1h',       # 1小时K线
    check_interval=300   # 每5分钟检查一次
)
```

### 方法3: 使用RSIDCABot类

```python
from trading.rsi_dca_bot import RSIDCABot

# 初始化
bot = RSIDCABot(
    ca="代币地址",
    dca_amount=0.1,
    max_buy_count=10,
    rsi_period=14,
    rsi_buy_threshold=30.0,
    rsi_reset_threshold=50.0
)

# 运行
bot.run(interval='1h', check_interval=300)

# 查看状态
status = bot.get_status()
print(f"进度: {status['progress']}")
print(f"最后RSI: {status['last_rsi']}")
```

## 参数说明

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `ca` | str | 代币地址 | `"FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump"` |
| `dca_amount` | float | 每次定投金额（SOL） | `0.1` |
| `max_buy_count` | int | 最大定投次数 | `10` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `interval` | str | `'1h'` | K线周期（'1m', '5m', '15m', '1h', '1d'） |
| `check_interval` | int | `300` | 检查间隔（秒） |
| `rsi_period` | int | `14` | RSI周期 |
| `rsi_buy_threshold` | float | `30.0` | RSI买入阈值 |
| `rsi_reset_threshold` | float | `50.0` | RSI重置阈值 |

## K线周期说明

| 周期 | 说明 | 适用场景 |
|------|------|----------|
| `'1m'` | 1分钟 | 超短线，快速响应 |
| `'5m'` | 5分钟 | 短线交易 |
| `'15m'` | 15分钟 | 短线交易（推荐） |
| `'1h'` | 1小时 | 中线交易（推荐） |
| `'1d'` | 1天 | 长线投资 |

## 工作流程

### 1. 启动阶段

```
启动机器人
  ↓
设置参数（代币地址、定投金额、最大次数）
  ↓
初始化交易执行器
  ↓
开始监控
```

### 2. 监控阶段

```
每5分钟（check_interval）
  ↓
获取K线数据（从LogEarn API）
  ↓
计算RSI（14周期）
  ↓
判断状态
```

### 3. 买入判断

```
if waiting_for_reset:
    if RSI >= 50:
        重置状态 → 可再次买入
    else:
        继续等待
else:
    if RSI < 30:
        执行买入 → 设置waiting_for_reset=True
    else:
        继续监控
```

### 4. 停止条件

```
if buy_count >= max_buy_count:
    停止机器人
```

## 运行示例

### 示例1: 1小时K线，定投10次

```bash
export TOKEN_CA="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump"
export LOGEARN_API_KEY="sk_xxx"

python -c "
from trading.rsi_dca_bot import run_rsi_dca
run_rsi_dca(
    ca='FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump',
    dca_amount=0.1,
    max_buy_count=10,
    interval='1h'
)
"
```

### 示例2: 15分钟K线，定投5次

```python
from trading.rsi_dca_bot import run_rsi_dca

run_rsi_dca(
    ca="代币地址",
    dca_amount=0.05,     # 每次0.05 SOL
    max_buy_count=5,     # 最多5次
    interval='15m',      # 15分钟K线
    check_interval=180   # 每3分钟检查
)
```

### 示例3: 自定义RSI阈值

```python
from trading.rsi_dca_bot import RSIDCABot

bot = RSIDCABot(
    ca="代币地址",
    dca_amount=0.2,
    max_buy_count=20,
    rsi_period=14,
    rsi_buy_threshold=25.0,   # RSI < 25时买入
    rsi_reset_threshold=60.0  # RSI > 60时重置
)

bot.run(interval='1h', check_interval=300)
```

## 日志输出

机器人会实时输出运行日志：

```
================================================================================
🤖 RSI定投机器人启动
================================================================================
代币地址: FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump
定投金额: 0.1 SOL
最大次数: 10
RSI周期: 14
买入阈值: RSI < 30.0
重置阈值: RSI > 50.0
K线周期: 1h
检查间隔: 300秒
================================================================================

[2026-05-11 18:30:00] 获取K线数据...
  ✅ 获取200根K线
  📊 当前RSI: 28.50
  🎯 触发买入条件: RSI(28.50) < 30.0

  📈 RSI定投买入
     RSI: 28.50
     价格: 0.00005000 SOL
     金额: 0.1 SOL
     次数: 1/10
     ✅ 买入成功
  📈 定投进度: 1/10

[2026-05-11 18:35:00] 获取K线数据...
  ✅ 获取200根K线
  📊 当前RSI: 35.20
  ⏳ 等待RSI回到50.0以上...
  📈 定投进度: 1/10

[2026-05-11 18:40:00] 获取K线数据...
  ✅ 获取200根K线
  📊 当前RSI: 52.30
  ✅ RSI回到50.0以上(52.30)，可以再次买入
  📈 定投进度: 1/10

...

================================================================================
🎉 定投完成！总共买入10次
================================================================================
```

## 注意事项

### 1. 环境变量

必须设置以下环境变量：
```bash
export LOGEARN_API_KEY="你的API Key"
export TOKEN_CA="代币地址"  # 可选，可在代码中指定
```

### 2. K线数量

- RSI计算至少需要 `rsi_period + 1` 根K线
- 默认获取200根K线，足够计算RSI
- 如果K线不足，会报错

### 3. 检查间隔

- 建议设置为5分钟（300秒）
- 太短会频繁请求API
- 太长会错过买入机会

### 4. 买入次数

- 达到 `max_buy_count` 后自动停止
- 不会超过设定次数
- 可以随时手动停止（Ctrl+C）

### 5. 状态重置

- 买入后必须等待 RSI > 50 才能再次买入
- 这期间即使RSI再次跌破30也不会买入
- 确保每次买入之间有足够的间隔

## 常见问题

### Q1: 如何修改定投金额？

修改 `dca_amount` 参数：
```python
run_rsi_dca(ca="...", dca_amount=0.2, max_buy_count=10)  # 改为0.2 SOL
```

### Q2: 如何修改RSI阈值？

使用 `RSIDCABot` 类：
```python
bot = RSIDCABot(
    ca="...",
    dca_amount=0.1,
    max_buy_count=10,
    rsi_buy_threshold=25.0,   # 改为25
    rsi_reset_threshold=60.0  # 改为60
)
```

### Q3: 如何查看当前进度？

使用 `get_status()` 方法：
```python
status = bot.get_status()
print(f"进度: {status['progress']}")  # 输出: 3/10
print(f"已买入: {status['buy_count']}")
print(f"等待重置: {status['waiting_for_reset']}")
```

### Q4: 如何停止机器人？

- 按 `Ctrl+C` 手动停止
- 达到最大次数后自动停止
- 发生错误时会自动重试

### Q5: 买入失败怎么办？

- 机器人会记录失败日志
- 不会增加买入次数
- 继续监控，等待下次机会

## 与Fibonacci交易机器人的区别

| 特性 | RSI定投 | Fibonacci交易 |
|------|---------|---------------|
| 策略 | RSI < 30定投 | Fibonacci回撤 + AO |
| 买入 | 固定金额 | 分档位买入 |
| 卖出 | 无 | 自动卖出 |
| 次数 | 限制次数 | 单次完整交易 |
| 适用 | 长期定投 | 短期交易 |

## 总结

RSI定投机器人是一个简单有效的定投工具：

1. ✅ **简单策略**：只监控RSI，无需复杂判断
2. ✅ **自动执行**：自动买入，无需人工干预
3. ✅ **风险控制**：固定金额，限制次数
4. ✅ **状态管理**：买入后等待重置，避免频繁交易
5. ✅ **灵活配置**：支持多种K线周期和参数

适合长期看好某个代币，想要定投建仓的场景！
