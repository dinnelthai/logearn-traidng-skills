# 主要交易流程

## 概述

主交易逻辑采用 **Fibonacci 回撤 + AO (Awesome Oscillator)** 策略，通过分析K线数据自动检测买入和卖出信号。

## 核心流程

### 1. 信号检测流程 (fib_signal)

```
K线数据 → ZigZag检测波峰 → 计算Fibonacci档位 → 检测信号
```

#### 步骤详解

1. **ZigZag检测波峰**
   - 使用 ZigZag 算法检测价格波峰和波谷
   - 参数：deviation=5.0%, depth=10, lookback=5
   - 返回：swing_high（波峰）、swing_low（波谷）

2. **计算Fibonacci档位**
   - 基于波峰和波谷计算买入档位：
     - buy_618: 61.8% 回撤
     - buy_786: 78.6% 回撤
     - buy_861: 86.1% 回撤
   - 计算止损档位：stop: 92.0% 回撤
   - 计算卖出档位：
     - sell_100: 100% 回到波峰（卖出30%）
     - sell_1272: 127.2% 扩展位（卖出50%）

3. **检测信号**
   - **买入信号**：价格穿透Fibonacci买入档位
   - **止损信号**：价格穿透止损档位（仅持仓时）
   - **AO卖出信号**：AO指标触发卖出（优先级最高）
   - **Fib卖出信号**：价格回到卖出档位

### 2. 买入流程

```
检测到买入信号 → 检查仓位 → 计算买入金额 → 执行买入
```

#### 步骤详解

1. **检测买入信号**
   - 价格穿透 buy_618、buy_786 或 buy_861 档位
   - 确认穿透：最低价触及档位 + 收盘价回升

2. **检查仓位**
   - 检查是否已买入该档位
   - 检查剩余仓位是否足够
   - 检查总资金是否充足

3. **计算买入金额**
   - 总仓位比例：30% of 总资金
   - 档位分配：
     - buy_618: 50% of 仓位
     - buy_786: 25% of 仓位
     - buy_861: 25% of 仓位
   - 最小买入金额：0.005 SOL

4. **执行买入**
   - 调用 TradeExecutor.buy()
   - 通过 LogEarn CLI 执行交易
   - 记录买入信息（价格、时间、档位）

### 3. 卖出流程

```
持仓中 → 检测卖出信号 → 执行卖出 → 计算利润
```

#### 步骤详解

1. **AO卖出信号（优先级最高）**
   - AO > 35k 且绿转红 → 全部卖出
   - AO < 35k 且收益率 > 50% → 全部卖出
   - AO触发后忽略Fib卖出信号

2. **Fib卖出信号**
   - 价格回到 100%（波峰）→ 卖出30%
   - 价格达到 127.2% → 卖出50%
   - 每个档位只触发一次

3. **止损信号**
   - 价格穿透 92.0% 止损档位 → 全部卖出
   - 止损价在买入时锁定，持仓期间不下移

4. **执行卖出**
   - 调用 TradeExecutor.sell()
   - 通过 LogEarn CLI 执行交易
   - 记录卖出信息（价格、时间、类型）

### 4. 仓位管理

```
买入 → 更新仓位状态 → 持仓监控 → 卖出 → 重置仓位
```

#### 状态变量

- `tiers_bought`: 已买入的档位列表
- `entry_prices`: 各档位的买入价格
- `entry_amounts`: 各档位的买入数量
- `pending_tiers`: 待买入的档位列表
- `entry_swing_high`: 买入时锁定的波峰
- `entry_stop_price`: 买入时锁定的止损价
- `fib_sold_tiers`: 已通过Fib卖出的档位列表

#### 仓位计算

- **加权均价**: Σ(价格 × 数量) / Σ数量
- **总持仓**: Σ各档位数量
- **剩余仓位**: 最大仓位 - 当前持仓

## 交易检测流程 (check_single_trade)

### 输入

- K线数据列表
- 总资金
- 交易配置

### 输出

```python
{
    "matched": True/False,  # 是否匹配到完整交易
    "buy_points": [...],    # 买入点列表
    "sell_points": [...],   # 卖出点列表
    "profit": {...},       # 利润信息
}
```

### 处理逻辑

1. **初始化**
   - 创建 PositionManager
   - 初始化状态变量
   - 初始化记录变量

2. **逐根K线遍历**
   - 传递从头开始的所有K线给 fib_signal
   - 计算加权均价
   - 检测信号
   - 根据信号执行买入/卖出

3. **买入处理**
   - 检查是否可以买入
   - 计算买入金额
   - 记录买入点
   - 更新状态变量

4. **卖出处理**
   - 记录卖出点
   - 计算利润
   - 更新累计卖出比例

5. **返回结果**
   - 买入点列表
   - 卖出点列表
   - 利润信息
   - 是否匹配完整交易

## 关键参数

### Fibonacci配置

- **买入档位**: 0.618, 0.786, 0.861
- **卖出档位**: 1.000, 1.272
- **止损**: 0.920
- **ZigZag参数**: deviation=5.0, depth=10, lookback=5

### AO配置

- **快速周期**: 5
- **慢速周期**: 34
- **卖出阈值**: 35k
- **收益率阈值**: 50%

### 仓位配置

- **最大仓位比例**: 30%
- **最小买入金额**: 0.005 SOL
- **档位大小**: buy_618=3%, buy_786=2%, buy_861=1%

### 交易时间

- **交易窗口**: 24小时（无时间限制）

## 数据流

```
K线数据
  ↓
parse_klines → Kline对象
  ↓
check_single_trade
  ↓
fib_signal (每根K线)
  ↓
  ├─ _swing_from_klines (ZigZag)
  ├─ fib_entry_levels (Fib档位)
  ├─ ao_sell_signal (AO卖出)
  └─ check_fib_sell (Fib卖出)
  ↓
PositionManager (仓位管理)
  ↓
TradeExecutor (真实交易执行)
```

## 特殊逻辑

### 1. 穿透确认

- **浅插针**: 插针 < 3% + 收盘回升 > 2%
- **深插针**: 插针 >= 3% + 收盘回升 >= 5%
- **假突破**: 收盘回升 > 6% 不算穿透

### 2. 档位锁定

- 买入时锁定波峰和止损价
- 持仓期间波峰不下移
- 止损价不上移

### 3. AO优先级

- AO卖出信号优先级最高
- AO触发后忽略Fib卖出信号
- AO未启动时使用固定止盈

### 4. 分批卖出

- Fib卖出支持分批
- 每个档位只触发一次
- 累计卖出比例跟踪

## 模块职责

### fib_calculator.py

- ZigZag波峰检测
- Fibonacci档位计算
- 买入/卖出/止损信号检测
- AO指标计算

### position_manager.py

- 仓位计算
- 买入金额计算
- 加权均价计算
- 交易时间检查

### trade_checker.py

- 交易检测入口
- 信号处理
- 买入/卖出记录
- 利润计算

### executor.py

- 真实交易执行
- LogEarn CLI调用
- 交易结果返回

## 使用示例

```python
from trading.trade_checker import check_single_trade
from trading.fib_calculator import parse_klines

# 解析K线
klines = parse_klines(raw_klines)

# 检测交易
result = check_single_trade(
    klines=klines,
    total_capital=2.0
)

# 查看结果
if result['matched']:
    print(f"买入点: {len(result['buy_points'])}")
    print(f"卖出点: {len(result['sell_points'])}")
    print(f"利润: {result['profit']['profit_sol']} SOL")
```
