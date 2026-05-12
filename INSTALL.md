# 安装指南

## 📦 安装为 Skills

### 方法1: 安装指定 Release 版本（推荐）

#### 安装最新 Release

```bash
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@release/v0.1.0
```

#### 安装指定 Tag

```bash
# 安装 v0.1.0 版本
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@v0.1.0
```

#### 克隆后安装

```bash
# 克隆仓库
git clone https://github.com/dinnelthai/logearn-traidng-skills.git
cd logearn-traidng-skills

# 切换到 release 分支
git checkout release/v0.1.0

# 安装
pip install -e .
```

### 方法2: 本地安装（开发模式）

```bash
cd /Users/leon/logearn-trading-skills/logearn-traidng-skills
pip install -e .
```

### 方法3: 从 GitHub 主分支安装（不推荐）

```bash
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git
```

---

## 🚀 使用

### 单次交易机器人

```bash
# 设置环境变量
export TOKEN_CA="代币地址"
export LOGEARN_API_KEY="你的API Key"

# 运行
python example_single_trade.py
```

### Python 调用

```python
# 单次交易
from trading.single_trade_bot import run_single_trade

def get_klines():
    # 从API获取K线数据
    return fetch_klines(ca)

run_single_trade(
    ca="代币地址",
    klines_provider=get_klines,
    total_capital=2.0,
    check_interval=60
)
```

```python
# 交易检测
from trading.trade_checker import check_single_trade
from trading.fib_calculator import parse_klines

klines = parse_klines(raw_klines)
result = check_single_trade(
    klines=klines,
    total_capital=2.0
)

if result['matched']:
    print(f"✅ 完整交易")
    print(f"利润: {result['profit']['profit_sol']} SOL")
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

# 查看版本
python -c "import trading; print(trading.__version__)"

# 测试导入
python -c "from trading.single_trade_bot import run_single_trade; print('✅ 安装成功')"
```

---

## ⚙️ 配置

### 环境变量

```bash
# LogEarn API Key（必需）
export LOGEARN_API_KEY="your_api_key"

# 代币地址（可选，可在代码中指定）
export TOKEN_CA="代币地址"
```

### 配置文件

可以通过 Python 代码配置：

```python
from trading.config import TradingConfig, PositionConfig

config = TradingConfig(
    position=PositionConfig(
        max_position_ratio=0.30,  # 最大仓位30%
        min_position_sol=0.005,   # 最小买入0.005 SOL
        trading_end_hour=24       # 24小时交易
    )
)
```

---

## 📋 版本说明

### Release 版本

- **v0.1.0** (release/v0.1.0) - 当前稳定版本
  - ✅ 单次交易机器人
  - ✅ Fibonacci回撤策略
  - ✅ AO卖出信号
  - ✅ 分批买入卖出
  - ✅ 移除市值门槛逻辑

### 安装指定版本

```bash
# 安装 v0.1.0
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@v0.1.0

# 安装 release/v0.1.0 分支
pip install git+https://github.com/dinnelthai/logearn-traidng-skills.git@release/v0.1.0
```

---

**当前版本**: v0.1.0  
**最后更新**: 2026-05-11
