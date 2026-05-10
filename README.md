# LogEarn Trading Skills

基于 Fibonacci 回撤 + AO (Awesome Oscillator) 的 Solana 代币交易策略模块。

---

## 📁 项目结构

```
logearn-traidng-skills/
├── trading/          # 核心交易模块
├── backtester/       # 回测模块
├── tests/            # 测试文件
├── examples/         # 使用示例
├── diagnostics/      # 诊断工具
├── docs/             # 文档
└── papertrading.py   # 纸上交易入口
```

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/dinnelthai/logearn-traidng-skills.git
cd logearn-traidng-skills

# 安装为 skills
pip install -e .
```

### 2. 配置 LogEarn

```bash
# 安装 LogEarn Skills
npx skills add logearn/logearn-skills

# 设置环境变量
export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"
export LOGEARN_API_KEY="your_api_key"
```

详细配置请查看 [SETUP_LOGEARN.md](SETUP_LOGEARN.md)

### 3. 使用

```bash
# 纸上交易（回测）
papertrading <CA地址> [市值门槛]

# 示例
papertrading HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump 180k
```

---

## 📊 核心功能

### Fibonacci 回撤策略
- **买入档位**: 0.618, 0.786, 0.861
- **卖出档位**: 1.000, 1.272
- **止损**: 0.920

### AO 卖出信号
- **零轴上方**: AO > 35k，绿转红卖出
- **零轴下方**: 收益率 > 50% 卖出

### 市值过滤（双重机制）

#### 1. K线市值过滤
从第一次达到最小市值的K线开始分析

#### 2. 波峰市值门槛 ⭐ 新功能
- 只有波峰市值达到门槛才启动买入检测
- 买卖周期完成后自动重置
- 支持动态调整门槛

---

## 📝 使用示例

### 命令行使用

```bash
# 默认门槛 180k
papertrading <CA地址>

# 自定义门槛
papertrading <CA地址> 200k

# 不启用门槛
papertrading <CA地址> 0
```

### Python 调用

```python
from papertrading import papertrading

# 运行回测
result = papertrading(
    ca="你的CA地址",
    min_swing_high_mcap=180.0  # 180k USD
)

# 查看结果
if result:
    print(f"交易次数: {len(result['trades'])}")
    print(f"胜率: {result['win_rate']*100:.1f}%")
    print(f"平均收益: {result['avg_profit_rate']*100:.2f}%")
```

### 高级用法

```python
from trading.win_rate_analyzer import analyze_token_trades
from backtester.fetch_klines import get_token_info, fetch_klines

# 获取数据
info = get_token_info(ca)
klines = fetch_klines(ca)

# 运行分析（双重市值过滤）
result = analyze_token_trades(
    ca=ca,
    raw_klines=klines,
    supply=info['total_supply'],
    min_market_cap=180.0,         # K线过滤
    min_swing_high_mcap=180.0,    # 波峰门槛
    max_trades=5
)
```

---

## 🧪 测试

```bash
# 运行所有测试
./run_tests.sh

# 波峰市值门槛测试
python tests/test_swing_high_mcap_filter.py

# 市值过滤测试
python tests/test_filter_logic.py
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
✅ 多次交易分析  
✅ 胜率统计  
✅ HTML报告生成  

---

## 🔧 配置参数

### 环境变量

```bash
# LogEarn CLI 路径（必须）
export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"

# LogEarn API Key（必须）
export LOGEARN_API_KEY="your_api_key"

# 数据库路径（可选）
export BACKTEST_DB="$HOME/backtest/data/backtest.db"

# 缓存路径（可选）
export BACKTEST_CACHE="$HOME/backtest/cache"
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
│   └── config.py
│
├── backtester/       # 回测工具
│   ├── fetch_klines.py
│   ├── backtest.py
│   └── run_backtest.py
│
├── tests/            # 测试文件
├── examples/         # 使用示例
├── diagnostics/      # 诊断工具
├── docs/             # 文档
│
├── papertrading.py   # 纸上交易入口
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
