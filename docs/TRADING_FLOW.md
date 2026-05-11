# 核心交易逻辑流程图

## 整体流程

```mermaid
graph TD
    A[开始] --> B[获取K线数据]
    B --> C[解析K线 parse_klines]
    C --> D[检测波峰 _swing_from_klines]
    D --> E{检测到波峰?}
    E -->|否| F[继续下一根K线]
    F --> D
    E -->|是| G[计算Fibonacci档位 calc_fib_levels]
    G --> H[检测买入信号 fib_signal]
    H --> I{触发买入?}
    I -->|否| J[继续下一根K线]
    J --> H
    I -->|是| K[仓位管理 calculate_position_size]
    K --> L[执行买入 TradeExecutor.buy]
    L --> M[监控卖出信号]
    M --> N{触发卖出?}
    N -->|否| O[继续监控]
    O --> M
    N -->|是| P[执行卖出 TradeExecutor.sell]
    P --> Q[计算利润]
    Q --> R[结束]
```

## 详细流程

### 1. 信号检测流程

```mermaid
graph TD
    A[开始检测] --> B[获取最新K线]
    B --> C[更新K线窗口]
    C --> D{K线数 >= 10?}
    D -->|否| E[等待更多K线]
    E --> B
    D -->|是| F[ZigZag检测波峰]
    F --> G{检测到新波峰?}
    G -->|是| H[锁定波峰价格]
    H --> I[计算Fibonacci档位]
    I --> J[计算止损价]
    J --> K[继续检测]
    G -->|否| K
    K --> L{当前价格穿透Fib档位?}
    L -->|是| M[触发买入信号]
    L -->|否| N{当前价格穿透止损价?}
    N -->|是| O[触发止损信号]
    N -->|否| P[检测AO卖出信号]
    P --> Q{AO触发卖出?}
    Q -->|是| R[触发AO卖出]
    Q -->|否| S{价格回到波峰?}
    S -->|是| T[触发Fib卖出]
    S -->|否| U[继续监控]
    U --> B
```

### 2. Fibonacci档位计算

```mermaid
graph LR
    A[波峰价格] --> B[计算61.8%档位]
    A --> C[计算78.6%档位]
    A --> D[计算86.1%档位]
    A --> E[计算止损92.0%]
    B --> F[buy_618]
    C --> G[buy_786]
    D --> H[buy_861]
    E --> I[stop]
```

### 3. 仓位管理流程

```mermaid
graph TD
    A[触发买入信号] --> B{已持仓?}
    B -->|否| C[检查总资金]
    C --> D[计算买入金额]
    D --> E{金额 >= 最小仓位?}
    E -->|否| F[跳过买入]
    E -->|是| G[计算代币数量]
    G --> H[执行买入]
    B -->|是| I{已买入该档位?}
    I -->|是| F
    I -->|否| J[检查剩余仓位]
    J --> K[计算买入金额]
    K --> H
```

### 4. 卖出信号检测

```mermaid
graph TD
    A[持仓中] --> B[计算AO值]
    B --> C{AO > 35k?}
    C -->|是| D{绿转红?}
    D -->|是| E[触发AO卖出]
    D -->|否| F[检查收益率]
    F --> G{收益率 > 50%?}
    G -->|是| E
    G -->|否| H[检查Fib卖出]
    C -->|否| H
    H --> I{价格回到100%?}
    I -->|是| J[触发Fib卖出]
    I -->|否| K{价格达到127.2%?}
    K -->|是| J
    K -->|否| L{价格穿透止损?}
    L -->|是| M[触发止损]
    L -->|否| N[继续监控]
    N --> A
```

### 5. 真实交易执行流程

```mermaid
graph TD
    A[交易信号] --> B{买入信号?}
    B -->|是| C[调用LogEarn CLI]
    C --> D[执行SOL代币交换]
    D --> E{交易成功?}
    E -->|是| F[记录买入信息]
    E -->|否| G[记录错误日志]
    G --> H[重试或放弃]
    B -->|否| I{卖出信号?}
    I -->|是| J[调用LogEarn CLI]
    J --> K[执行代币SOL交换]
    K --> L{交易成功?}
    L -->|是| M[记录卖出信息]
    L -->|否| N[记录错误日志]
    N --> H
    I -->|否| O[继续监控]
```

## 核心模块说明

### 1. fib_calculator.py
- **功能**: Fibonacci回撤计算和信号检测
- **核心函数**:
  - `parse_klines`: 解析原始K线数据
  - `_swing_from_klines`: ZigZag检测波峰波谷
  - `calc_fib_levels`: 计算Fibonacci档位
  - `fib_signal`: 检测买入/卖出信号

### 2. position_manager.py
- **功能**: 仓位管理和买入金额计算
- **核心函数**:
  - `calculate_position_size`: 计算买入金额
  - `check_can_buy`: 检查是否可以买入
  - `check_trading_hours`: 检查交易时间窗口

### 3. profit_manager.py
- **功能**: 利润管理和卖出信号检测
- **核心函数**:
  - `check_profit_target`: 检查利润目标
  - `check_ao_sell_signal`: 检测AO卖出信号
  - `check_stop_loss`: 检查止损

### 4. executor.py
- **功能**: 真实交易执行
- **核心函数**:
  - `buy`: 执行买入操作
  - `sell`: 执行卖出操作
  - `_logearn_swap`: 调用LogEarn CLI进行交易

### 5. trade_checker.py
- **功能**: 交易检测和过滤
- **核心函数**:
  - `check_single_trade`: 检测单次交易
  - `filter_klines_by_market_cap`: 市值过滤

### 6. win_rate_analyzer.py
- **功能**: 胜率分析和多次交易分析
- **核心函数**:
  - `analyze_token_trades`: 分析多次交易
  - `split_trades_by_sell_points`: 分割交易周期

## 数据流向

```
K线数据 → parse_klines → Kline对象
                ↓
        filter_klines_by_market_cap (可选)
                ↓
        _swing_from_klines (ZigZag)
                ↓
        calc_fib_levels (Fibonacci档位)
                ↓
        fib_signal (信号检测)
                ↓
        calculate_position_size (仓位管理)
                ↓
        TradeExecutor (真实交易执行)
                ↓
        ProfitManager (利润管理)
```

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

### 市值配置
- **市值门槛**: 180k USD
- **交易时间**: 24小时（无限制）
