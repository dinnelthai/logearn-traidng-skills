# 市值显示格式修复

**修复时间**: 2026-05-10  
**问题**: 买入和卖出时市值显示不正确  
**状态**: ✅ 已修复

---

## 📋 问题描述

用户反馈：买入市值和卖出市值显示不对，应该按照 **K (千)** 和 **M (百万)** 的格式显示。

**参考格式**（来自用户界面）：
- Clawd: Mcap = **$251.5K**
- GAYTIES: Mcap = **$269.1K**
- UFO: Mcap = **$45.4K**

---

## ✅ 修复内容

### 1. 新增市值格式化函数

**文件**: `trading/trade_checker.py`

```python
def _format_market_cap(market_cap: float) -> str:
    """
    格式化市值显示（K/M格式）
    
    Args:
        market_cap: 市值（单位：k，即千美元）
    
    Returns:
        str: 格式化的市值字符串
        
    示例:
        45.4 -> "$45.4K"
        251.5 -> "$251.5K"
        1500.0 -> "$1.5M"
        2500.0 -> "$2.5M"
    """
    if market_cap >= 1000:
        # >= 1000k = >= 1M
        return f"${market_cap/1000:.1f}M"
    else:
        # < 1000k
        return f"${market_cap:.1f}K"
```

**格式规则**：
- 市值 < 1000k：显示为 `$XXX.XK`
- 市值 >= 1000k：显示为 `$X.XM`

---

### 2. 在买入/卖出记录中保存市值

**买入记录**：
```python
buy_records.append({
    "tier": tier,
    "price": price,
    "amount": amount,
    "kline_index": i,
    "timestamp": klines[i].time,
    "market_cap": klines[i].market_cap  # 新增：记录买入时的市值
})
```

**卖出记录**（AO/止损/Fib）：
```python
sell_records.append({
    "price": signal.get("price"),
    "kline_index": i,
    "timestamp": klines[i].time,
    "reason": "...",
    "type": "...",
    "percentage": ...,
    "market_cap": klines[i].market_cap  # 新增：记录卖出时的市值
})
```

---

### 3. 在打印输出中显示市值

**买入点显示**：
```python
print("📊 买入点:")
for i, buy in enumerate(result["buy_points"], 1):
    print(f"  {i}. {buy['tier']}")
    print(f"     价格: {buy['price']:.8f}")
    print(f"     金额: {buy['amount']:.4f} SOL")
    print(f"     K线: #{buy['kline_index']}")
    # 新增：显示市值
    if buy.get('market_cap') and buy['market_cap'] > 0:
        mcap_str = _format_market_cap(buy['market_cap'])
        print(f"     市值: {mcap_str}")
```

**卖出点显示**：
```python
print("📈 卖出点:")
for i, sell in enumerate(sell_points, 1):
    print(f"  {i}. {sell['type']}")
    print(f"     价格: {sell['price']:.8f}")
    print(f"     比例: {sell.get('percentage', 1.0)*100:.0f}%")
    print(f"     K线: #{sell['kline_index']}")
    print(f"     原因: {sell['reason']}")
    if sell.get('tier'):
        print(f"     档位: {sell['tier']}")
    # 新增：显示市值
    if sell.get('market_cap') and sell['market_cap'] > 0:
        mcap_str = _format_market_cap(sell['market_cap'])
        print(f"     市值: {mcap_str}")
```

---

## 📊 修复效果

### 修复前
```
📊 买入点:
  1. buy_618
     价格: 0.00006275
     金额: 0.0600 SOL
     K线: #20
     # 没有市值显示
```

### 修复后
```
📊 买入点:
  1. buy_618
     价格: 0.00006275
     金额: 0.0600 SOL
     K线: #20
     市值: $133.0K  ✅ 新增
```

---

## 🧪 测试验证

### 格式化测试
```
✅     45.4k ->     $45.4K
✅    251.5k ->    $251.5K
✅    269.1k ->    $269.1K
✅    999.9k ->    $999.9K
✅   1000.0k ->      $1.0M
✅   1500.0k ->      $1.5M
✅   2500.0k ->      $2.5M
✅  10000.0k ->     $10.0M
```

### 实际输出示例
```
📊 买入点:
  1. buy_618
     价格: 0.00006275
     金额: 0.0600 SOL
     K线: #20
     市值: $133.0K

📈 卖出点:
  1. fib_sell
     价格: 0.00008700
     比例: 30%
     K线: #30
     原因: 价格触达 sell_100 位 0.00008500，卖出 30%
     档位: sell_100
     市值: $178.5K
  2. fib_sell
     价格: 0.00009600
     比例: 50%
     K线: #33
     原因: 价格触达 sell_1272 位 0.00009479，卖出 50%
     档位: sell_1272
     市值: $198.0K
```

### 单元测试
```
✅ 78个现有测试全部通过
```

---

## 📁 修改文件

**核心代码**：
1. `trading/trade_checker.py` - 添加格式化函数 + 记录市值 + 显示市值

**修改行数**：约30行

---

## ✨ 功能特性

1. **自动格式化**
   - < 1000k：显示为K（千）
   - >= 1000k：显示为M（百万）

2. **精度控制**
   - 保留1位小数
   - 清晰易读

3. **向后兼容**
   - 如果K线没有market_cap字段，不显示市值
   - 如果market_cap为0，不显示市值

4. **完整记录**
   - 买入时记录市值
   - 每次卖出都记录市值
   - 支持多次卖出

---

## 💡 使用说明

### 数据准备

确保K线数据包含 `market_cap` 字段：

```python
raw_klines = [
    {
        "time": 1000000,
        "open": 0.0001,
        "high": 0.00011,
        "low": 0.00009,
        "close": 0.0001,
        "volume": "1000000",
        "market_cap": 251.5  # 单位：k（千美元）
    },
    # ...
]
```

### 自动显示

调用 `print_trade_result()` 时会自动显示市值：

```python
result = check_single_trade_from_raw(raw_klines)
print_trade_result(result)
```

输出会自动包含市值信息（如果有）。

---

## ✅ 总结

**修复完成**：
- ✅ 市值按K/M格式显示
- ✅ 买入点显示市值
- ✅ 卖出点显示市值
- ✅ 格式清晰易读
- ✅ 向后兼容
- ✅ 所有测试通过

**显示效果**：
- $45.4K ✅
- $251.5K ✅
- $1.5M ✅

**用户体验**：与界面显示格式完全一致！🎉
