# K线服务使用指南

## 概述

K线服务（`kline_service.py`）是一个统一的K线数据获取接口，为所有交易模块提供K线数据。

## 特点

1. ✅ **统一接口** - 所有模块使用同一个K线服务
2. ✅ **多种周期** - 支持1m, 5m, 15m, 1h, 1d
3. ✅ **支持翻页** - 可获取所有历史K线
4. ✅ **自动解析** - 自动转换为Kline对象
5. ✅ **单例模式** - 全局共享一个服务实例

## 支持的K线周期

| 周期 | 说明 | intervalTime |
|------|------|--------------|
| `'1m'` | 1分钟 | 60秒 |
| `'5m'` | 5分钟 | 300秒 |
| `'15m'` | 15分钟 | 900秒 |
| `'1h'` | 1小时 | 3600秒 |
| `'1d'` | 1天 | 86400秒 |

## 使用方式

### 方法1: 使用便捷函数（推荐）

```python
from trading.kline_service import get_klines

# 获取5分钟K线（默认）
klines = get_klines("代币地址", interval='5m', page_size=200)

# 获取1小时K线
klines = get_klines("代币地址", interval='1h', page_size=200)

# 遍历K线
for kline in klines:
    print(f"时间: {kline.time}, 收盘价: {kline.close}")
```

### 方法2: 使用KlineService类

```python
from trading.kline_service import KlineService

# 创建服务实例
service = KlineService()

# 获取K线（返回Kline对象列表）
klines = service.get_klines("代币地址", interval='5m', page_size=200)

# 获取原始K线（返回字典列表）
raw_klines = service.get_klines_raw("代币地址", interval='5m', page_size=200)

# 获取最新一根K线
latest = service.get_latest_kline("代币地址", interval='5m')

# 获取所有历史K线（翻页）
all_klines = service.get_all_klines("代币地址", interval='5m', max_pages=10)
```

### 方法3: 使用单例

```python
from trading.kline_service import get_kline_service

# 获取全局单例
service = get_kline_service()

# 使用服务
klines = service.get_klines("代币地址", interval='5m')
```

## 数据格式

### Kline对象格式

```python
@dataclass
class Kline:
    time: int          # Unix时间戳（秒）
    open: float        # 开盘价（SOL）
    high: float        # 最高价（SOL）
    low: float         # 最低价（SOL）
    close: float       # 收盘价（SOL）
    volume: float      # 成交量
    market_cap: float  # 市值（默认0）
```

### 原始数据格式

```python
{
    "time": 1775883000,          # Unix时间戳（秒）
    "open": 0.001234,            # 开盘价（SOL）
    "openU": 0.001234,           # 开盘价（USD）
    "high": 0.001300,            # 最高价（SOL）
    "highU": 0.001300,           # 最高价（USD）
    "low": 0.001200,             # 最低价（SOL）
    "lowU": 0.001200,            # 最低价（USD）
    "close": 0.001280,           # 收盘价（SOL）
    "closeU": 0.001280,          # 收盘价（USD）
    "volume": 98765,             # 成交量
    "volumeU": 98765,            # 成交量（USD）
    "market_cap": 0              # 市值（添加字段）
}
```

## 在不同模块中使用

### 1. 在Fibonacci交易中使用

```python
from trading import get_klines, fib_signal

# 获取5分钟K线
klines = get_klines("代币地址", interval='5m', page_size=200)

# 计算Fibonacci信号
signal = fib_signal(
    klines,
    entry_price=None,
    tiers_bought=[],
    pending_tiers=[],
    skip_ao=False
)

if signal:
    print(f"信号: {signal['action']}")
```

### 2. 在RSI定投中使用

```python
from trading import get_klines, calculate_rsi

# 获取1小时K线
klines = get_klines("代币地址", interval='1h', page_size=200)

# 计算RSI
rsi = calculate_rsi(klines, period=14)
print(f"RSI: {rsi:.2f}")

if rsi < 30:
    print("触发买入")
```

### 3. 在单次交易机器人中使用

```python
from trading import run_single_trade, get_klines_raw

def klines_provider():
    # 使用5分钟K线
    return get_klines_raw("代币地址", interval='5m', page_size=200)

run_single_trade(
    ca="代币地址",
    klines_provider=klines_provider,
    total_capital=2.0
)
```

## 翻页获取历史数据

```python
from trading.kline_service import KlineService

service = KlineService()

# 方法1: 使用get_all_klines自动翻页（推荐）
all_klines = service.get_all_klines("代币地址", interval='1h', max_pages=10)
print(f"总共获取{len(all_klines)}根K线（已自动去重）")

# 方法2: 手动翻页
klines_page1 = service.get_klines("代币地址", interval='1h', page_size=200)
oldest_time = klines_page1[-1].time

klines_page2 = service.get_klines("代币地址", interval='1h', 
                                  page_size=200, end_time=oldest_time)
```

### K线拼接去重机制

**重要**：翻页获取K线时，相邻页面可能包含重复的K线。`get_all_klines`方法会自动去重：

```python
# 第1页: [K1, K2, K3, K4, K5]
# 第2页: [K5, K6, K7, K8, K9]  ← K5重复
# 第3页: [K9, K10, K11, K12]  ← K9重复

# 自动去重后: [K1, K2, K3, K4, K5, K6, K7, K8, K9, K10, K11, K12]
```

**去重逻辑**：
1. 使用`set`记录已见过的时间戳
2. 只添加未见过的K线
3. 如果某一页完全重复，自动停止翻页

**示例**：
```python
service = KlineService()

# 获取所有历史K线（自动去重）
all_klines = service.get_all_klines("代币地址", interval='5m', max_pages=10)

# 验证无重复
times = [k.time for k in all_klines]
assert len(times) == len(set(times))  # 时间戳唯一
print(f"✅ 获取{len(all_klines)}根K线，无重复")
```

## 环境变量

```bash
# 必需
export LOGEARN_API_KEY="你的API Key"

# 可选（默认值）
export LOGEARN_API_BASE="https://logearn.com/logearn"
```

## 完整示例

### 示例1: 获取K线并计算RSI

```python
from trading import get_klines, calculate_rsi

# 获取K线
klines = get_klines("代币地址", interval='1h', page_size=200)

# 计算RSI
rsi = calculate_rsi(klines, period=14)

print(f"获取{len(klines)}根K线")
print(f"最新价格: {klines[0].close:.8f} SOL")
print(f"当前RSI: {rsi:.2f}")
```

### 示例2: 获取多个周期的K线

```python
from trading import get_klines

ca = "代币地址"

# 获取不同周期的K线
klines_5m = get_klines(ca, interval='5m', page_size=200)
klines_15m = get_klines(ca, interval='15m', page_size=200)
klines_1h = get_klines(ca, interval='1h', page_size=200)

print(f"5分钟K线: {len(klines_5m)}根")
print(f"15分钟K线: {len(klines_15m)}根")
print(f"1小时K线: {len(klines_1h)}根")
```

### 示例3: 在交易策略中使用

```python
from trading import get_klines, calculate_rsi, TradeExecutor

# 初始化
ca = "代币地址"
executor = TradeExecutor()

# 获取K线
klines = get_klines(ca, interval='5m', page_size=200)

# 计算RSI
rsi = calculate_rsi(klines, period=14)

# 交易逻辑
if rsi < 30:
    print("RSI超卖，买入")
    result = executor.buy(ca=ca, amount_sol=0.1, current_price=klines[0].close)
    if result.success:
        print("买入成功")
elif rsi > 70:
    print("RSI超买，卖出")
    result = executor.sell(ca=ca, percentage=1.0)
    if result.success:
        print("卖出成功")
```

## API规范

K线服务完全符合LogEarn API规范：

### 请求参数

```json
{
  "chain": "3",
  "base": "代币地址",
  "intervalTime": 300,
  "pageSize": 200,
  "endTime": 1775883812
}
```

### 响应格式

```json
{
  "code": 200,
  "data": {
    "body": [
      {
        "time": 1775883000,
        "open": "0.001234",
        "openU": "0.001234",
        "high": "0.001300",
        "highU": "0.001300",
        "low": "0.001200",
        "lowU": "0.001200",
        "close": "0.001280",
        "closeU": "0.001280",
        "volume": "98765",
        "volumeU": "98765"
      }
    ]
  }
}
```

## 注意事项

1. **API Key必需** - 必须设置`LOGEARN_API_KEY`环境变量
2. **页面大小** - 建议不超过200根K线
3. **时间顺序** - 返回的K线按时间倒序（最新的在前）
4. **USD计价** - 带U结尾的字段表示USD计价
5. **自动转换** - 字符串价格自动转换为float

## 常见问题

### Q1: 如何修改默认K线周期？

修改`interval`参数：
```python
klines = get_klines("CA", interval='15m')  # 改为15分钟
```

### Q2: 如何获取更多K线？

增加`page_size`或使用翻页：
```python
# 方法1: 增加page_size
klines = get_klines("CA", interval='5m', page_size=200)

# 方法2: 翻页获取
all_klines = service.get_all_klines("CA", interval='5m', max_pages=10)
```

### Q3: 如何处理API错误？

使用try-except捕获异常：
```python
try:
    klines = get_klines("CA", interval='5m')
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"获取失败: {e}")
```

### Q4: 如何在多个模块间共享K线数据？

使用全局单例：
```python
from trading import get_kline_service

service = get_kline_service()  # 全局共享
klines = service.get_klines("CA", interval='5m')
```

## 总结

K线服务提供了统一、简洁的K线获取接口：

1. ✅ **统一接口** - 所有模块使用同一服务
2. ✅ **多种周期** - 支持1m到1d多种周期
3. ✅ **自动解析** - 自动转换为Kline对象
4. ✅ **支持翻页** - 可获取所有历史数据
5. ✅ **易于使用** - 简单的函数调用

推荐在所有交易模块中使用K线服务！
