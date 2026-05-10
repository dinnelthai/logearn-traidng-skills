# Bug 修复报告：Fib 分批卖出逻辑错误

## 📋 Bug 描述

### 问题位置
`trading/trade_checker.py` 第 138-160 行

### 严重程度
🔴 **严重** - 导致利润计算错误和交易记录丢失

### 问题详情

在 Fib 卖出逻辑中，代码使用单个 `sell_record` 变量记录卖出信息。当发生多次 Fib 分批卖出时（例如先在 sell_100 卖出 30%，后在 sell_1272 卖出 50%），后续的卖出会**覆盖**之前的记录，导致：

1. **丢失交易记录**：只保留最后一次卖出，之前的卖出记录全部丢失
2. **利润计算错误**：`_calculate_profit()` 只使用最后一次的价格和比例，忽略了之前的卖出

### 根本原因

Fib 卖出规则设计为**分批卖出**：
- `sell_100`（回到波峰）→ 卖出 30%
- `sell_1272`（127.2% 扩展）→ 卖出 50%

但代码实现时使用了单个变量而非列表来存储卖出记录。

---

## ✅ 修复方案

### 1. 数据结构变更

**变更前：**
```python
sell_record = None  # 单个卖出记录
```

**变更后：**
```python
sell_records = []  # 支持多次卖出（Fib分批卖出）
total_sell_percentage = 0.0  # 累计卖出比例
```

### 2. 卖出逻辑修复

#### AO 卖出（全部卖出）
```python
elif action == "sell":
    sell_records.append({
        "price": signal.get("price"),
        "kline_index": i,
        "timestamp": klines[i].time,
        "reason": signal.get("ao_reason", "AO卖出信号"),
        "type": "ao_sell",
        "percentage": 1.0  # AO卖出全部
    })
    total_sell_percentage = 1.0
    break
```

#### 止损（全部卖出）
```python
elif action == "stop":
    sell_records.append({
        "price": signal.get("price"),
        "kline_index": i,
        "timestamp": klines[i].time,
        "reason": "触发止损",
        "type": "stop_loss",
        "percentage": 1.0  # 止损全部卖出
    })
    total_sell_percentage = 1.0
    break
```

#### Fib 卖出（分批卖出）
```python
elif action == "fib_sell":
    percentage = signal.get("percentage", 0.3)
    tier = signal.get("tier", "")
    
    # 记录 Fib 卖出
    sell_records.append({
        "price": signal.get("price"),
        "kline_index": i,
        "timestamp": klines[i].time,
        "reason": signal.get("reason", "Fib卖出信号"),
        "type": "fib_sell",
        "percentage": percentage,
        "tier": tier
    })
    
    # 标记已卖出档位
    fib_sold_tiers.append(tier)
    
    # 累计卖出比例
    total_sell_percentage += percentage
    
    # 如果累计卖出 >= 100%，结束交易
    if total_sell_percentage >= 1.0:
        break
    # 否则继续（可能还有后续卖出）
```

### 3. 新增利润计算函数

添加 `_calculate_profit_multi_sell()` 函数支持多次卖出：

```python
def _calculate_profit_multi_sell(entry_prices: Dict[str, float],
                                  entry_amounts: Dict[str, float],
                                  tiers_bought: List[str],
                                  sell_records: List[Dict]) -> Dict:
    """
    计算利润（支持多次分批卖出）
    
    Args:
        entry_prices: 各档位买入价格
        entry_amounts: 各档位买入金额
        tiers_bought: 已买入档位
        sell_records: 卖出记录列表，每条记录包含 price 和 percentage
    
    Returns:
        Dict: 利润信息
    """
    # 计算总投入
    total_invested = sum(entry_amounts[tier] for tier in tiers_bought)
    
    # 计算总持仓 tokens
    total_tokens = sum(
        entry_amounts[tier] / entry_prices[tier]
        for tier in tiers_bought
    )
    
    # 计算所有卖出的总回报
    total_returned = 0.0
    total_sell_percentage = 0.0
    
    for sell in sell_records:
        sell_price = sell.get("price", 0)
        sell_percentage = sell.get("percentage", 0)
        
        # 计算本次卖出的 tokens 和回报
        tokens_sold = total_tokens * sell_percentage
        returned = tokens_sold * sell_price
        total_returned += returned
        total_sell_percentage += sell_percentage
    
    # 计算利润（基于已卖出部分）
    # 投入成本按卖出比例分摊
    invested_for_sold = total_invested * total_sell_percentage
    profit_sol = total_returned - invested_for_sold
    profit_rate = profit_sol / invested_for_sold if invested_for_sold > 0 else 0.0
    
    return {
        "invested": total_invested,  # 总投入
        "invested_for_sold": invested_for_sold,  # 已卖出部分的投入
        "returned": total_returned,  # 总回报
        "profit_sol": profit_sol,  # 利润
        "profit_rate": profit_rate,  # 收益率
        "sell_percentage": total_sell_percentage  # 总卖出比例
    }
```

### 4. API 变更

**返回值变更：**
```python
# 变更前
return {
    "matched": True,
    "buy_points": buy_records,
    "sell_point": sell_record,  # 单数
    "profit": profit
}

# 变更后
return {
    "matched": True,
    "buy_points": buy_records,
    "sell_points": sell_records,  # 复数，列表
    "profit": profit
}
```

### 5. 打印函数更新

更新 `print_trade_result()` 以支持显示多次卖出：

```python
# 卖出点（支持多次卖出）
sell_points = result.get("sell_points", [])
if sell_points:
    print("📈 卖出点:")
    for i, sell in enumerate(sell_points, 1):
        print(f"  {i}. {sell['type']}")
        print(f"     价格: {sell['price']:.8f}")
        print(f"     比例: {sell.get('percentage', 1.0)*100:.0f}%")
        print(f"     K线: #{sell['kline_index']}")
        print(f"     原因: {sell['reason']}")
        if sell.get('tier'):
            print(f"     档位: {sell['tier']}")
```

---

## 🧪 测试验证

### 单元测试
添加了新的测试用例 `test_calculate_profit_multi_sell()`：

```python
def test_calculate_profit_multi_sell(self):
    """测试多次分批卖出的利润计算"""
    entry_prices = {"buy_618": 0.00005}
    entry_amounts = {"buy_618": 0.06}
    tiers_bought = ["buy_618"]
    
    # 模拟两次卖出：
    # 1. 在 0.00008 卖出 30%
    # 2. 在 0.00010 卖出 50%
    sell_records = [
        {"price": 0.00008, "percentage": 0.30},
        {"price": 0.00010, "percentage": 0.50}
    ]
    
    profit = _calculate_profit_multi_sell(
        entry_prices, entry_amounts, tiers_bought, sell_records
    )
    
    # 验证结果
    self.assertAlmostEqual(profit["invested"], 0.06, places=4)
    self.assertAlmostEqual(profit["invested_for_sold"], 0.048, places=4)
    self.assertAlmostEqual(profit["returned"], 0.0888, places=4)
    self.assertAlmostEqual(profit["profit_sol"], 0.0408, places=4)
    self.assertAlmostEqual(profit["profit_rate"], 0.85, places=2)
    self.assertAlmostEqual(profit["sell_percentage"], 0.80, places=2)
```

### 测试结果
```
✅ 所有 9 个测试用例通过
```

---

## 📊 影响范围

### 修改的文件
1. `trading/trade_checker.py` - 核心修复
2. `tests/test_trade_checker.py` - 测试更新

### 向后兼容性
⚠️ **破坏性变更**：API 返回值从 `sell_point`（单数）改为 `sell_points`（复数列表）

**需要更新的调用代码：**
```python
# 旧代码
sell = result["sell_point"]

# 新代码
sell_points = result["sell_points"]
sell = sell_points[0]  # 获取第一次卖出
```

---

## 📝 修复前后对比

### 场景：买入后先触发 sell_100（30%），再触发 sell_1272（50%）

#### 修复前 ❌
- **记录**：只保留 sell_1272 的卖出记录，sell_100 记录丢失
- **利润计算**：只基于 sell_1272 的价格和 50% 比例
- **结果**：利润计算错误，无法追溯完整交易过程

#### 修复后 ✅
- **记录**：保留两次卖出记录
  - 第 1 次：sell_100，30%
  - 第 2 次：sell_1272，50%
- **利润计算**：基于两次卖出的加权平均
  - 总卖出比例：80%
  - 总回报：第1次回报 + 第2次回报
  - 收益率：基于已卖出部分的投入计算
- **结果**：准确记录和计算

---

## ✨ 总结

这个 bug 修复确保了：
1. ✅ 完整记录所有 Fib 分批卖出
2. ✅ 准确计算多次卖出的利润
3. ✅ 支持任意次数的分批卖出
4. ✅ 保持代码与交易规则一致
5. ✅ 通过完整的单元测试验证

修复后的代码能够正确处理 Fib 卖出策略的分批卖出逻辑，确保交易记录完整和利润计算准确。

---

# Bug 修复报告 #2：AO "watch" 信号误判为卖出

## 📋 Bug 描述

### 问题位置
`trading/fib_calculator.py` 第 470-480 行

### 严重程度
🔴 **严重** - 可能导致错误的卖出操作

### 问题详情

`ao_sell_signal()` 函数在某些情况下返回 `{"action": "watch", ...}`（当 AO < 35k 绿转红但没有持仓价格信息时）。

但在 `fib_signal()` 中使用 `if sell:` 来判断是否有卖出信号：

```python
sell = ao_sell_signal(ao_values, entry_price=entry_price, current_price=latest_close)
if sell:  # ❌ Bug: 非空字典都为 True
    return {"action": "sell", ...}
```

**问题**：Python 中非空字典为 `True`，所以 `{"action": "watch"}` 也会被判断为真，导致：
1. ❌ "watch" 信号被当作 "sell" 信号处理
2. ❌ 触发错误的卖出操作

### 触发条件

当同时满足以下条件时触发：
1. AO 绿转红
2. AO 值 < 35k
3. `entry_price` 为 `None`（没有持仓价格信息）

---

## ✅ 修复方案

### 修复代码

```python
# 修复前
sell = ao_sell_signal(ao_values, entry_price=entry_price, current_price=latest_close)
if sell:  # ❌ 会误判 {"action": "watch"} 为真
    return {"action": "sell", ...}

# 修复后
sell = ao_sell_signal(ao_values, entry_price=entry_price, current_price=latest_close)
if sell and sell.get("action") == "sell":  # ✅ 明确检查 action
    return {"action": "sell", ...}
```

### 修复位置

`trading/fib_calculator.py:471`

---

## 🧪 测试验证

创建了专门的测试 `test_ao_watch_bug.py` 验证修复：

```python
# 测试场景：AO < 35k 绿转红，但没有持仓价格
result = fib_signal(
    klines,
    entry_price=None,  # 没有持仓价格
    tiers_bought=["buy_618"],
    skip_ao=False,
    ...
)

# 验证：不应触发卖出
assert result.get("action") != "sell"
```

### 测试结果
```
✅ 测试通过
✅ 所有现有测试仍然通过（24个测试）
```

---

## 📊 影响范围

### 修改的文件
1. `trading/fib_calculator.py` - 核心修复（1行）
2. `test_ao_watch_bug.py` - 新增测试

### 向后兼容性
✅ **无破坏性变更** - 只修复了错误行为

---

## 📝 修复前后对比

### 修复前 ❌
- AO < 35k 绿转红 + 无持仓价格 → 返回 `{"action": "watch"}`
- `if sell:` 判断为真 → **错误触发卖出**

### 修复后 ✅
- AO < 35k 绿转红 + 无持仓价格 → 返回 `{"action": "watch"}`
- `if sell and sell.get("action") == "sell":` 判断为假 → **不触发卖出**

---

# Bug 修复报告 #3：除零保护缺失

## 📋 Bug 描述

### 问题位置
`trading/trade_checker.py` 第 217、258 行

### 严重程度
🟡 **中等** - 极端情况下可能导致程序崩溃

### 问题详情

在计算持仓 tokens 时，直接使用 `entry_amounts[tier] / entry_prices[tier]`，没有检查 `entry_prices[tier]` 是否为 0。

虽然正常情况下价格不会为 0，但在异常数据或边界情况下可能导致 `ZeroDivisionError`。

---

## ✅ 修复方案

### 修复代码

```python
# 修复前
total_tokens = sum(
    entry_amounts[tier] / entry_prices[tier]
    for tier in tiers_bought
)

# 修复后
total_tokens = sum(
    entry_amounts[tier] / entry_prices[tier]
    for tier in tiers_bought
    if entry_prices.get(tier, 0) > 0  # ✅ 添加除零保护
)
```

### 修复位置

1. `trading/trade_checker.py:219` - `_calculate_profit` 函数
2. `trading/trade_checker.py:260` - `_calculate_profit_multi_sell` 函数

---

## 🧪 测试验证

### 测试结果
```
✅ 所有 9 个单元测试通过
✅ 没有破坏现有功能
```

---

## 📊 总结

### 本次检查发现并修复的 Bug

1. ✅ **Fib 分批卖出逻辑错误** - 多次卖出记录被覆盖
2. ✅ **AO "watch" 信号误判** - 被错误当作卖出信号
3. ✅ **除零保护缺失** - 极端情况下可能崩溃

### 修改的文件

- `trading/trade_checker.py` - 核心修复（+97 行，API 变更）
- `trading/fib_calculator.py` - AO 信号判断修复（1 行）
- `tests/test_trade_checker.py` - 测试更新
- `test_ao_watch_bug.py` - 新增测试
- `test_fib_sell_bug.py` - 新增测试
- `BUG_FIX_REPORT.md` - 详细修复报告

### 测试覆盖

```
✅ 9 个 trade_checker 测试通过
✅ 24 个 fib_calculator 测试通过
✅ 2 个新增专项测试通过
```

所有 bug 已修复并通过测试验证！
