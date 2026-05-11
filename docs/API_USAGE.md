# 对外开放接口使用指南

## 概述

本项目提供了一套完整的交易接口，支持Fibonacci交易、RSI定投等多种策略。

## 📦 安装

```bash
# 从GitHub安装最新版本
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@release/v0.1.0

# 或克隆后安装
git clone https://github.com/dinnelthai/logearn-traidng-skills.git
cd logearn-traidng-skills
git checkout release/v0.1.0
pip install -e .
```

## 🔑 环境变量

```bash
# 必需
export LOGEARN_API_KEY="你的API Key"

# 可选
export TOKEN_CA="代币地址"
export LOGEARN_API_BASE="https://logearn.com/logearn"
```

## 📚 核心接口

### 1. K线服务（统一数据获取）

#### 1.1 获取K线数据

```python
from trading import get_klines

# 获取5分钟K线（默认）
klines = get_klines("代币地址", interval='5m', page_size=200)

# 获取1小时K线
klines = get_klines("代币地址", interval='1h', page_size=200)

# 遍历K线
for kline in klines:
    print(f"时间: {kline.time}")
    print(f"开盘: {kline.open}")
    print(f"最高: {kline.high}")
    print(f"最低: {kline.low}")
    print(f"收盘: {kline.close}")
    print(f"成交量: {kline.volume}")
```

#### 1.2 获取原始K线数据

```python
from trading import get_klines_raw

# 获取原始字典格式
raw_klines = get_klines_raw("代币地址", interval='5m', page_size=200)

for kline in raw_klines:
    print(kline['time'])      # Unix时间戳
    print(kline['close'])     # 收盘价（SOL）
    print(kline['closeU'])    # 收盘价（USD）
```

#### 1.3 使用K线服务类

```python
from trading import KlineService

# 创建服务实例
service = KlineService()

# 获取K线
klines = service.get_klines("代币地址", interval='5m')

# 获取最新一根K线
latest = service.get_latest_kline("代币地址", interval='5m')

# 获取所有历史K线（翻页）
all_klines = service.get_all_klines("代币地址", interval='5m', max_pages=10)
```

**支持的周期**：`'1m'`, `'5m'`, `'15m'`, `'1h'`, `'1d'`

---

### 2. Fibonacci交易（单次交易）

#### 2.1 快捷运行

```python
from trading import run_single_trade, get_klines_raw

# K线提供函数
def klines_provider():
    return get_klines_raw("代币地址", interval='5m', page_size=200)

# 运行单次交易
run_single_trade(
    ca="代币地址",
    klines_provider=klines_provider,
    total_capital=2.0,      # 总资金2 SOL
    check_interval=60       # 每60秒检查一次
)
```

#### 2.2 使用机器人类

```python
from trading import SingleTradeBot, get_klines_raw

# 创建机器人
bot = SingleTradeBot(
    ca="代币地址",
    total_capital=2.0
)

# K线提供函数
def klines_provider():
    return get_klines_raw("代币地址", interval='5m', page_size=200)

# 运行
bot.run(klines_provider, check_interval=60)
```

**特点**：
- 自动检测Fibonacci回撤买入点（61.8%, 78.6%, 86.1%）
- 自动检测AO卖出信号
- 分批买入，分批卖出
- 全部卖出后自动停止

---

### 3. RSI定投（定投策略）

#### 3.1 快捷运行

```python
from trading import run_rsi_dca

# 运行RSI定投
run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,         # 每次定投0.1 SOL
    max_buy_count=10,       # 最多定投10次
    interval='1h',          # 1小时K线
    check_interval=300      # 每5分钟检查一次
)
```

#### 3.2 使用机器人类

```python
from trading import RSIDCABot

# 创建机器人
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
print(f"已买入: {status['buy_count']}")
```

**特点**：
- RSI < 30 时自动买入
- 买入后等待RSI > 50才能再次买入
- 固定金额定投
- 达到最大次数后自动停止

---

### 4. 技术指标计算

#### 4.1 RSI指标

```python
from trading import get_klines, calculate_rsi

# 获取K线
klines = get_klines("代币地址", interval='1h', page_size=200)

# 计算RSI
rsi = calculate_rsi(klines, period=14)
print(f"当前RSI: {rsi:.2f}")

# 计算RSI序列
from trading import calculate_rsi_series
rsi_values = calculate_rsi_series(klines, period=14)
```

#### 4.2 Fibonacci信号

```python
from trading import get_klines, fib_signal

# 获取K线
klines = get_klines("代币地址", interval='5m', page_size=200)

# 计算信号
signal = fib_signal(
    klines,
    entry_price=None,
    tiers_bought=[],
    pending_tiers=[],
    skip_ao=False
)

if signal:
    print(f"信号类型: {signal['action']}")
    print(f"价格: {signal.get('price')}")
```

---

### 5. 交易执行

#### 5.1 买入

```python
from trading import TradeExecutor

# 创建执行器（自动绑定钱包）
executor = TradeExecutor()

# 买入
result = executor.buy(
    ca="代币地址",
    amount_sol=0.1,
    current_price=0.00005
)

if result.success:
    print("买入成功")
else:
    print(f"买入失败: {result.message}")
```

#### 5.2 卖出

```python
from trading import TradeExecutor

executor = TradeExecutor()

# 卖出全部
result = executor.sell(
    ca="代币地址",
    percentage=1.0
)

# 卖出50%
result = executor.sell(
    ca="代币地址",
    percentage=0.5
)

if result.success:
    print("卖出成功")
```

#### 5.3 查询持仓

```python
from trading import TradeExecutor

executor = TradeExecutor()

# 获取持仓
positions = executor.get_positions()

for pos in positions:
    print(f"代币: {pos['token_address']}")
    print(f"持仓: {pos['hold_amount']}")
```

---

### 6. 交易检测（回测）

#### 6.1 检测单次交易

```python
from trading.trade_checker import check_single_trade
from trading import get_klines

# 获取K线
klines = get_klines("代币地址", interval='5m', page_size=200)

# 检测交易
result = check_single_trade(
    klines=klines,
    total_capital=2.0
)

if result['matched']:
    print("✅ 检测到完整交易")
    print(f"买入点: {len(result['buy_points'])}")
    print(f"卖出点: {len(result['sell_points'])}")
    print(f"利润: {result['profit']['profit_sol']} SOL")
else:
    print("❌ 未检测到完整交易")
```

#### 6.2 分析多次交易

```python
from trading.win_rate_analyzer import analyze_token_trades
from trading import get_klines_raw

# 获取原始K线
raw_klines = get_klines_raw("代币地址", interval='5m', page_size=200)

# 分析交易
result = analyze_token_trades(
    ca="代币地址",
    raw_klines=raw_klines,
    total_capital=2.0,
    max_trades=5
)

print(f"交易次数: {len(result['trades'])}")
print(f"胜率: {result['win_rate']*100:.1f}%")
```

---

## 🎯 完整使用示例

### 示例1: Fibonacci交易（5分钟K线）

```python
#!/usr/bin/env python3
import os
from trading import run_single_trade, get_klines_raw

# 配置
CA = os.getenv("TOKEN_CA", "代币地址")
TOTAL_CAPITAL = 2.0
CHECK_INTERVAL = 60

# K线提供函数
def klines_provider():
    return get_klines_raw(CA, interval='5m', page_size=200)

# 运行
if __name__ == "__main__":
    run_single_trade(
        ca=CA,
        klines_provider=klines_provider,
        total_capital=TOTAL_CAPITAL,
        check_interval=CHECK_INTERVAL
    )
```

### 示例2: RSI定投（1小时K线）

```python
#!/usr/bin/env python3
import os
from trading import run_rsi_dca

# 配置
CA = os.getenv("TOKEN_CA", "代币地址")
DCA_AMOUNT = 0.1
MAX_BUY_COUNT = 10

# 运行
if __name__ == "__main__":
    run_rsi_dca(
        ca=CA,
        dca_amount=DCA_AMOUNT,
        max_buy_count=MAX_BUY_COUNT,
        interval='1h',
        check_interval=300
    )
```

### 示例3: 自定义策略

```python
#!/usr/bin/env python3
from trading import (
    get_klines, calculate_rsi, fib_signal,
    TradeExecutor
)

# 初始化
ca = "代币地址"
executor = TradeExecutor()

# 获取K线
klines = get_klines(ca, interval='5m', page_size=200)

# 计算指标
rsi = calculate_rsi(klines, period=14)
signal = fib_signal(klines, entry_price=None, tiers_bought=[])

# 交易逻辑
if rsi < 30 and signal and signal['action'].startswith('buy'):
    print(f"买入信号: RSI={rsi:.2f}, Fib={signal['action']}")
    result = executor.buy(ca=ca, amount_sol=0.1, current_price=klines[0].close)
    if result.success:
        print("买入成功")
```

---

## 📋 接口参数说明

### K线服务参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ca` | str | - | 代币地址（必需） |
| `interval` | str | `'5m'` | K线周期 |
| `page_size` | int | `200` | 返回K线数量 |
| `end_time` | int | None | 结束时间（翻页用） |

### Fibonacci交易参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ca` | str | - | 代币地址（必需） |
| `klines_provider` | function | - | K线提供函数（必需） |
| `total_capital` | float | `2.0` | 总资金（SOL） |
| `check_interval` | int | `60` | 检查间隔（秒） |

### RSI定投参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ca` | str | - | 代币地址（必需） |
| `dca_amount` | float | - | 每次定投金额（必需） |
| `max_buy_count` | int | - | 最大定投次数（必需） |
| `interval` | str | `'1h'` | K线周期 |
| `check_interval` | int | `300` | 检查间隔（秒） |
| `rsi_period` | int | `14` | RSI周期 |
| `rsi_buy_threshold` | float | `30.0` | RSI买入阈值 |
| `rsi_reset_threshold` | float | `50.0` | RSI重置阈值 |

---

## 🔧 命令行使用

### 1. 运行Fibonacci交易

```bash
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"

python example_single_trade.py
```

### 2. 运行RSI定投

```bash
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"

python example_rsi_dca.py
```

### 3. 测试K线服务

```bash
python -m trading.kline_service 代币地址 5m 10
```

### 4. 测试RSI定投

```bash
python -m trading.rsi_dca_bot 代币地址 0.1 10 1h
```

---

## 📖 相关文档

- [安装指南](INSTALL.md)
- [K线服务使用指南](KLINE_SERVICE_GUIDE.md)
- [RSI定投使用指南](RSI_DCA_GUIDE.md)
- [单次交易使用指南](SINGLE_TRADE_GUIDE.md)
- [交易流程说明](TRADING_PROCESS.md)

---

## ❓ 常见问题

### Q1: 如何修改K线周期？

```python
# Fibonacci交易使用5分钟K线
klines = get_klines_raw(ca, interval='5m')

# RSI定投使用1小时K线
run_rsi_dca(ca=ca, dca_amount=0.1, max_buy_count=10, interval='1h')
```

### Q2: 如何查看交易日志？

所有机器人都会自动输出实时日志到控制台。

### Q3: 如何停止机器人？

按 `Ctrl+C` 手动停止，或等待交易完成后自动停止。

### Q4: 如何处理错误？

```python
try:
    run_single_trade(ca=ca, klines_provider=klines_provider)
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"运行错误: {e}")
```

### Q5: 如何在多个代币上同时运行？

每个代币启动一个独立的进程：

```bash
# 终端1
export TOKEN_CA="代币1"
python example_single_trade.py

# 终端2
export TOKEN_CA="代币2"
python example_rsi_dca.py
```

---

## 🎉 总结

本项目提供了完整的交易接口：

1. ✅ **K线服务** - 统一的数据获取接口
2. ✅ **Fibonacci交易** - 自动化单次交易
3. ✅ **RSI定投** - 智能定投策略
4. ✅ **技术指标** - RSI、Fibonacci等
5. ✅ **交易执行** - 买入、卖出、查询持仓
6. ✅ **交易检测** - 回测和分析

所有接口都经过测试，可直接使用！
