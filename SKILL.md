---
name: logearn-trading-skills
description: LogEarn Solana Meme币交易技能库 — TradeExecutor / PositionManager / ProfitManager / FIB计算器 / AO指标。数据来源：signals_3x.db（684条历史信号）
triggers: [logearn-trading, trading-skills, 回测, backtest, fib, ao, 止盈止损]
version: 1.0.0
tags: [trading, solana, meme-coin, fibonacci, ao-indicator]
source: git@github.com:dinnelthai/logearn-traidng-skills.git
---

# logearn-trading-skills

Solana Meme币交易技能库，包含完整的交易执行、仓位管理、止盈止损逻辑。

## 核心模块

### 交易执行器 (TradeExecutor)
- `buy(ca, amount_sol, limit_price, current_price, slippage)` — 买入
- `sell(ca, percentage)` — 卖出（全部/部分）
- `get_positions()` — 获取持仓

### 仓位管理器 (PositionManager)
- `calculate_position_size(total_capital, tier)` — 计算档位买入金额
- `can_buy(ca, amount_sol, total_capital, positions)` — 检查可否买入
- `calculate_weighted_avg_price(...)` — 计算加权均价
- `get_position_value(positions, ca)` — 持仓市值

### 止盈止损管理器 (ProfitManager)
- `check_profit_target(...)` — 固定止盈（50%/100%）
- `check_ao_sell_signal(...)` — AO绿转红卖出
- `check_stop_loss(...)` — 止损检查
- `is_ao_active(ao_values)` — AO是否启动

### FIB计算器 (fib_calculator.py)
- `fib_entry_levels(swing_high, swing_low)` → `{buy_618, buy_786, buy_861, stop}` 价格
- `fib_sell_levels(swing_high, swing_low)` → `{sell_100, sell_1272}` 价格
- `calc_ao(klines)` → AO值列表
- `fib_signal(...)` → 买入/止损/AO卖出/FIB卖出信号
- `check_penetration_with_tolerance(...)` — 带容差的档位穿透判断

## 关键常量

```
BUY_RATIOS   = [("buy_618", 0.618), ("buy_786", 0.786), ("buy_861", 0.861)]
STOP_RATIO   = 0.920   # 止损：波峰 - 92% 回调
SELL_RATIOS  = [("sell_100", 1.000), ("sell_1272", 1.272)]
SELL_PCT     = {"sell_100": 0.30, "sell_1272": 0.50}
AO_THRESHOLD = 0.00003500 (35k)
AO_PROFIT_THRESHOLD = 0.50 (50%)
PROFIT_TARGET_50 = 0.50 (50%止盈)
PROFIT_TARGET_100 = 1.00 (100%止盈)
```

## 回测方法

```python
from backtest.backtester import Backtester
from trading.fib_calculator import BUY_RATIOS, STOP_RATIO, SELL_RATIOS

bt = Backtester()
result = bt.run(
    signal_data={        # 从 signals_3x.db 读取
        'swap_begin_time': unix_ts,
        'signal_price': float,   # 信号触发时的价格
        'low_price': float,      # 波谷
        'top_price': float,      # 波峰
        'max_price': float,      # 历史最高
        'max_up_ratio': float,   # 历史最大涨幅倍数
    }
)
# result: {win/total, avg_profit, exit_reasons: {ao/50%/100%/fib/stop}}
```
