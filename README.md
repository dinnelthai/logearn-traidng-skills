# LogEarn Trading Skills

基于 Fibonacci 回撤 + AO (Awesome Oscillator) 的 Solana 代币交易策略模块。

---

## 📁 项目结构

```
logearn-traidng-skills/
├── trading/          # 核心交易模块
├── tests/            # 测试文件
├── docs/             # 文档
└── executor.py       # 真实交易入口
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
# 真实交易
python trading/executor.py <CA地址>
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

### Python 调用

```python
from trading.executor import execute_trade

# 执行真实交易
result = execute_trade(
    ca="你的CA地址",
    min_swing_high_mcap=180.0  # 180k USD
)

# 查看结果
if result:
    print(f"交易状态: {result['status']}")
    print(f"买入价格: {result['buy_price']}")
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
