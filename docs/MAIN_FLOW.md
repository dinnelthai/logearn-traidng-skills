# 主要功能流程图

## 概述

本项目对外提供**2个核心交易接口**，内部自动处理K线获取和交易执行。

---

## 🎯 整体架构

```mermaid
graph TB
    User[用户] --> API{选择交易策略}
    
    API -->|短线交易| Fib[run_fibonacci_trade]
    API -->|长期定投| RSI[run_rsi_dca]
    
    Fib --> FibBot[Fibonacci交易机器人]
    RSI --> RSIBot[RSI定投机器人]
    
    FibBot --> KlineService[K线服务<br/>5分钟K线]
    RSIBot --> KlineService2[K线服务<br/>1小时K线]
    
    KlineService --> LogEarnAPI[LogEarn API]
    KlineService2 --> LogEarnAPI
    
    FibBot --> Executor[交易执行器]
    RSIBot --> Executor
    
    Executor --> LogEarnCLI[LogEarn CLI]
    
    style API fill:#f9f,stroke:#333,stroke-width:4px
    style Fib fill:#bbf,stroke:#333,stroke-width:2px
    style RSI fill:#bfb,stroke:#333,stroke-width:2px
    style KlineService fill:#ffd,stroke:#333,stroke-width:1px
    style KlineService2 fill:#ffd,stroke:#333,stroke-width:1px
    style Executor fill:#fbb,stroke:#333,stroke-width:2px
```

---

## 📊 流程1: Fibonacci交易

### 1.1 整体流程

```mermaid
graph TB
    Start([用户调用<br/>run_fibonacci_trade]) --> Init[初始化机器人<br/>ca, total_capital]
    
    Init --> Loop{交易完成?}
    
    Loop -->|否| GetKline[获取5分钟K线<br/>自动调用LogEarn API]
    GetKline --> CalcFib[计算Fibonacci信号<br/>检测买入/卖出点]
    
    CalcFib --> CheckSignal{检测到信号?}
    
    CheckSignal -->|买入信号| BuyAction[执行买入<br/>61.8%/78.6%/86.1%]
    CheckSignal -->|卖出信号| SellAction[执行卖出<br/>AO信号/Fib档位]
    CheckSignal -->|无信号| Wait[等待check_interval]
    
    BuyAction --> UpdateState[更新状态<br/>tiers_bought, entry_prices]
    SellAction --> CheckComplete{全部卖出?}
    
    CheckComplete -->|是| Complete([交易完成<br/>停止机器人])
    CheckComplete -->|否| Wait
    UpdateState --> Wait
    Wait --> Loop
    
    Loop -->|是| Complete
    
    style Start fill:#bbf,stroke:#333,stroke-width:3px
    style Complete fill:#bfb,stroke:#333,stroke-width:3px
    style BuyAction fill:#fbb,stroke:#333,stroke-width:2px
    style SellAction fill:#fbf,stroke:#333,stroke-width:2px
```

### 1.2 买入流程详解

```mermaid
graph TB
    Start([检测到买入信号]) --> CheckTier{判断档位}
    
    CheckTier -->|61.8%| Buy618[买入618档<br/>3% 资金]
    CheckTier -->|78.6%| Buy786[买入786档<br/>15% 资金]
    CheckTier -->|86.1%| Buy861[买入861档<br/>12% 资金]
    
    Buy618 --> Validate[验证买入条件<br/>检查资金/持仓]
    Buy786 --> Validate
    Buy861 --> Validate
    
    Validate --> CanBuy{可以买入?}
    
    CanBuy -->|是| CalcAmount[计算买入金额<br/>position_size]
    CanBuy -->|否| Skip([跳过买入])
    
    CalcAmount --> Execute[调用TradeExecutor.buy<br/>执行买入]
    
    Execute --> Success{买入成功?}
    
    Success -->|是| Update[更新状态<br/>tiers_bought<br/>entry_prices<br/>entry_amounts]
    Success -->|否| Log[记录失败日志]
    
    Update --> End([继续监控])
    Log --> End
    Skip --> End
    
    style Start fill:#bbf,stroke:#333,stroke-width:2px
    style Execute fill:#fbb,stroke:#333,stroke-width:2px
    style Update fill:#bfb,stroke:#333,stroke-width:2px
```

### 1.3 卖出流程详解

```mermaid
graph TB
    Start([检测到卖出信号]) --> CheckType{信号类型}
    
    CheckType -->|AO卖出| AOSell[AO卖出<br/>全部卖出100%]
    CheckType -->|止损| StopLoss[止损<br/>全部卖出100%]
    CheckType -->|Fib卖出| FibSell[Fib卖出<br/>部分卖出30%]
    
    AOSell --> Execute[调用TradeExecutor.sell<br/>执行卖出]
    StopLoss --> Execute
    FibSell --> Execute
    
    Execute --> Success{卖出成功?}
    
    Success -->|是| CheckAmount{卖出比例}
    Success -->|否| Log[记录失败日志]
    
    CheckAmount -->|100%| Complete([标记交易完成<br/>停止机器人])
    CheckAmount -->|<100%| Update[更新状态<br/>fib_sold_tiers]
    
    Update --> Continue([继续监控])
    Log --> Continue
    
    style Start fill:#fbf,stroke:#333,stroke-width:2px
    style Execute fill:#fbb,stroke:#333,stroke-width:2px
    style Complete fill:#bfb,stroke:#333,stroke-width:3px
```

---

## 📈 流程2: RSI定投

### 2.1 整体流程

```mermaid
graph TB
    Start([用户调用<br/>run_rsi_dca]) --> Init[初始化机器人<br/>ca, dca_amount, max_buy_count]
    
    Init --> Loop{达到最大次数?}
    
    Loop -->|否| GetKline[获取1小时K线<br/>自动调用LogEarn API]
    GetKline --> CalcRSI[计算RSI指标<br/>14周期]
    
    CalcRSI --> CheckState{当前状态}
    
    CheckState -->|等待重置| CheckReset{RSI >= 50?}
    CheckState -->|可买入| CheckBuy{RSI < 30?}
    
    CheckReset -->|是| Reset[重置状态<br/>waiting_for_reset=False]
    CheckReset -->|否| Wait[等待check_interval<br/>默认300秒]
    
    CheckBuy -->|是| Buy[执行定投买入<br/>固定金额dca_amount]
    CheckBuy -->|否| Wait
    
    Reset --> Wait
    Buy --> UpdateCount[更新买入次数<br/>buy_count++]
    UpdateCount --> SetWait[设置等待状态<br/>waiting_for_reset=True]
    SetWait --> Wait
    
    Wait --> Loop
    
    Loop -->|是| Complete([定投完成<br/>停止机器人])
    
    style Start fill:#bfb,stroke:#333,stroke-width:3px
    style Complete fill:#bfb,stroke:#333,stroke-width:3px
    style Buy fill:#fbb,stroke:#333,stroke-width:2px
```

### 2.2 状态机

```mermaid
stateDiagram-v2
    [*] --> 可买入状态
    
    可买入状态 --> 等待重置状态: RSI < 30<br/>执行买入
    等待重置状态 --> 可买入状态: RSI >= 50<br/>重置状态
    
    可买入状态 --> 可买入状态: RSI >= 30<br/>继续等待
    等待重置状态 --> 等待重置状态: RSI < 50<br/>继续等待
    
    可买入状态 --> [*]: 达到最大次数
    等待重置状态 --> [*]: 达到最大次数
    
    note right of 可买入状态
        waiting_for_reset = False
        可以检测RSI并买入
    end note
    
    note right of 等待重置状态
        waiting_for_reset = True
        等待RSI回到50以上
    end note
```

### 2.3 买入时机示例

```
时间轴：
  ↓
RSI=28 < 30 → 买入（1/10）→ waiting_for_reset=True
  ↓
RSI=35 < 50 → 继续等待
  ↓
RSI=45 < 50 → 继续等待
  ↓
RSI=52 >= 50 → 重置状态 → waiting_for_reset=False
  ↓
RSI=55 >= 30 → 继续等待
  ↓
RSI=29 < 30 → 买入（2/10）→ waiting_for_reset=True
  ↓
...
  ↓
买入（10/10）→ 停止
```

---

## 🔧 内部模块交互

### 3.1 K线服务流程

```mermaid
graph LR
    Bot[交易机器人] --> KlineService[K线服务]
    
    KlineService --> BuildRequest[构建请求<br/>chain=3<br/>base=CA<br/>intervalTime<br/>pageSize]
    
    BuildRequest --> CallAPI[调用LogEarn API<br/>POST /get_kline_list]
    
    CallAPI --> ParseResponse[解析响应<br/>提取body数据]
    
    ParseResponse --> Convert[转换数据<br/>字符串→float<br/>添加market_cap]
    
    Convert --> Return[返回K线列表<br/>Kline对象]
    
    Return --> Bot
    
    style KlineService fill:#ffd,stroke:#333,stroke-width:2px
    style CallAPI fill:#bbf,stroke:#333,stroke-width:2px
```

### 3.2 交易执行流程

```mermaid
graph TB
    Bot[交易机器人] --> Executor[TradeExecutor]
    
    Executor --> CheckAction{操作类型}
    
    CheckAction -->|买入| BuildBuy[构建买入请求<br/>tokenIn=SOL<br/>tokenOut=CA<br/>amountIn=lamports]
    CheckAction -->|卖出| GetPosition[获取持仓<br/>查询token数量]
    
    GetPosition --> BuildSell[构建卖出请求<br/>tokenIn=CA<br/>tokenOut=SOL<br/>amountIn=token数量]
    
    BuildBuy --> CallCLI[调用LogEarn CLI<br/>log-swap]
    BuildSell --> CallCLI
    
    CallCLI --> ParseResult[解析结果<br/>检查code=200]
    
    ParseResult --> Success{成功?}
    
    Success -->|是| ReturnSuccess[返回成功<br/>TradeResult.success=True]
    Success -->|否| ReturnFail[返回失败<br/>TradeResult.success=False]
    
    ReturnSuccess --> Bot
    ReturnFail --> Bot
    
    style Executor fill:#fbb,stroke:#333,stroke-width:2px
    style CallCLI fill:#bbf,stroke:#333,stroke-width:2px
```

---

## 📋 数据流

### 4.1 Fibonacci交易数据流

```
用户输入
  ↓
ca: "代币地址"
total_capital: 2.0 SOL
check_interval: 60秒
  ↓
K线服务
  ↓
5分钟K线数据 (200根)
  ↓
Fibonacci计算
  ↓
买入信号: {action: "buy_618", price: 0.00005, tier: "618"}
  ↓
仓位管理
  ↓
买入金额: 0.06 SOL (3%)
  ↓
交易执行
  ↓
LogEarn CLI
  ↓
交易结果: {success: true, code: 200}
  ↓
状态更新
  ↓
tiers_bought: ["buy_618"]
entry_prices: {"buy_618": 0.00005}
entry_amounts: {"buy_618": 1200}
```

### 4.2 RSI定投数据流

```
用户输入
  ↓
ca: "代币地址"
dca_amount: 0.1 SOL
max_buy_count: 10
  ↓
K线服务
  ↓
1小时K线数据 (200根)
  ↓
RSI计算
  ↓
RSI值: 28.5
  ↓
判断逻辑
  ↓
RSI < 30 → 触发买入
  ↓
交易执行
  ↓
买入0.1 SOL
  ↓
状态更新
  ↓
buy_count: 1
waiting_for_reset: True
  ↓
继续监控
  ↓
等待RSI >= 50
```

---

## 🎯 关键决策点

### 5.1 Fibonacci交易决策树

```
获取K线
  ↓
计算Fibonacci档位
  ↓
检测信号
  ├─ 价格回撤到61.8% → 买入3%
  ├─ 价格回撤到78.6% → 买入15%
  ├─ 价格回撤到86.1% → 买入12%
  ├─ AO零轴上方绿转红 → 全部卖出
  ├─ 收益率>50% → 全部卖出
  ├─ 价格突破Fib档位 → 部分卖出30%
  └─ 跌破止损价 → 全部卖出
```

### 5.2 RSI定投决策树

```
获取K线
  ↓
计算RSI
  ↓
检查状态
  ├─ waiting_for_reset=False
  │   ├─ RSI < 30 → 买入 → 设置waiting_for_reset=True
  │   └─ RSI >= 30 → 继续等待
  └─ waiting_for_reset=True
      ├─ RSI >= 50 → 重置状态 → 设置waiting_for_reset=False
      └─ RSI < 50 → 继续等待
```

---

## 🔄 完整生命周期

### Fibonacci交易完整周期

```
1. 启动
   ↓
2. 初始化机器人
   ↓
3. 进入监控循环
   ├─ 获取5分钟K线
   ├─ 计算Fibonacci信号
   ├─ 检测买入信号 → 分批买入
   ├─ 检测卖出信号 → 分批卖出
   └─ 等待60秒
   ↓
4. 全部卖出
   ↓
5. 标记交易完成
   ↓
6. 停止机器人
```

### RSI定投完整周期

```
1. 启动
   ↓
2. 初始化机器人
   ↓
3. 进入监控循环
   ├─ 获取1小时K线
   ├─ 计算RSI
   ├─ RSI < 30 → 买入 → 等待重置
   ├─ RSI >= 50 → 重置状态
   └─ 等待300秒
   ↓
4. 达到最大次数
   ↓
5. 停止机器人
```

---

## 📊 总结

### 对外接口（2个）

1. **`run_fibonacci_trade(ca, total_capital, check_interval)`**
   - 短线交易
   - 5分钟K线
   - Fibonacci + AO策略

2. **`run_rsi_dca(ca, dca_amount, max_buy_count, check_interval)`**
   - 长期定投
   - 1小时K线
   - RSI策略

### 内部模块（自动处理）

1. **K线服务** - 自动获取K线数据
2. **技术指标** - 自动计算RSI、Fibonacci
3. **交易执行** - 自动调用LogEarn CLI
4. **状态管理** - 自动管理交易状态

### 核心优势

- ✅ **简单** - 只需传递CA地址
- ✅ **自动** - K线获取、交易执行全自动
- ✅ **可靠** - 完整的错误处理和日志
- ✅ **灵活** - 支持多种策略和参数配置
