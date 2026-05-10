# 🚀# LogEarn Trading Skills

基于 Fibonacci 回撤 + AO (Awesome Oscillator) 的 Solana 代币交易策略模块。

---

## 📁 项目结构

```
logearn-traidng-skills/
├── trading/              # 核心交易模块
│   ├── fib_calculator.py    # Fibonacci + AO 计算
│   ├── position_manager.py  # 仓位管理
│   ├── trade_checker.py     # 交易检测器
│   ├── win_rate_analyzer.py # 胜率分析器
│   ├── executor.py          # 交易执行器
│   └── config.py            # 配置管理
│
├── backtester/           # 回测模块
│   ├── backtest.py          # 回测主程序
│   ├── run_backtest.py      # 回测运行器
│   ├── fetch_klines.py      # K线数据获取
│   └── gen_html.py          # HTML报告生成
│
├── tests/                # 测试文件
│   ├── test_*.py            # 单元测试
│   └── test_swing_high_mcap_filter.py  # 波峰市值门槛测试
│
├── examples/             # 使用示例
│   ├── example_trade_check.py
│   ├── example_win_rate_analysis.py
│   └── example_market_cap_filter.py
│
├── diagnostics/          # 诊断工具
│   ├── diagnose_backtest_mcap.py
│   ├── add_backtest_debug.py
│   └── test_ca_mcap.py
│
├── docs/                 # 文档
│   ├── SWING_HIGH_MCAP_FILTER_GUIDE.md
│   ├── TRADE_CHECKER_GUIDE.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── ...
│
├── test_trading.py       # 集成测试
├── requirements.txt      # 依赖
├── setup.py             # 安装配置
└── README.md            # 本文件
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行示例

```bash
# 交易检测示例
python examples/example_trade_check.py

# 胜率分析示例
python examples/example_win_rate_analysis.py

# 市值过滤示例
python examples/example_market_cap_filter.py
```

### 3. 运行回测

```bash
python backtester/run_backtest.py <CA地址>
```

---

## 📊 核心功能

### 1. Fibonacci 回撤策略

- **买入档位**: 0.618, 0.786, 0.861
- **卖出档位**: 1.000 (回到波峰), 1.272 (扩展位)
- **止损**: 0.920 (波峰的92%)

### 2. AO (Awesome Oscillator) 卖出

- **零轴上方**: AO > 35k 时，绿转红第二根卖出
- **零轴下方**: AO < 35k 时，收益率 > 50% 才卖出

### 3. 仓位管理

- **分档买入**: 0.618档3%, 0.786档2%, 0.861档1%
- **分批卖出**: 1.000档卖30%, 1.272档卖50%
- **最大仓位**: 单币30%

### 4. 市值过滤（双重机制）

#### K线市值过滤
从第一次达到最小市值的K线开始分析

```python
result = analyze_token_trades(
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
