# 安装指南

## 📦 安装为 Skills

### 方法1: 本地安装（开发模式）

```bash
cd /Users/leon/logearn-trading-skills/logearn-traidng-skills
pip install -e .
```

### 方法2: 从 GitHub 安装

```bash
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git
```

---

## 🚀 使用

### 命令行使用

安装后可以直接使用 `papertrading` 命令：

```bash
# 基本用法（默认180k门槛）
papertrading <CA地址>

# 自定义门槛
papertrading <CA地址> 200

# 不启用门槛
papertrading <CA地址> 0
```

### Python 调用

```python
# 纸上交易
from papertrading import papertrading

result = papertrading(
    ca="你的CA地址",
    min_swing_high_mcap=180.0
)

if result:
    print(f"交易次数: {len(result['trades'])}")
    print(f"胜率: {result['win_rate']*100:.1f}%")
```

```python
# 使用交易模块
from trading.win_rate_analyzer import analyze_token_trades
from backtester.fetch_klines import get_token_info, fetch_klines

# 获取数据
info = get_token_info(ca)
klines = fetch_klines(ca)

# 运行分析
result = analyze_token_trades(
    ca=ca,
    raw_klines=klines,
    supply=info['total_supply'],
    min_swing_high_mcap=180.0,
    max_trades=5
)
```

---

## 🔧 卸载

```bash
pip uninstall logearn-trading-skills
```

---

## 📝 验证安装

```bash
# 检查是否安装成功
pip show logearn-trading-skills

# 测试命令
papertrading --help
```

---

## ⚙️ 配置

### 环境变量

```bash
# LogEarn API Key（如果需要）
export LOGEARN_API_KEY="your_api_key"
```

### 配置文件

可以通过 Python 代码配置：

```python
from trading.config import TradingConfig

config = TradingConfig(
    min_swing_high_mcap=180.0  # 波峰市值门槛
)
```

---

**版本**: 1.1.0  
**最后更新**: 2026-05-10
