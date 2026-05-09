# 快速参考指南

## 🚀 快速开始

### 运行测试
```bash
./run_tests.sh
```

### 使用配置
```python
from trading.config import DEFAULT_CONFIG, create_custom_config, AOConfig

# 使用默认配置
config = DEFAULT_CONFIG
print(config.ao.threshold_normal)  # 0.00003500

# 自定义配置
custom_config = create_custom_config(
    ao=AOConfig(threshold_normal=0.00005000)
)
```

---

## 📋 配置参数速查

### Fibonacci 配置
```python
fibonacci = FibonacciConfig(
    buy_ratios=[("buy_618", 0.618), ("buy_786", 0.786), ("buy_861", 0.861)],
    stop_ratio=0.920,
    sell_ratios=[("sell_100", 1.000), ("sell_1272", 1.272)],
    sell_percentages={"sell_100": 0.30, "sell_1272": 0.50},
    
    # ZIGZAG
    zigzag_deviation=5.0,
    zigzag_depth=10,
    zigzag_lookback=5,
    
    # 容差
    shallow_penetration_threshold=0.03,  # 3%
    shallow_tolerance=0.02,              # 2%
    deep_tolerance=0.05                  # 5%
)
```

### AO 配置
```python
ao = AOConfig(
    fast_period=5,
    slow_period=34,
    threshold_normal=0.00003500,  # 35k
    profit_threshold=0.50,        # 50%
    min_length=34,
    min_value_threshold=0.000001
)
```

### 仓位配置
```python
position = PositionConfig(
    max_position_ratio=0.30,  # 30%
    min_position_sol=0.005,
    tier_sizes={
        "buy_618": 0.03,  # 3%
        "buy_786": 0.02,  # 2%
        "buy_861": 0.01   # 1%
    },
    trading_start_hour=0,
    trading_end_hour=13
)
```

### 止盈配置
```python
profit = ProfitConfig(
    profit_target_50=0.50,
    profit_target_100=1.00,
    profit_50_sell_percentage=0.50,
    profit_100_sell_percentage=1.00
)
```

---

## 🔧 核心 API

### Fibonacci 计算器
```python
from trading.fib_calculator import (
    parse_klines,
    calc_ao,
    fib_entry_levels,
    fib_sell_levels,
    ao_sell_signal,
    fib_sell_signal,
    fib_signal
)

# 解析 K线
klines = parse_klines(raw_klines)

# 计算 AO
ao_values = calc_ao(klines)

# 计算 Fib 档位
levels = fib_entry_levels(swing_high=0.0001, swing_low=0.00005)
# {'buy_618': 0.0000691, 'buy_786': 0.0000607, 'buy_861': 0.0000569, 'stop': 0.000054}

# AO 卖出信号
signal = ao_sell_signal(ao_values, entry_price=0.00004, current_price=0.00006)
# {'action': 'sell', 'ao_value': 0.00004, 'threshold': 0.000035, 'reason': '...'}

# Fib 卖出信号
signal = fib_sell_signal(swing_high=0.0001, swing_low=0.00005, current_price=0.0001)
# {'action': 'fib_sell', 'tier': 'sell_100', 'percentage': 0.3, ...}

# 综合信号判断
signal = fib_signal(klines, entry_price=0.00004, tiers_bought=["buy_618"])
# {'action': 'buy_786'|'sell'|'stop'|'watch', ...}
```

### 仓位管理器
```python
from trading.position_manager import PositionManager

pm = PositionManager()

# 计算仓位
size = pm.calculate_position_size(total_capital=2.0, tier="buy_618")
# 0.06 SOL (3%)

# 检查是否可以买入
can_buy, reason = pm.can_buy(
    ca="token_address",
    amount_sol=0.05,
    total_capital=2.0,
    positions=[]
)

# 计算加权均价
avg_price = pm.calculate_weighted_avg_price(
    entry_prices={"buy_618": 0.00004, "buy_786": 0.00003},
    entry_amounts={"buy_618": 0.06, "buy_786": 0.04},
    tiers_bought=["buy_618", "buy_786"]
)
```

### 止盈止损管理器
```python
from trading.profit_manager import ProfitManager

pm = ProfitManager()

# 检查止盈
action = pm.check_profit_target(
    current_price=0.00006,
    avg_price=0.00004,
    profit_50_sold=False,
    ao_active=False
)
# ProfitAction(should_sell=True, percentage=0.5, reason='...', profit_rate=0.5)

# 检查 AO 卖出
should_sell, reason = pm.check_ao_sell_signal(
    ao_values=[...],
    entry_price=0.00004,
    current_price=0.00006
)

# 检查止损
should_stop, reason = pm.check_stop_loss(
    current_price=0.00003,
    stop_price=0.000035
)

# 检查 AO 是否启动
is_active = pm.is_ao_active(ao_values)
```

---

## 🎯 交易流程

### 1. 空仓 → 买入
```python
# 1. 获取 K线数据
klines = parse_klines(raw_klines)

# 2. 判断信号
signal = fib_signal(klines)

# 3. 买入执行
if signal.get("action") in ["buy_618", "buy_786", "buy_861"]:
    tier = signal["action"]
    price = signal["price"]
    
    # 计算买入金额
    amount = pm.calculate_position_size(total_capital, tier)
    
    # 检查是否可以买入
    can_buy, reason = pm.can_buy(ca, amount, total_capital, positions)
    
    if can_buy:
        # 执行买入
        executor.buy(ca, amount, limit_price=price)
        
        # 记录状态
        tiers_bought.append(tier)
        entry_swing_high = signal["swing_high"]
        entry_stop_price = signal["stop_price"]
```

### 2. 持仓 → 卖出
```python
# 1. 判断信号
signal = fib_signal(
    klines,
    entry_price=avg_price,
    tiers_bought=tiers_bought,
    entry_swing_high=entry_swing_high,
    entry_stop_price=entry_stop_price
)

# 2. 止损
if signal.get("action") == "stop":
    executor.sell(ca, percentage=1.0)  # 全部卖出

# 3. AO 卖出
elif signal.get("action") == "sell":
    executor.sell(ca, percentage=1.0)  # 全部卖出

# 4. Fib 卖出
elif signal.get("action") == "fib_sell":
    percentage = signal["percentage"]
    executor.sell(ca, percentage=percentage)  # 分批卖出
```

---

## 📊 信号返回格式

### 买入信号
```python
{
    "action": "buy_618"|"buy_786"|"buy_861",
    "price": 0.00006,
    "level": 0.00006,
    "penetrated": [],
    "pending": ["buy_786", "buy_861"],
    "swing_high": 0.0001,
    "stop_price": 0.000054
}
```

### 止损信号
```python
{
    "action": "stop",
    "price": 0.000053,
    "level": 0.000054
}
```

### AO 卖出信号
```python
{
    "action": "sell",
    "price": 0.00008,
    "level": 0.00008,
    "ao_value": 0.00004,
    "ao_threshold": 0.000035,
    "ao_reason": "ao≥35k绿转红"
}
```

### Fib 卖出信号
```python
{
    "action": "fib_sell",
    "tier": "sell_100"|"sell_1272",
    "percentage": 0.3|0.5,
    "price": 0.0001,
    "level": 0.0001,
    "reason": "价格触达 sell_100 位 0.00010000，卖出 30%"
}
```

### 观察信号
```python
{
    "action": "watch",
    "price": 0.00007,
    "levels": {...},
    "penetrated": [],
    "pending": []
}
```

---

## 🧪 测试

### 运行所有测试
```bash
./run_tests.sh
```

### 运行特定测试
```bash
# 配置测试
python3 -m unittest tests.test_config -v

# Fib 计算器测试
python3 -m unittest tests.test_fib_calculator -v

# 仓位管理测试
python3 -m unittest tests.test_position_manager -v

# 止盈止损测试
python3 -m unittest tests.test_profit_manager -v
```

### 运行单个测试用例
```bash
python3 -m unittest tests.test_config.TestAOConfig.test_default_values -v
```

---

## 📁 文件结构

```
trading/
├── __init__.py
├── config.py              # 配置管理
├── fib_calculator.py      # Fibonacci + AO 核心逻辑
├── position_manager.py    # 仓位管理
├── profit_manager.py      # 止盈止损管理
└── executor.py            # 交易执行器

tests/
├── __init__.py
├── test_config.py         # 配置测试
├── test_fib_calculator.py # Fib 计算器测试
├── test_position_manager.py # 仓位管理测试
└── test_profit_manager.py # 止盈止损测试

run_tests.sh               # 测试运行脚本
BUG_FIXES_AND_TESTS.md     # Bug 修复与测试报告
QUICK_REFERENCE.md         # 快速参考指南（本文件）
```

---

## 🔗 相关文档

- [Bug 修复与测试报告](BUG_FIXES_AND_TESTS.md)
- [交易逻辑梳理](README.md)
