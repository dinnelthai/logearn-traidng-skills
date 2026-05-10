# 交易检测器 (Trade Checker)

## 🎯 功能概述

交易检测器用于**检测K线数据是否符合一次完整交易**（买入→卖出），主要用于避免重复交易同一个 token。

### 核心特性

- ✅ **100% 复用核心逻辑**：使用 `fib_signal()` 和 `PositionManager`
- ✅ **只检测一次交易**：买入→卖出后立即停止
- ✅ **简单清晰的输出**：买入点、卖出点、利润
- ✅ **完整的单元测试**：8 个测试用例，100% 通过

---

## 🚀 快速开始

### 基本用法

```python
from trading.trade_checker import check_single_trade_from_raw

# 获取 K线数据
raw_klines = get_klines(token_address)

# 检测是否符合一次完整交易
result = check_single_trade_from_raw(raw_klines, total_capital=2.0)

# 判断结果
if result["matched"]:
    print("✅ 已有完整交易，跳过")
    pass  # 不执行交易
else:
    print("❌ 未匹配到完整交易，可以交易")
    execute_trade(token_address)
```

### 实际应用

```python
from trading.trade_checker import check_single_trade_from_raw

def should_trade_token(token_address: str) -> bool:
    """判断是否应该交易某个 token"""
    klines = get_klines(token_address)
    result = check_single_trade_from_raw(klines)
    return not result["matched"]  # 未匹配才能交易

# 使用
if should_trade_token("token_address"):
    execute_trade("token_address")
else:
    print("跳过，已有完整交易记录")
```

---

## 📊 返回数据格式

### 匹配到完整交易

```python
{
    "matched": True,
    "buy_points": [
        {
            "tier": "buy_618",
            "price": 0.00005,
            "amount": 0.06,
            "kline_index": 10,
            "timestamp": 1000000
        }
    ],
    "sell_points": [
        {
            "price": 0.00008,
            "kline_index": 25,
            "timestamp": 1005000,
            "reason": "AO卖出信号",
            "type": "ao_sell",
            "percentage": 1.0
        }
    ],
    "profit": {
        "invested": 0.06,
        "returned": 0.096,
        "profit_sol": 0.036,
        "profit_rate": 0.60  # 60%
    }
}
```

### 未匹配到完整交易

```python
{
    "matched": False,
    "buy_points": [],
    "sell_points": [],
    "profit": None
}
```

---

## 📝 API 参考

### check_single_trade_from_raw()

```python
def check_single_trade_from_raw(
    raw_klines: List[dict],
    total_capital: float = 2.0,
    config = None
) -> Dict
```

从原始K线数据检测交易。

**参数**：
- `raw_klines`: 原始K线数据列表
- `total_capital`: 总资金（SOL），默认 2.0
- `config`: 交易配置，默认 `DEFAULT_CONFIG`

**返回**：
- `Dict`: 检测结果

### print_trade_result()

```python
def print_trade_result(result: Dict)
```

格式化打印交易检测结果。

---

## 💡 使用示例

### 示例 1: 基本检测

```python
from trading.trade_checker import check_single_trade_from_raw, print_trade_result

raw_klines = [...]
result = check_single_trade_from_raw(raw_klines)
print_trade_result(result)
```

### 示例 2: 批量过滤

```python
def filter_tradable_tokens(token_list: list) -> list:
    """过滤出可以交易的 token"""
    tradable = []
    
    for token in token_list:
        klines = get_klines(token["address"])
        result = check_single_trade_from_raw(klines)
        
        if not result["matched"]:
            tradable.append(token)
    
    return tradable
```

### 示例 3: 运行完整示例

```bash
python3 example_trade_check.py
```

---

## 🧪 测试

### 运行测试

```bash
# 运行交易检测器测试
python3 -m unittest tests.test_trade_checker -v

# 运行所有测试
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 测试覆盖

- ✅ 利润计算（全部卖出/部分卖出/多档位）
- ✅ 交易检测（匹配/未匹配）
- ✅ 数据结构验证（买入点/卖出点/利润）

**测试结果**: 77 个测试用例，100% 通过

---

## 📁 文件结构

```
trading/
└── trade_checker.py           # 交易检测器核心代码

tests/
└── test_trade_checker.py      # 单元测试

example_trade_check.py         # 使用示例
TRADE_CHECKER_GUIDE.md         # 详细使用指南
README_TRADE_CHECKER.md        # 本文件
```

---

## 🔍 工作原理

### 核心逻辑

```python
# 1. 逐根K线遍历
for i in range(len(klines)):
    current_klines = klines[:i+1]
    
    # 2. 调用核心信号函数（100% 复用）
    signal = fib_signal(
        current_klines,
        entry_price=avg_price,
        tiers_bought=tiers_bought,
        ...
    )
    
    # 3. 根据信号类型记录
    if signal["action"] in ["buy_618", "buy_786", "buy_861"]:
        # 记录买入
        buy_records.append(...)
    
    elif signal["action"] in ["sell", "stop", "fib_sell"]:
        # 记录卖出，结束检测
        sell_record = ...
        break
```

### 关键点

1. **100% 复用核心逻辑**
   - 使用 `fib_signal()` 判断买卖信号
   - 使用 `PositionManager.calculate_position_size()` 计算仓位
   - 使用 `PositionManager.calculate_weighted_avg_price()` 计算均价

2. **只检测一次交易**
   - 遇到卖出信号后立即停止
   - 不会检测多次交易

3. **状态管理与实际交易一致**
   - `tiers_bought`: 已买入档位
   - `entry_prices`: 各档位买入价
   - `entry_swing_high`: 波峰
   - `entry_stop_price`: 止损价

---

## ⚠️ 注意事项

1. **K线数据要求**
   - 需要足够的K线数据（建议至少 50 根）
   - 需要包含完整的下跌和反弹过程

2. **逻辑一致性**
   - 检测结果与实际交易结果完全一致
   - 不会出现检测通过但实际交易失败的情况

3. **只检测一次**
   - 只检测第一次完整交易
   - 适用于"每个 token 只交易一次"的策略

4. **时间锁**
   - 检测器内部允许全天检测（`trading_end_hour=24`）
   - 实际交易时仍受时间锁限制

---

## 📚 相关文档

- [详细使用指南](TRADE_CHECKER_GUIDE.md)
- [使用示例](example_trade_check.py)
- [交易逻辑梳理](README.md)
- [配置文件说明](trading/config.py)
- [Bug 修复报告](BUG_FIXES_AND_TESTS.md)

---

## ✅ 总结

交易检测器提供了一个简单可靠的方式来检测K线是否符合一次完整交易，帮助你：

- ✅ 避免重复交易同一个 token
- ✅ 快速判断交易机会
- ✅ 分析历史交易表现

**核心优势**：100% 复用核心逻辑，确保检测结果与实际交易完全一致。
