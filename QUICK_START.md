# 快速开始指南

## 🚀 5分钟上手

### 1. 安装

```bash
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@release/v0.1.0
```

### 2. 设置环境变量

```bash
export LOGEARN_API_KEY="你的API Key"
export TOKEN_CA="代币地址"
```

### 3. 选择策略运行

#### 方式A: Fibonacci交易（5分钟K线）

```python
from trading import run_single_trade, get_klines_raw

def klines_provider():
    return get_klines_raw("代币地址", interval='5m', page_size=200)

run_single_trade(
    ca="代币地址",
    klines_provider=klines_provider,
    total_capital=2.0
)
```

#### 方式B: RSI定投（1小时K线）

```python
from trading import run_rsi_dca

run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,
    max_buy_count=10,
    interval='1h'
)
```

---

## 📚 核心接口速查

### K线服务

```python
from trading import get_klines

# 获取5分钟K线
klines = get_klines("CA", interval='5m', page_size=200)
```

### RSI指标

```python
from trading import get_klines, calculate_rsi

klines = get_klines("CA", interval='1h')
rsi = calculate_rsi(klines, period=14)
```

### 交易执行

```python
from trading import TradeExecutor

executor = TradeExecutor()

# 买入
executor.buy(ca="CA", amount_sol=0.1, current_price=0.00005)

# 卖出
executor.sell(ca="CA", percentage=1.0)
```

---

## 📖 详细文档

- [API使用指南](docs/API_USAGE.md) - 完整接口说明
- [K线服务](docs/KLINE_SERVICE_GUIDE.md) - K线获取
- [RSI定投](docs/RSI_DCA_GUIDE.md) - 定投策略
- [单次交易](docs/SINGLE_TRADE_GUIDE.md) - Fibonacci交易
- [安装指南](INSTALL.md) - 详细安装步骤

---

## 💡 使用建议

1. **Fibonacci交易** - 适合短线交易，使用5分钟K线
2. **RSI定投** - 适合长期定投，使用1小时K线
3. **自定义策略** - 组合使用K线服务和技术指标

---

## ⚠️ 注意事项

1. 必须设置 `LOGEARN_API_KEY` 环境变量
2. LogEarn skill与token绑定，不需要指定钱包
3. 建议先在测试环境运行
4. 按 `Ctrl+C` 可随时停止

---

**开始交易吧！** 🎉
