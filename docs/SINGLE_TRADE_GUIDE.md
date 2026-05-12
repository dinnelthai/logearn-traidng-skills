# 单次交易使用指南

## 概述

本指南展示如何使用交易接口实现**只在一个币上开仓关仓交易一次就停止**。

## 方法1: 使用 SingleTradeBot（推荐）

### 特点
- ✅ 自动检测买入卖出信号
- ✅ 自动执行交易
- ✅ 交易完成后自动停止
- ✅ 支持分批买入和分批卖出

### 使用步骤

#### 1. 设置环境变量

```bash
export WALLET_ADDRESS="你的钱包地址"
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"
```

#### 2. 运行单次交易

```bash
python example_single_trade.py
```

#### 3. 代码示例

```python
from trading.single_trade_bot import run_single_trade

# 定义K线数据提供函数
def get_klines():
    # 从API获取K线数据
    # 返回格式: List[dict]
    return fetch_klines_from_api(ca)

# 运行单次交易
run_single_trade(
    wallet="你的钱包地址",
    ca="代币地址",
    klines_provider=get_klines,
    total_capital=2.0,      # 总资金 2 SOL
    check_interval=60       # 每60秒检查一次
)
```

### 工作流程

```
启动机器人
    ↓
获取K线数据
    ↓
检测信号
    ↓
买入信号? → 执行买入 → 更新状态
    ↓
卖出信号? → 执行卖出 → 检查是否全部卖出
    ↓
全部卖出? → 标记交易完成 → 停止机器人
    ↓
继续监控...
```

## 方法2: 手动调用交易接口

### 特点
- ✅ 完全手动控制
- ✅ 适合自定义策略
- ⚠️ 需要自己管理状态

### 代码示例

```python
from trading.executor import TradeExecutor
from trading.fib_calculator import parse_klines, fib_signal
from trading.position_manager import PositionManager

# 初始化
executor = TradeExecutor(wallet="你的钱包地址")
position_manager = PositionManager()

# 状态变量
tiers_bought = []
entry_prices = {}
entry_amounts = {}
trade_completed = False

# 获取K线
raw_klines = fetch_klines(ca)
klines = parse_klines(raw_klines)

# 检测信号
signal = fib_signal(
    klines,
    entry_price=None,
    tiers_bought=tiers_bought,
    pending_tiers=[],
    skip_ao=False
)

# 处理买入信号
if signal and signal.get("action") in ["buy_618", "buy_786", "buy_861"]:
    action = signal["action"]
    
    # 计算买入金额
    buy_amount = position_manager.calculate_position_size(
        tier=action,
        total_capital=2.0
    )
    
    # 执行买入
    result = executor.buy(
        ca=ca,
        amount_sol=buy_amount,
        current_price=klines[-1].close
    )
    
    if result.success:
        print("✅ 买入成功")
        tiers_bought.append(action)
        entry_prices[action] = klines[-1].close
        entry_amounts[action] = buy_amount / klines[-1].close

# 处理卖出信号
if signal and signal.get("action") in ["sell", "stop"]:
    # 执行卖出（全部）
    result = executor.sell(
        ca=ca,
        percentage=1.0  # 全部卖出
    )
    
    if result.success:
        print("✅ 卖出成功")
        trade_completed = True  # 标记交易完成
```

## 方法3: 使用 check_single_trade 检测

### 特点
- ✅ 适合回测和分析
- ✅ 不执行真实交易
- ✅ 返回完整交易信息

### 代码示例

```python
from trading.trade_checker import check_single_trade
from trading.fib_calculator import parse_klines

# 获取K线
raw_klines = fetch_klines(ca)
klines = parse_klines(raw_klines)

# 检测一次完整交易
result = check_single_trade(
    klines=klines,
    total_capital=2.0
)

# 检查结果
if result['matched']:
    print("✅ 检测到完整交易")
    print(f"买入点: {len(result['buy_points'])}")
    print(f"卖出点: {len(result['sell_points'])}")
    print(f"利润: {result['profit']['profit_sol']} SOL")
    
    # 根据检测结果手动执行交易
    # ...
else:
    print("❌ 未检测到完整交易")
```

## 关键参数说明

### SingleTradeBot 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `wallet` | str | - | 钱包地址（必需） |
| `ca` | str | - | 代币地址（必需） |
| `total_capital` | float | 2.0 | 总资金（SOL） |
| `check_interval` | int | 60 | 检查间隔（秒） |

### 交易执行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `amount_sol` | float | - | 买入金额（SOL） |
| `percentage` | float | 1.0 | 卖出比例（0-1） |
| `slippage` | float | 0.02 | 滑点容忍度 |

## 交易流程

### 1. 买入流程

```
检测买入信号
    ↓
检查是否可以买入
    ↓
计算买入金额
    ↓
执行买入
    ↓
更新状态（tiers_bought, entry_prices, entry_amounts）
```

### 2. 卖出流程

```
检测卖出信号
    ↓
确定卖出比例
    ↓
执行卖出
    ↓
检查是否全部卖出
    ↓
全部卖出 → 标记交易完成
```

## 注意事项

### 1. 环境变量

必须设置以下环境变量：
- `LOGEARN_API_KEY`: LogEarn API密钥
- `WALLET_ADDRESS`: 钱包地址（可选，可在代码中指定）

### 2. K线数据

K线数据格式要求：
```python
[
    {
        "time": 1778338500,
        "open": 3.0102516e-08,
        "high": 6.2482795e-08,
        "low": 3.0102516e-08,
        "close": 4.1256067e-08,
        "volume": 98.066454773,
        "market_cap": 3.8327  # 可选
    },
    ...
]
```

### 3. 交易完成条件

交易完成的条件：
- ✅ 已买入任意档位
- ✅ 已全部卖出（sell_percentage >= 1.0）

### 4. 自动停止

机器人会在以下情况自动停止：
- ✅ 交易完成（全部卖出）
- ✅ 用户中断（Ctrl+C）
- ❌ 发生异常错误

## 常见问题

### Q1: 如何修改买入金额？

修改 `total_capital` 参数：
```python
run_single_trade(
    wallet=wallet,
    ca=ca,
    klines_provider=get_klines,
    total_capital=5.0  # 改为5 SOL
)
```

### Q2: 如何修改检查间隔？

修改 `check_interval` 参数：
```python
run_single_trade(
    wallet=wallet,
    ca=ca,
    klines_provider=get_klines,
    check_interval=30  # 改为30秒
)
```

### Q3: 如何查看交易日志？

机器人会自动打印交易日志：
```
📈 买入信号: buy_618
   价格: 0.00005000 SOL
   金额: 0.0300 SOL
   ✅ 买入成功

📉 卖出信号: AO卖出
   价格: 0.00008000 SOL
   比例: 100%
   ✅ 卖出成功

🎉 交易完成！
```

### Q4: 如何处理交易失败？

机器人会自动处理交易失败：
- 买入失败：跳过本次买入，继续监控
- 卖出失败：跳过本次卖出，继续监控

### Q5: 如何获取K线数据？

需要实现 `klines_provider` 函数，从API获取K线数据。示例：
```python
def get_klines():
    import requests
    url = f"https://api.example.com/klines/{ca}"
    response = requests.get(url)
    return response.json()["klines"]
```

## 完整示例

```python
#!/usr/bin/env python3
import os
from trading.single_trade_bot import run_single_trade

# 配置
WALLET = os.getenv("WALLET_ADDRESS")
CA = "代币地址"
TOTAL_CAPITAL = 2.0
CHECK_INTERVAL = 60

# K线提供函数
def get_klines():
    # 从API获取K线
    return fetch_klines_from_api(CA)

# 运行
if __name__ == "__main__":
    run_single_trade(
        wallet=WALLET,
        ca=CA,
        klines_provider=get_klines,
        total_capital=TOTAL_CAPITAL,
        check_interval=CHECK_INTERVAL
    )
```

## 总结

使用 `SingleTradeBot` 可以轻松实现**只交易一次就停止**的需求：

1. ✅ 自动检测买入卖出信号
2. ✅ 自动执行交易
3. ✅ 交易完成后自动停止
4. ✅ 支持分批买入和分批卖出
5. ✅ 完整的日志输出

只需要提供K线数据，机器人会自动完成整个交易流程！
