# 🚀 LogEarn Trading Skills

**Solana Meme币交易模块 - 独立的交易逻辑库**

专业的交易执行、仓位管理和止盈止损模块，可独立使用或集成到任何交易系统。

---

## 🎯 核心功能

### 3大核心模块

```
1. TradeExecutor - 交易执行器
   ├─ 买入token（限价/市价）
   ├─ 卖出token（全部/部分）
   ├─ 获取持仓信息
   └─ LogEarn API集成

2. PositionManager - 仓位管理器
   ├─ 仓位大小计算
   ├─ 仓位上限检查（30%）
   ├─ 交易时间检查（13点前）
   ├─ 加权平均价格计算
   └─ 持仓市值计算

3. ProfitManager - 止盈止损管理器
   ├─ 固定止盈检查（50%/100%）
   ├─ AO卖出信号检测
   ├─ 止损检查
   ├─ AO启动检测
   └─ 收益率计算
```

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/dinnelthai/logearn-trading-skills.git
cd logearn-trading-skills
```

### 基本使用

```python
from trading import TradeExecutor, PositionManager, ProfitManager

# 初始化
executor = TradeExecutor(wallet="your_wallet_address")
position_mgr = PositionManager(max_position_ratio=0.30)
profit_mgr = ProfitManager(profit_target_50=0.50)

# 买入
result = executor.buy(
    ca="token_address",
    amount_sol=0.05,
    limit_price=0.00004
)

if result.success:
    print(f"买入成功: {result.message}")

# 检查仓位
positions = executor.get_positions()
can_buy, reason = position_mgr.can_buy(
    ca="token_address",
    amount_sol=0.05,
    total_capital=2.0,
    positions=positions
)

# 检查止盈
action = profit_mgr.check_profit_target(
    current_price=0.00006,
    avg_price=0.00004,
    profit_50_sold=False,
    ao_active=False
)

if action.should_sell:
    print(f"触发止盈: {action.reason}")
    result = executor.sell(ca="token_address", percentage=action.percentage)
```

---

## 📦 模块说明

### TradeExecutor - 交易执行器

```python
from trading import TradeExecutor

executor = TradeExecutor(
    wallet="your_wallet_address",
    logearn_cli_path="/path/to/logearn-cli.py"  # 可选
)

# 买入
result = executor.buy(
    ca="token_address",
    amount_sol=0.05,
    limit_price=0.00004,
    current_price=0.000038,
    slippage=0.02
)

# 卖出（全部）
result = executor.sell(ca="token_address", percentage=1.0)

# 卖出（50%）
result = executor.sell(ca="token_address", percentage=0.5)

# 获取持仓
positions = executor.get_positions()
```

---

### PositionManager - 仓位管理器

```python
from trading import PositionManager

pm = PositionManager(
    max_position_ratio=0.30,  # 单币最大30%
    min_position_sol=0.005,   # 最小0.005 SOL
    trading_end_hour=13       # 13点后禁止开仓
)

# 计算买入金额
amount = pm.calculate_position_size(total_capital=2.0, tier="buy_618")

# 检查是否可以买入
can_buy, reason = pm.can_buy(
    ca="token_address",
    amount_sol=0.05,
    total_capital=2.0,
    positions=positions
)

# 计算加权平均价格
avg_price = pm.calculate_weighted_avg_price(
    entry_prices={"buy_618": 0.00004, "buy_786": 0.00003},
    entry_amounts={"buy_618": 0.06, "buy_786": 0.04},
    tiers_bought=["buy_618", "buy_786"]
)

# 获取持仓市值
value = pm.get_position_value(positions, ca="token_address")

# 获取持仓比例
ratio = pm.get_position_ratio(positions, total_capital=2.0)
```

---

### ProfitManager - 止盈止损管理器

```python
from trading import ProfitManager

pm = ProfitManager(
    profit_target_50=0.50,   # 50%止盈
    profit_target_100=1.00,  # 100%止盈
)

# 检查止盈
action = pm.check_profit_target(
    current_price=0.00006,
    avg_price=0.00004,
    profit_50_sold=False,
    ao_active=False
)

if action.should_sell:
    print(f"卖出比例: {action.percentage*100}%")
    print(f"原因: {action.reason}")

# 检查AO卖出信号
should_sell, reason = pm.check_ao_sell_signal(
    ao_values=ao_values,
    entry_price=0.00004,
    current_price=0.00006
)

# 检查止损
should_stop, reason = pm.check_stop_loss(
    current_price=0.00003,
    stop_price=0.000035
)

# 检查AO是否启动
is_active = pm.is_ao_active(ao_values)

# 计算收益率
profit_rate = pm.calculate_profit_rate(
    current_price=0.00006,
    avg_price=0.00004
)
```

---

## 🔧 完整示例

### 场景: 完整的交易流程

```python
from trading import TradeExecutor, PositionManager, ProfitManager

# 初始化
executor = TradeExecutor(wallet="your_wallet")
position_mgr = PositionManager(max_position_ratio=0.30)
profit_mgr = ProfitManager()

# 配置
total_capital = 2.0
ca = "token_address"

# ========== 步骤1: 买入 ==========

# 计算买入金额
amount_618 = position_mgr.calculate_position_size(total_capital, "buy_618")

# 检查是否可以买入
positions = executor.get_positions()
can_buy, reason = position_mgr.can_buy(
    ca=ca,
    amount_sol=amount_618,
    total_capital=total_capital,
    positions=positions
)

if not can_buy:
    print(f"不能买入: {reason}")
    exit()

# 执行买入
result = executor.buy(ca=ca, amount_sol=amount_618, limit_price=0.00004)

if not result.success:
    print(f"买入失败: {result.error}")
    exit()

print(f"买入成功: {amount_618} SOL")

# ========== 步骤2: 持仓监控 ==========

# 记录买入信息
entry_prices = {"buy_618": 0.00004}
entry_amounts = {"buy_618": amount_618}
tiers_bought = ["buy_618"]

# 计算加权均价
avg_price = position_mgr.calculate_weighted_avg_price(
    entry_prices, entry_amounts, tiers_bought
)

# 监控价格
current_price = 0.00006  # 从K线获取

# 检查止盈
action = profit_mgr.check_profit_target(
    current_price=current_price,
    avg_price=avg_price,
    profit_50_sold=False,
    ao_active=False
)

if action.should_sell:
    print(f"触发止盈: {action.reason}")
    
    # 执行卖出
    result = executor.sell(ca=ca, percentage=action.percentage)
    
    if result.success:
        print(f"卖出成功: {action.percentage*100}%")
```

---

## 🧪 测试

运行测试:

```bash
python3 test_trading.py
```

测试覆盖:
- ✅ 仓位计算
- ✅ 加权平均价格
- ✅ 仓位上限检查
- ✅ 持仓市值计算
- ✅ 止盈检查（50%/100%）
- ✅ AO卖出信号
- ✅ 止损检查
- ✅ 完整交易流程

测试结果:
```
============================================================
🎉 所有测试通过！
============================================================
```

---

## 📊 配置参数

### PositionManager

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_position_ratio` | 0.30 | 单币最大仓位比例 |
| `min_position_sol` | 0.005 | 最小买入金额（SOL） |
| `trading_start_hour` | 0 | 交易开始时间（北京时间） |
| `trading_end_hour` | 13 | 交易结束时间（北京时间） |

### ProfitManager

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `profit_target_50` | 0.50 | 50%止盈目标 |
| `profit_target_100` | 1.00 | 100%止盈目标 |
| `ao_threshold_normal` | 0.00003500 | AO正常阈值（35k） |
| `ao_profit_threshold` | 0.50 | AO低时的收益率要求 |

---

## 🎯 设计原则

### 1. 单一职责

每个类只负责一个功能:
- `TradeExecutor`: 只负责交易执行
- `PositionManager`: 只负责仓位管理
- `ProfitManager`: 只负责止盈止损

### 2. 依赖注入

所有配置通过构造函数传入，便于测试和复用。

### 3. 返回值明确

使用 `dataclass` 定义返回值结构:
- `TradeResult`: 交易结果
- `ProfitAction`: 止盈动作

### 4. 无副作用

所有方法都是纯函数，不修改外部状态。

### 5. 易于测试

所有逻辑都可以独立测试，不依赖外部API。

---

## 📁 文件结构

```
logearn-trading-skills/
├── trading/
│   ├── __init__.py           # 模块入口
│   ├── executor.py           # 交易执行器 (235行)
│   ├── position_manager.py   # 仓位管理器 (185行)
│   ├── profit_manager.py     # 止盈止损管理器 (195行)
│   └── README.md            # 详细文档
├── test_trading.py           # 完整测试 (280行)
├── TRADING_MODULE_SUMMARY.md # 总结文档
├── README.md                # 本文档
├── .gitignore
└── requirements.txt
```

---

## 💡 优势

### 1. 模块化

- ✅ 每个模块职责清晰
- ✅ 易于维护和扩展
- ✅ 可以独立测试

### 2. 可复用

- ✅ 可以在其他项目中使用
- ✅ 不依赖特定交易系统
- ✅ 配置灵活

### 3. 可测试

- ✅ 100%测试覆盖
- ✅ 不需要真实API
- ✅ 快速验证逻辑

### 4. 易于理解

- ✅ 代码结构清晰
- ✅ 文档完善
- ✅ 示例丰富

---

## 🔄 集成到其他项目

### 示例: 集成到Phase2

```python
# phase2_runner.py

from trading import TradeExecutor, PositionManager, ProfitManager

# 初始化
executor = TradeExecutor(wallet=WALLET)
position_mgr = PositionManager()
profit_mgr = ProfitManager()

# 替换原有逻辑
def exec_buy(ca, level_price, amount_sol, current_price=None):
    result = executor.buy(ca, amount_sol, level_price, current_price)
    return {"code": result.code, "error": result.error}

def can_buy(ca, amount_sol, total_capital, current_price=None):
    positions = executor.get_positions()
    can_buy, reason = position_mgr.can_buy(
        ca, amount_sol, total_capital, positions
    )
    return can_buy
```

---

## 📚 文档

- [trading/README.md](trading/README.md) - 详细的模块文档
- [TRADING_MODULE_SUMMARY.md](TRADING_MODULE_SUMMARY.md) - 模块总结

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 License

MIT License

---

## 🙏 致谢

感谢LogEarn提供的API支持。

---

**开发时间**: 2026-05-09  
**版本**: 1.0.0  
**状态**: 🟢 稳定  
**测试**: ✅ 通过
