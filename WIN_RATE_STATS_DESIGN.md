# 交易胜率统计功能设计

**设计时间**: 2026-05-10  
**功能**: 统计每个币第N次交易的胜率  
**目标**: 分析第1次、第2次、第3次...交易的成功率

---

## 📋 需求分析

### 核心需求
统计每个币的交易胜率，按交易次数分组：
- **第1次交易胜率**：所有币的第1次交易中，盈利的比例
- **第2次交易胜率**：所有币的第2次交易中，盈利的比例
- **第3次交易胜率**：所有币的第3次交易中，盈利的比例
- ...以此类推

### 使用场景
1. **策略优化**：判断是否应该对同一个币进行多次交易
2. **风险控制**：如果第2次、第3次胜率低，可以设置规则避免重复交易
3. **数据分析**：了解交易策略在不同交易次数下的表现

---

## 🎯 设计方案

### 数据结构

#### 1. 单个币的交易记录
```python
{
    "ca": "token_address",
    "symbol": "TOKEN",
    "trades": [
        {
            "trade_number": 1,  # 第几次交易
            "matched": True,
            "profit_sol": 0.036,
            "profit_rate": 0.60,  # 60%
            "is_win": True,  # 是否盈利
            "buy_time": 1000000,
            "sell_time": 1005000,
            "market_cap_at_buy": 133.0,  # K
            "market_cap_at_sell": 178.5  # K
        },
        {
            "trade_number": 2,  # 第2次交易
            "matched": True,
            "profit_sol": -0.015,
            "profit_rate": -0.25,  # -25%
            "is_win": False,  # 亏损
            "buy_time": 1010000,
            "sell_time": 1012000,
            "market_cap_at_buy": 200.0,
            "market_cap_at_sell": 150.0
        }
    ]
}
```

#### 2. 胜率统计结果
```python
{
    "total_tokens": 100,  # 总共分析的币数
    "stats_by_trade_number": {
        1: {  # 第1次交易
            "total_trades": 100,  # 总交易数
            "wins": 65,  # 盈利次数
            "losses": 35,  # 亏损次数
            "win_rate": 0.65,  # 胜率 65%
            "avg_profit_rate": 0.45,  # 平均收益率
            "avg_win_profit": 0.80,  # 平均盈利收益率
            "avg_loss_profit": -0.30,  # 平均亏损收益率
            "total_profit_sol": 12.5  # 总利润
        },
        2: {  # 第2次交易
            "total_trades": 50,  # 只有50个币有第2次交易
            "wins": 20,
            "losses": 30,
            "win_rate": 0.40,  # 胜率 40%
            "avg_profit_rate": -0.10,
            "avg_win_profit": 0.60,
            "avg_loss_profit": -0.40,
            "total_profit_sol": -2.5
        },
        3: {  # 第3次交易
            "total_trades": 15,
            "wins": 5,
            "losses": 10,
            "win_rate": 0.33,  # 胜率 33%
            "avg_profit_rate": -0.20,
            "avg_win_profit": 0.50,
            "avg_loss_profit": -0.45,
            "total_profit_sol": -1.8
        }
    },
    "summary": {
        "best_trade_number": 1,  # 胜率最高的是第1次交易
        "worst_trade_number": 3,  # 胜率最低的是第3次交易
        "recommendation": "建议只进行第1次交易，避免重复交易"
    }
}
```

---

## 🔧 实现设计

### 1. 核心函数

#### `analyze_token_trades()`
分析单个币的所有交易

```python
def analyze_token_trades(
    ca: str,
    raw_klines: List[dict],
    total_capital: float = 2.0,
    min_market_cap: float = 180.0,
    max_trades: int = 5  # 最多分析5次交易
) -> Dict:
    """
    分析单个币的多次交易
    
    逻辑：
    1. 第1次交易：使用完整K线数据
    2. 第2次交易：从第1次卖出后开始
    3. 第3次交易：从第2次卖出后开始
    ...
    
    Returns:
        {
            "ca": "...",
            "trades": [...]
        }
    """
```

#### `calculate_win_rate_stats()`
统计所有币的胜率

```python
def calculate_win_rate_stats(
    tokens_trades: List[Dict]
) -> Dict:
    """
    统计胜率
    
    Args:
        tokens_trades: 所有币的交易记录列表
    
    Returns:
        胜率统计结果
    """
```

#### `print_win_rate_report()`
打印胜率报告

```python
def print_win_rate_report(stats: Dict):
    """
    打印胜率统计报告
    
    输出格式：
    ==========================================
    📊 交易胜率统计报告
    ==========================================
    
    总分析币数: 100
    
    第1次交易:
      总交易数: 100
      盈利次数: 65
      亏损次数: 35
      胜率: 65.0%
      平均收益率: +45.0%
      总利润: +12.5 SOL
    
    第2次交易:
      总交易数: 50
      盈利次数: 20
      亏损次数: 30
      胜率: 40.0%
      平均收益率: -10.0%
      总利润: -2.5 SOL
    
    第3次交易:
      总交易数: 15
      盈利次数: 5
      亏损次数: 10
      胜率: 33.3%
      平均收益率: -20.0%
      总利润: -1.8 SOL
    
    ==========================================
    💡 建议
    ==========================================
    ✅ 第1次交易胜率最高 (65.0%)
    ❌ 避免第2次、第3次交易（胜率低于50%）
    """
```

---

### 2. 交易次数识别逻辑

#### 方案A：基于时间窗口（推荐）
```python
def split_klines_by_trades(
    klines: List[Kline],
    cooldown_hours: int = 24  # 冷却期：24小时
) -> List[List[Kline]]:
    """
    将K线数据分割成多次交易
    
    逻辑：
    1. 第1次交易完成后，等待24小时冷却期
    2. 冷却期后的K线数据作为第2次交易
    3. 以此类推
    
    Returns:
        [
            [第1次交易的K线],
            [第2次交易的K线],
            [第3次交易的K线],
            ...
        ]
    """
```

#### 方案B：基于卖出点分割（更精确）
```python
def split_trades_by_sell_points(
    klines: List[Kline]
) -> List[Dict]:
    """
    基于卖出点分割交易
    
    逻辑：
    1. 运行第1次回测，找到卖出点
    2. 从卖出点后的K线开始第2次回测
    3. 重复直到没有更多交易
    
    Returns:
        [
            {
                "trade_number": 1,
                "klines": [...],
                "result": {...}
            },
            ...
        ]
    """
```

---

### 3. 数据存储

#### 选项1：JSON文件
```python
# 保存到文件
{
    "tokens": [
        {
            "ca": "...",
            "symbol": "...",
            "trades": [...]
        }
    ],
    "stats": {...}
}
```

#### 选项2：SQLite数据库（推荐）
```sql
-- 币表
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY,
    ca TEXT UNIQUE,
    symbol TEXT,
    first_seen TIMESTAMP
);

-- 交易表
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    token_id INTEGER,
    trade_number INTEGER,  -- 第几次交易
    matched BOOLEAN,
    profit_sol REAL,
    profit_rate REAL,
    is_win BOOLEAN,
    buy_time TIMESTAMP,
    sell_time TIMESTAMP,
    market_cap_at_buy REAL,
    market_cap_at_sell REAL,
    FOREIGN KEY (token_id) REFERENCES tokens(id)
);

-- 胜率统计视图
CREATE VIEW win_rate_by_trade_number AS
SELECT 
    trade_number,
    COUNT(*) as total_trades,
    SUM(CASE WHEN is_win THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN NOT is_win THEN 1 ELSE 0 END) as losses,
    AVG(CASE WHEN is_win THEN 1.0 ELSE 0.0 END) as win_rate,
    AVG(profit_rate) as avg_profit_rate,
    SUM(profit_sol) as total_profit_sol
FROM trades
WHERE matched = 1
GROUP BY trade_number
ORDER BY trade_number;
```

---

## 📊 使用示例

### 示例1：分析单个币的多次交易

```python
from trading.win_rate_analyzer import analyze_token_trades

# 获取K线数据（假设有很长的历史数据）
raw_klines = get_klines("token_address", days=90)

# 分析多次交易
result = analyze_token_trades(
    ca="token_address",
    raw_klines=raw_klines,
    total_capital=2.0,
    min_market_cap=180.0,
    max_trades=5  # 最多分析5次交易
)

print(f"币地址: {result['ca']}")
print(f"总交易次数: {len(result['trades'])}")

for trade in result['trades']:
    print(f"\n第{trade['trade_number']}次交易:")
    print(f"  匹配: {trade['matched']}")
    if trade['matched']:
        print(f"  收益率: {trade['profit_rate']*100:+.2f}%")
        print(f"  盈利: {'✅' if trade['is_win'] else '❌'}")
```

### 示例2：批量分析多个币

```python
from trading.win_rate_analyzer import (
    analyze_token_trades,
    calculate_win_rate_stats,
    print_win_rate_report
)

# 获取所有币的列表
tokens = [
    {"ca": "addr1", "symbol": "TOKEN1"},
    {"ca": "addr2", "symbol": "TOKEN2"},
    # ... 100个币
]

# 分析所有币
all_trades = []
for token in tokens:
    raw_klines = get_klines(token['ca'], days=90)
    result = analyze_token_trades(
        ca=token['ca'],
        raw_klines=raw_klines
    )
    all_trades.append(result)

# 计算胜率统计
stats = calculate_win_rate_stats(all_trades)

# 打印报告
print_win_rate_report(stats)
```

### 示例3：导出到数据库

```python
from trading.win_rate_analyzer import save_to_database

# 保存到SQLite
save_to_database(
    trades_data=all_trades,
    db_path="win_rate_stats.db"
)

# 查询统计
import sqlite3
conn = sqlite3.connect("win_rate_stats.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM win_rate_by_trade_number")
for row in cursor.fetchall():
    print(row)
```

---

## 🎨 可视化设计

### 1. 胜率对比图
```
第1次交易: ████████████████████ 65%
第2次交易: ████████████         40%
第3次交易: ██████               33%
第4次交易: ████                 25%
第5次交易: ███                  20%
```

### 2. 收益率分布
```
第1次交易:
  盈利: 65次, 平均 +80%
  亏损: 35次, 平均 -30%
  
第2次交易:
  盈利: 20次, 平均 +60%
  亏损: 30次, 平均 -40%
```

### 3. 累计收益曲线
```
         ┌─────────────────────────────┐
  +15 SOL│         ●                   │ 第1次交易
         │        ╱                    │
  +10 SOL│       ╱                     │
         │      ●                      │
   +5 SOL│     ╱                       │
         │    ╱                        │
    0 SOL├───●─────────────────────────┤
         │           ●                 │ 第2次交易
   -5 SOL│            ╲                │
         │             ●               │ 第3次交易
  -10 SOL└─────────────────────────────┘
         1st   2nd   3rd   4th   5th
```

---

## 🔍 高级功能

### 1. 按市值区间统计
```python
stats = calculate_win_rate_stats(
    all_trades,
    group_by_market_cap=True,
    market_cap_ranges=[
        (0, 100),      # < 100K
        (100, 500),    # 100K - 500K
        (500, 1000),   # 500K - 1M
        (1000, 5000),  # 1M - 5M
        (5000, None)   # > 5M
    ]
)
```

### 2. 按时间段统计
```python
stats = calculate_win_rate_stats(
    all_trades,
    group_by_time=True,
    time_periods=[
        "2024-01",
        "2024-02",
        "2024-03"
    ]
)
```

### 3. 过滤条件
```python
stats = calculate_win_rate_stats(
    all_trades,
    filters={
        "min_market_cap": 180.0,  # 只统计市值 >= 180K 的
        "min_profit_rate": -0.5,  # 排除亏损超过50%的异常交易
        "max_profit_rate": 10.0   # 排除收益超过1000%的异常交易
    }
)
```

---

## 📝 实现步骤

### 阶段1：核心功能（必需）
1. ✅ 实现 `analyze_token_trades()` - 分析单币多次交易
2. ✅ 实现 `split_trades_by_sell_points()` - 分割交易
3. ✅ 实现 `calculate_win_rate_stats()` - 统计胜率
4. ✅ 实现 `print_win_rate_report()` - 打印报告

### 阶段2：数据存储（推荐）
1. ✅ 设计数据库schema
2. ✅ 实现 `save_to_database()` - 保存到数据库
3. ✅ 实现 `load_from_database()` - 从数据库加载

### 阶段3：高级功能（可选）
1. ⭕ 按市值区间统计
2. ⭕ 按时间段统计
3. ⭕ 可视化图表
4. ⭕ Web界面展示

---

## ⚠️ 注意事项

### 1. 数据质量
- 确保K线数据足够长（建议至少30-90天）
- 确保市值数据准确
- 处理数据缺失情况

### 2. 交易识别
- 定义清晰的"交易结束"标准
- 避免重叠交易
- 处理未完成的交易

### 3. 统计准确性
- 排除异常数据（如价格异常波动）
- 考虑样本量（交易次数太少时统计不可靠）
- 区分"未交易"和"交易失败"

### 4. 性能优化
- 批量处理多个币
- 缓存中间结果
- 使用数据库索引

---

## ✅ 预期输出

### 控制台输出
```
==========================================
📊 交易胜率统计报告
==========================================

总分析币数: 100
总交易数: 165

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第1次交易:
  总交易数: 100
  盈利次数: 65 (65.0%)
  亏损次数: 35 (35.0%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  胜率: 65.0% ████████████████████
  平均收益率: +45.0%
  平均盈利: +80.0%
  平均亏损: -30.0%
  总利润: +12.5 SOL

第2次交易:
  总交易数: 50
  盈利次数: 20 (40.0%)
  亏损次数: 30 (60.0%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  胜率: 40.0% ████████████
  平均收益率: -10.0%
  平均盈利: +60.0%
  平均亏损: -40.0%
  总利润: -2.5 SOL

第3次交易:
  总交易数: 15
  盈利次数: 5 (33.3%)
  亏损次数: 10 (66.7%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  胜率: 33.3% ██████
  平均收益率: -20.0%
  平均盈利: +50.0%
  平均亏损: -45.0%
  总利润: -1.8 SOL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 建议:
  ✅ 第1次交易表现最佳 (胜率 65.0%)
  ⚠️  第2次交易胜率下降至 40.0%
  ❌ 避免第3次及以后的交易 (胜率 < 35%)
  
  建议策略: 只进行第1次交易，避免重复交易

==========================================
```

---

**设计完成，等待实现！** 🚀
