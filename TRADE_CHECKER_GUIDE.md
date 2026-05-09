# 交易检测器使用指南

## 📋 功能说明

`trade_checker.py` 用于检测K线数据是否符合**一次完整交易**（买入→卖出），主要用于：
- ✅ 判断某个 token 是否已经完成过一次交易
- ✅ 避免重复交易同一个 token
- ✅ 输出买卖点和利润信息

## 🎯 核心特性

- **100% 复用核心逻辑**：使用 `fib_signal()` 和 `PositionManager`，不重新实现任何判断
- **只检测一次交易**：买入→卖出后立即停止
- **简单清晰的输出**：买入点、卖出点、利润

---

## 🚀 快速使用

### 基本用法

```python
from trading.trade_checker import check_single_trade_from_raw

# 获取 K线数据
raw_klines = [
    {
        "time": 1000000,
        "open": "0.0001",
        "high": "0.00012",
        "low": "0.00009",
        "close": "0.00011",
        "volume": "1000000"
    },
    # ... 更多K线
]

# 检测是否符合一次完整交易
result = check_single_trade_from_raw(raw_klines, total_capital=2.0)

# 判断结果
if result["matched"]:
    print("✅ 已有完整交易，跳过")
    # 不执行交易
else:
    print("❌ 未匹配到完整交易，可以交易")
    # 执行交易逻辑
```

### 实际应用场景

```python
from trading.trade_checker import check_single_trade_from_raw

def should_trade_token(token_address: str) -> bool:
    """
    判断是否应该交易某个 token
    
    Returns:
        True: 可以交易
        False: 已有完整交易，跳过
    """
    # 1. 获取 K线数据
    klines = get_klines(token_address)
    
    # 2. 检测是否已有完整交易
    result = check_single_trade_from_raw(klines)
    
    # 3. 返回判断结果
    return not result["matched"]  # 未匹配到完整交易才能交易


# 使用示例
token_address = "xxxxx"

if should_trade_token(token_address):
    print(f"开始交易 {token_address}")
    execute_trade(token_address)
else:
    print(f"跳过 {token_address}，已有完整交易记录")
```

---

## 📊 返回数据结构

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
        },
        {
            "tier": "buy_786",
            "price": 0.00004,
            "amount": 0.04,
            "kline_index": 12,
            "timestamp": 1001000
        }
    ],
    "sell_point": {
        "price": 0.00008,
        "kline_index": 25,
        "timestamp": 1005000,
        "reason": "ao≥35k绿转红",
        "type": "ao_sell"
    },
    "profit": {
        "invested": 0.10,      # 总投入（SOL）
        "returned": 0.176,     # 总回报（SOL）
        "profit_sol": 0.076,   # 利润（SOL）
        "profit_rate": 0.76    # 收益率 76%
    }
}
```

### 未匹配到完整交易

```python
{
    "matched": False,
    "buy_points": [],
    "sell_point": None,
    "profit": None
}
```

---

## 🔍 字段说明

### buy_points（买入点列表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `tier` | str | 买入档位（buy_618/buy_786/buy_861）|
| `price` | float | 买入价格 |
| `amount` | float | 买入金额（SOL）|
| `kline_index` | int | K线索引（从0开始）|
| `timestamp` | int | 时间戳 |

### sell_point（卖出点）

| 字段 | 类型 | 说明 |
|------|------|------|
| `price` | float | 卖出价格 |
| `kline_index` | int | K线索引 |
| `timestamp` | int | 时间戳 |
| `reason` | str | 卖出原因 |
| `type` | str | 卖出类型（ao_sell/stop_loss/fib_sell）|

### profit（利润信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| `invested` | float | 总投入（SOL）|
| `returned` | float | 总回报（SOL）|
| `profit_sol` | float | 利润（SOL）|
| `profit_rate` | float | 收益率（0.76 = 76%）|

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

**参数**：
- `raw_klines`: 原始K线数据列表
- `total_capital`: 总资金（SOL），默认 2.0
- `config`: 交易配置，默认使用 `DEFAULT_CONFIG`

**返回**：
- `Dict`: 检测结果（见上方数据结构）

### check_single_trade()

```python
def check_single_trade(
    klines: List[Kline],
    total_capital: float = 2.0,
    config = None
) -> Dict
```

**参数**：
- `klines`: 已解析的K线数据列表
- `total_capital`: 总资金（SOL），默认 2.0
- `config`: 交易配置

**返回**：
- `Dict`: 检测结果

### print_trade_result()

```python
def print_trade_result(result: Dict)
```

打印交易检测结果（格式化输出）

**参数**：
- `result`: `check_single_trade()` 返回的结果

---

## 💡 使用示例

### 示例 1: 基本检测

```python
from trading.trade_checker import check_single_trade_from_raw, print_trade_result

# K线数据
raw_klines = [...]

# 检测
result = check_single_trade_from_raw(raw_klines)

# 打印结果
print_trade_result(result)
```

### 示例 2: 批量检测多个 token

```python
from trading.trade_checker import check_single_trade_from_raw

def filter_tradable_tokens(token_list: list) -> list:
    """
    过滤出可以交易的 token（未有完整交易记录）
    """
    tradable = []
    
    for token in token_list:
        klines = get_klines(token["address"])
        result = check_single_trade_from_raw(klines)
        
        if not result["matched"]:
            tradable.append(token)
            print(f"✅ {token['symbol']}: 可交易")
        else:
            profit_rate = result["profit"]["profit_rate"]
            print(f"❌ {token['symbol']}: 已交易，收益率 {profit_rate*100:.2f}%")
    
    return tradable


# 使用
tokens = [
    {"symbol": "TOKEN1", "address": "xxx"},
    {"symbol": "TOKEN2", "address": "yyy"},
]

tradable_tokens = filter_tradable_tokens(tokens)
print(f"\n可交易 token 数量: {len(tradable_tokens)}")
```

### 示例 3: 自定义配置

```python
from trading.trade_checker import check_single_trade_from_raw
from trading.config import create_custom_config, AOConfig

# 自定义配置（例如：提高 AO 阈值）
custom_config = create_custom_config(
    ao=AOConfig(threshold_normal=0.00005000)  # 50k
)

# 使用自定义配置检测
result = check_single_trade_from_raw(
    raw_klines,
    total_capital=2.0,
    config=custom_config
)
```

---

## ⚠️ 注意事项

1. **K线数据质量**
   - 需要足够的K线数据（建议至少 50 根）
   - K线需要包含完整的下跌和反弹过程才能触发交易

2. **交易逻辑一致性**
   - 检测器 100% 复用核心交易逻辑
   - 检测结果与实际交易结果完全一致

3. **只检测一次交易**
   - 检测到卖出信号后立即停止
   - 不会检测多次交易

4. **时间锁限制**
   - 检测器内部设置 `trading_end_hour=24`，允许全天检测
   - 实际交易时仍受时间锁限制

---

## 🧪 测试

运行单元测试：

```bash
python3 -m unittest tests.test_trade_checker -v
```

运行示例：

```bash
python3 -m trading.trade_checker
```

---

## 📚 相关文档

- [交易逻辑梳理](README.md)
- [配置文件说明](trading/config.py)
- [Bug 修复报告](BUG_FIXES_AND_TESTS.md)
