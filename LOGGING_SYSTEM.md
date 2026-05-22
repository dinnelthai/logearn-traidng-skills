# 交易日志系统

## 📋 概述

完整的交易日志系统，记录所有关键交易决策和执行过程，帮助你：
- ✅ 追踪每笔交易的完整过程
- ✅ 分析交易决策的依据
- ✅ 排查问题和优化策略
- ✅ 生成交易报告

---

## 🎯 日志类型

### 1. 控制台日志（实时查看）
- 简洁的实时输出
- 只显示INFO级别以上的重要信息
- 适合监控交易进度

### 2. 文件日志（完整记录）
- 详细的DEBUG级别日志
- 保存在 `~/.logearn/logs/trading_YYYYMMDD.log`
- 包含所有操作细节

### 3. 交易数据日志（结构化）
- JSONL格式（每行一个JSON对象）
- 保存在 `~/.logearn/logs/trades_YYYYMMDD.jsonl`
- 方便数据分析和统计

---

## 📊 日志内容

### 交易执行日志

#### 买入日志
```python
logger.log_buy_attempt(ca, amount_sol, price)
# 输出: 🔵 买入尝试 | CA: FDBjQdN4... | 金额: 0.5 SOL | 价格: 0.00004000

logger.log_buy_success(ca, amount_sol, price, tokens_received)
# 输出: ✅ 买入成功 | CA: FDBjQdN4... | 花费: 0.5 SOL | 获得: 12500.00 tokens

logger.log_buy_failed(ca, amount_sol, reason)
# 输出: ❌ 买入失败 | CA: FDBjQdN4... | 金额: 0.5 SOL | 原因: 余额不足
```

#### 卖出日志
```python
logger.log_sell_attempt(ca, percentage, price)
# 输出: 🔴 卖出尝试 | CA: FDBjQdN4... | 比例: 100% | 价格: 0.00006000

logger.log_sell_success(ca, percentage, price, sol_received, profit_rate)
# 输出: ✅ 卖出成功 | CA: FDBjQdN4... | 比例: 100% | 获得: 0.75 SOL | 收益率: 50.00%

logger.log_sell_failed(ca, percentage, reason)
# 输出: ❌ 卖出失败 | CA: FDBjQdN4... | 比例: 100% | 原因: 持仓不足
```

---

### 信号检测日志

#### Fibonacci信号
```python
logger.log_fib_signal(ca, "buy", "buy_618", price, fib_price)
# 输出: 📊 FIB信号 | CA: FDBjQdN4... | 类型: buy | 档位: buy_618 | 当前价: 0.00003800 | FIB价: 0.00004000
```

#### AO信号
```python
logger.log_ao_signal(ca, ao_value, threshold, reason, price)
# 输出: 📈 AO信号 | CA: FDBjQdN4... | AO: 0.00003800 | 阈值: 0.00003500 | 原因: ao≥35k绿转红 | 价格: 0.00006000
```

#### RSI信号
```python
logger.log_rsi_signal(ca, rsi_value, "oversold", price)
# 输出: 📉 RSI信号 | CA: FDBjQdN4... | RSI: 28.50 | 类型: oversold | 价格: 0.00003500
```

#### 止损触发
```python
logger.log_stop_loss(ca, current_price, stop_price, "92%回撤")
# 输出: ⚠️ 止损触发 | CA: FDBjQdN4... | 当前价: 0.00003000 | 止损价: 0.00003200 | 原因: 92%回撤
```

---

### 仓位管理日志

#### 仓位检查
```python
logger.log_position_check(ca, position_value, max_allowed, can_buy)
# 输出: 💼 仓位检查 | CA: FDBjQdN4... | 当前: 1.50 SOL | 上限: 2.00 SOL | ✅ 可买入
```

#### 资金检查
```python
logger.log_capital_check(ca, invested, total_capital, can_buy)
# 输出: 💰 资金检查 | CA: FDBjQdN4... | 已投入: 8.00 SOL | 总资金: 10.00 SOL | ✅ 可买入
```

#### 加权均价
```python
logger.log_weighted_avg_price(ca, avg_price, total_amount)
# 输出: 📊 加权均价 | CA: FDBjQdN4... | 均价: 0.00004200 | 总量: 25000.00
```

---

### 策略执行日志

#### 策略启动
```python
logger.log_strategy_start("Fibonacci", ca, {
    "total_capital": 2.0,
    "check_interval": 60
})
# 输出: 🚀 策略启动 | 策略: Fibonacci | CA: FDBjQdN4... | 参数: {'total_capital': 2.0, 'check_interval': 60}
```

#### 策略停止
```python
logger.log_strategy_stop("Fibonacci", ca, "交易完成", {
    "total_invested": 2.0,
    "total_received": 3.0,
    "profit_rate": 0.5
})
# 输出: 🛑 策略停止 | 策略: Fibonacci | CA: FDBjQdN4... | 原因: 交易完成
# 输出: 📊 交易总结 | {'total_invested': 2.0, 'total_received': 3.0, 'profit_rate': 0.5}
```

---

### K线数据日志

```python
logger.log_kline_fetch(ca, "5m", 200, from_cache=True)
# 输出: 📊 K线获取 | CA: FDBjQdN4... | 周期: 5m | 数量: 200 | 来源: 缓存

logger.log_kline_cache_update(ca, "5m", 5, 205)
# 输出: 🔄 缓存更新 | CA: FDBjQdN4... | 周期: 5m | 新增: 5 | 总计: 205
```

---

### 错误和警告日志

```python
logger.log_error("买入执行", exception, ca)
# 输出: ❌ 错误 | 上下文: 买入执行 | CA: FDBjQdN4... | 错误: Connection timeout

logger.log_warning("API限流，等待重试", ca)
# 输出: ⚠️ 警告 | API限流，等待重试 | CA: FDBjQdN4...
```

---

## 💻 使用方法

### 基础使用

```python
from trading.logger import get_logger

# 获取日志实例（单例模式）
logger = get_logger()

# 记录交易
logger.log_buy_attempt("CA地址", 0.5, 0.00004)
logger.log_buy_success("CA地址", 0.5, 0.00004, 12500.0)

# 记录信号
logger.log_ao_signal("CA地址", 0.00003800, 0.00003500, "ao≥35k绿转红", 0.00006)

# 记录策略
logger.log_strategy_start("Fibonacci", "CA地址", {"total_capital": 2.0})
```

---

### 在交易执行器中使用

```python
# trading/executor.py
from .logger import get_logger

class TradeExecutor:
    def __init__(self):
        self.logger = get_logger()
    
    def buy(self, ca: str, amount_sol: float, ...):
        # 记录买入尝试
        self.logger.log_buy_attempt(ca, amount_sol, current_price)
        
        try:
            # 执行买入
            result = self._logearn_swap(...)
            
            if result.success:
                # 记录买入成功
                self.logger.log_buy_success(ca, amount_sol, current_price, tokens_received)
            else:
                # 记录买入失败
                self.logger.log_buy_failed(ca, amount_sol, result.message)
        
        except Exception as e:
            # 记录错误
            self.logger.log_error("买入执行", e, ca)
```

---

### 在策略Bot中使用

```python
# trading/single_trade_bot.py
from .logger import get_logger

class SingleTradeBot:
    def __init__(self, ca: str, total_capital: float):
        self.logger = get_logger()
        
        # 记录策略启动
        self.logger.log_strategy_start("Fibonacci", ca, {
            "total_capital": total_capital
        })
    
    def run(self):
        while not self.trade_complete:
            # 记录检查周期
            self.logger.log_check_cycle("Fibonacci", self.ca, cycle_num)
            
            # 检测信号
            signal = self.check_signals()
            
            if signal['type'] == 'buy':
                # 记录FIB信号
                self.logger.log_fib_signal(
                    self.ca, "buy", signal['tier'], 
                    current_price, signal['fib_price']
                )
                
                # 执行买入
                self.execute_buy(signal)
        
        # 记录策略停止
        self.logger.log_strategy_stop("Fibonacci", self.ca, "交易完成", summary)
```

---

## 📁 日志文件位置

### 默认路径
```
~/.logearn/logs/
├── trading_20260523.log      # 文本日志
└── trades_20260523.jsonl     # 结构化交易数据
```

### 自定义路径
```python
from trading.logger import get_logger

# 指定日志目录
logger = get_logger(log_dir="/path/to/logs")
```

---

## 📊 日志分析

### 读取JSONL交易数据

```python
import json

# 读取今天的交易数据
with open("~/.logearn/logs/trades_20260523.jsonl") as f:
    trades = [json.loads(line) for line in f]

# 统计买入次数
buy_count = sum(1 for t in trades if t['action'] == 'buy_success')

# 计算总收益
total_profit = sum(
    t.get('profit_rate', 0) 
    for t in trades 
    if t['action'] == 'sell_success'
)

# 找出所有错误
errors = [t for t in trades if t['action'] == 'error']
```

---

### 生成交易报告

```python
import pandas as pd

# 加载交易数据
trades = []
with open("~/.logearn/logs/trades_20260523.jsonl") as f:
    trades = [json.loads(line) for line in f]

df = pd.DataFrame(trades)

# 按代币统计
by_ca = df.groupby('ca').agg({
    'action': 'count',
    'profit_rate': 'mean'
})

# 按时间统计
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
by_hour = df.groupby('hour')['action'].count()
```

---

## 🎯 日志级别

### DEBUG
- K线获取
- 缓存更新
- 仓位检查
- 检查周期

### INFO
- 交易执行（买入/卖出）
- 信号检测
- 策略启动/停止

### WARNING
- 止损触发
- API限流
- 异常情况

### ERROR
- 交易失败
- 系统错误
- 异常捕获

---

## 🔧 配置示例

### 只输出到文件（不显示控制台）

```python
from trading.logger import TradeLogger
import logging

logger = TradeLogger()

# 移除控制台Handler
for handler in logger.logger.handlers[:]:
    if isinstance(handler, logging.StreamHandler):
        logger.logger.removeHandler(handler)
```

### 修改日志级别

```python
from trading.logger import get_logger

logger = get_logger()

# 设置控制台只显示WARNING以上
for handler in logger.logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.WARNING)
```

---

## 📋 完整示例

### Fibonacci交易日志示例

```
2026-05-23 06:00:00 - INFO - 🚀 策略启动 | 策略: Fibonacci | CA: FDBjQdN4... | 参数: {'total_capital': 2.0}
2026-05-23 06:00:05 - INFO - 📊 FIB信号 | CA: FDBjQdN4... | 类型: buy | 档位: buy_618 | 当前价: 0.00003800 | FIB价: 0.00004000
2026-05-23 06:00:06 - INFO - 🔵 买入尝试 | CA: FDBjQdN4... | 金额: 0.5 SOL | 价格: 0.00003800
2026-05-23 06:00:10 - INFO - ✅ 买入成功 | CA: FDBjQdN4... | 花费: 0.5 SOL | 获得: 13157.89 tokens
2026-05-23 06:15:30 - INFO - 📈 AO信号 | CA: FDBjQdN4... | AO: 0.00003800 | 阈值: 0.00003500 | 原因: ao≥35k绿转红 | 价格: 0.00006000
2026-05-23 06:15:31 - INFO - 🔴 卖出尝试 | CA: FDBjQdN4... | 比例: 100% | 价格: 0.00006000
2026-05-23 06:15:35 - INFO - ✅ 卖出成功 | CA: FDBjQdN4... | 比例: 100% | 获得: 0.79 SOL | 收益率: 58.00%
2026-05-23 06:15:36 - INFO - 🛑 策略停止 | 策略: Fibonacci | CA: FDBjQdN4... | 原因: 交易完成
2026-05-23 06:15:36 - INFO - 📊 交易总结 | {'total_invested': 0.5, 'total_received': 0.79, 'profit_rate': 0.58}
```

---

## ✅ 优势

1. **完整记录** - 所有交易决策和执行过程
2. **结构化数据** - JSONL格式方便分析
3. **实时监控** - 控制台输出实时查看
4. **问题排查** - 详细的DEBUG日志
5. **性能分析** - 统计交易数据优化策略
6. **合规审计** - 完整的交易记录

---

**专业的日志系统，让每笔交易都有迹可循！** 🎉
