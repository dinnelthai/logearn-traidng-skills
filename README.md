# LogEarn Trading Skills

基于 Fibonacci 回撤 + RSI 的 Solana 代币交易策略模块。

## ✨ 核心功能

1. **Fibonacci交易** - 基于Fibonacci回撤的自动化交易（5分钟K线）
2. **RSI定投** - 基于RSI指标的智能定投策略（1小时K线）
3. **统一K线服务** - 支持多种周期的K线数据获取
4. **技术指标** - RSI、Fibonacci、AO等指标计算
5. **交易执行** - 自动买入、卖出、持仓管理

---

## 📁 项目结构

```
logearn-traidng-skills/
├── trading/                    # 核心交易模块
│   ├── kline_service.py       # 统一K线服务
│   ├── indicators.py          # 技术指标（RSI等）
│   ├── rsi_dca_bot.py         # RSI定投机器人
│   ├── single_trade_bot.py    # Fibonacci交易机器人
│   ├── executor.py            # 交易执行器
│   └── fib_calculator.py      # Fibonacci计算
├── docs/                       # 文档
│   ├── API_USAGE.md           # 对外接口使用指南
│   ├── KLINE_SERVICE_GUIDE.md # K线服务指南
│   ├── RSI_DCA_GUIDE.md       # RSI定投指南
│   └── SINGLE_TRADE_GUIDE.md  # 单次交易指南
├── tests/                      # 测试文件
├── example_single_trade.py     # Fibonacci交易示例
├── example_rsi_dca.py         # RSI定投示例
└── QUICK_START.md             # 快速开始
```

---

## 🚀 快速开始

### 1. 安装

```bash
# 从GitHub安装最新版本
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@release/v0.1.0

# 或克隆后安装
git clone https://github.com/dinnelthai/logearn-traidng-skills.git
cd logearn-traidng-skills
git checkout release/v0.1.0
pip install -e .
```

### 2. 设置环境变量

```bash
export LOGEARN_API_KEY="你的API Key"
export TOKEN_CA="代币地址"  # 可选
```

### 3. 使用

#### 方式A: Fibonacci交易（5分钟K线）

```python
from trading import run_fibonacci_trade

# 自动使用K线缓存+增量更新
run_fibonacci_trade(
    ca="代币地址",
    total_capital=2.0,
    check_interval=60
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

#### 方式C: 命令行运行

```bash
# Fibonacci交易
python example_fibonacci_trade.py

# RSI定投
python example_rsi_dca.py
```

---

## 📚 对外公开接口

本项目只对外暴露**2个核心交易接口**，K线获取、缓存等由内部自动处理。

### 1. Fibonacci交易

```python
from trading import run_fibonacci_trade

# 运行Fibonacci交易（K线自动缓存+增量更新）
run_fibonacci_trade(
    ca="代币地址",
    total_capital=2.0,      # 总资金（SOL）
    check_interval=60       # 检查间隔（秒）
)
```

**特点**：
- 自动获取5分钟K线（首次全量，后续增量）
- Fibonacci回撤买入（61.8%, 78.6%, 86.1%）
- AO卖出信号
- 全部卖出后自动停止
- 首次获取全量历史K线，后续减少90%+ API调用

### 2. RSI定投

```python
from trading import run_rsi_dca

# 运行RSI定投（K线自动获取）
run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,         # 每次定投金额（SOL）
    max_buy_count=10,       # 最大定投次数
    check_interval=300      # 检查间隔（秒）
)
```

**特点**：
- 自动获取1小时K线
- RSI < 30 时自动买入
- 买入后等待RSI > 50才能再次买入
- 达到最大次数后自动停止

---

## �📊 策略说明

### Fibonacci交易策略（5分钟K线）
- **买入档位**: 0.618, 0.786, 0.861
- **卖出档位**: 1.000, 1.272
- **止损**: 0.920
- **AO卖出**: 零轴上方AO>35k绿转红，或收益率>50%

### RSI定投策略（1小时K线）
- **买入条件**: RSI < 30
- **重置条件**: RSI > 50
- **定投金额**: 固定金额
- **次数限制**: 达到最大次数后停止

---

## 📖 完整文档

- **[快速开始](QUICK_START.md)** - 5分钟上手
- **[公开接口](docs/PUBLIC_API.md)** - 对外公开接口说明（只有2个）
- **[RSI定投](docs/RSI_DCA_GUIDE.md)** - 定投策略说明
- **[安装指南](INSTALL.md)** - 详细安装步骤
- **[交易流程](docs/TRADING_PROCESS.md)** - 交易逻辑说明

---

## 📝 使用示例

### 示例1: Fibonacci交易

```python
from trading import run_fibonacci_trade

# 运行Fibonacci交易
run_fibonacci_trade(
    ca="代币地址",
    total_capital=2.0,
    check_interval=60
)
```

### 示例2: RSI定投

```python
from trading import run_rsi_dca

# 运行RSI定投
run_rsi_dca(
    ca="代币地址",
    dca_amount=0.1,
    max_buy_count=10,
    check_interval=300
)
```

---

## 🧪 测试

```bash
# 运行所有测试
./run_tests.sh
```

---

## 📖 文档

- **[安装配置](INSTALL.md)** - 安装说明
- **[LogEarn 配置](SETUP_LOGEARN.md)** - LogEarn Skills 配置
- **[波峰市值门槛](docs/SWING_HIGH_MCAP_FILTER_GUIDE.md)** - 波峰市值过滤功能
- **[Trade Checker](docs/TRADE_CHECKER_GUIDE.md)** - 交易检测器使用
- **[实现总结](docs/IMPLEMENTATION_SUMMARY.md)** - 最新功能实现

---

## 🎯 核心特性

✅ Fibonacci 回撤买入/卖出
✅ AO (Awesome Oscillator) 卖出信号
✅ 分档买入，分批卖出
✅ 仓位管理
✅ 止损机制
✅ K线市值过滤
✅ 波峰市值门槛 ⭐
✅ 买卖周期重置
✅ 真实交易执行  

---

## 🔧 配置参数

### 环境变量

```bash
# LogEarn CLI 路径（必须）
export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"

# LogEarn API Key（必须）
export LOGEARN_API_KEY="your_api_key"
```

### 交易配置

```python
from trading.config import TradingConfig

config = TradingConfig(
    min_swing_high_mcap=180.0  # 波峰市值门槛（180k USD）
)
```

---

## 📂 目录说明

```
.
├── trading/          # 核心交易逻辑
│   ├── fib_calculator.py
│   ├── position_manager.py
│   ├── trade_checker.py
│   ├── win_rate_analyzer.py
│   ├── executor.py
│   └── config.py
│
├── tests/            # 测试文件
├── docs/             # 文档
│
├── setup.py          # 安装配置
└── README.md         # 本文件
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- **GitHub**: https://github.com/dinnelthai/logearn-traidng-skills
- **LogEarn Skills**: https://github.com/logearn/logearn-skills

---

**版本**: 1.1.0  
**最后更新**: 2026-05-10  
**状态**: ✅ 稳定
