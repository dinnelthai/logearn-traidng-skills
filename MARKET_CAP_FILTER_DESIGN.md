# 市值过滤功能设计方案

## 📋 需求描述

**核心需求**：只有当市值第一次达到180k时才开始回测交易

**具体要求**：
1. ✅ 必须是"第一次"遇到180k市值
2. ✅ 达到180k后，允许市值波动（可以回调到100k或涨到200k）
3. ✅ 在达到180k之前的K线数据不参与交易检测

---

## 🎯 设计方案

### 方案选择

**推荐方案**：在K线数据中添加市值字段

**原因**：
- ✅ 灵活性高：支持任意市值数据源
- ✅ 解耦性好：不依赖总供应量等外部数据
- ✅ 易于测试：可以直接构造测试数据
- ✅ 性能好：避免重复计算

---

## 🔧 实现设计

### 1. 扩展Kline数据结构

```python
@dataclass
class Kline:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_cap: float = 0.0  # 新增：市值（单位：k，即千美元）
```

**说明**：
- `market_cap` 默认值为0，向后兼容
- 单位为k（千），例如 180k = 180.0

---

### 2. 新增市值过滤函数

```python
def filter_klines_by_market_cap(
    klines: List[Kline],
    min_market_cap: float = 180.0,  # 单位：k
    require_first_touch: bool = True
) -> List[Kline]:
    """
    根据市值过滤K线数据
    
    Args:
        klines: K线数据列表
        min_market_cap: 最小市值阈值（单位：k）
        require_first_touch: 是否要求"第一次"达到阈值
    
    Returns:
        List[Kline]: 过滤后的K线数据
        
    逻辑：
        1. 找到第一次市值 >= min_market_cap 的K线索引
        2. 从该索引开始返回所有后续K线
        3. 如果从未达到阈值，返回空列表
    """
```

---

### 3. 更新trade_checker函数

```python
def check_single_trade(
    klines: List[Kline], 
    total_capital: float = 2.0,
    config = None,
    min_market_cap: float = None  # 新增参数
) -> Dict:
    """
    检测K线是否符合一次完整交易（买入→卖出）
    
    Args:
        klines: K线数据列表
        total_capital: 总资金（SOL）
        config: 交易配置
        min_market_cap: 最小市值阈值（单位：k），None表示不过滤
    """
    
    # 市值过滤
    if min_market_cap is not None:
        klines = filter_klines_by_market_cap(klines, min_market_cap)
        if not klines:
            return {
                "matched": False,
                "buy_points": [],
                "sell_points": [],
                "profit": None,
                "filter_reason": f"市值未达到{min_market_cap}k"
            }
    
    # ... 原有逻辑 ...
```

---

### 4. 更新parse_klines函数

```python
def parse_klines(raw: list[dict]) -> list[Kline]:
    return [
        Kline(
            time=int(r["time"]),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            volume=float(r["volume"]) if r.get("volume") else 0.0,
            market_cap=float(r.get("market_cap", 0.0))  # 新增
        )
        for r in raw
    ]
```

---

## 📊 使用示例

### 示例1：基本使用

```python
from trading.trade_checker import check_single_trade_from_raw

# K线数据（包含市值）
raw_klines = [
    {
        "time": 1000000,
        "open": 0.0001,
        "high": 0.00011,
        "low": 0.00009,
        "close": 0.0001,
        "volume": "1000000",
        "market_cap": 150.0  # 150k，未达到180k
    },
    {
        "time": 1003600,
        "open": 0.00012,
        "high": 0.00013,
        "low": 0.00011,
        "close": 0.00012,
        "volume": "1000000",
        "market_cap": 185.0  # 185k，第一次达到180k ✅
    },
    {
        "time": 1007200,
        "open": 0.00011,
        "high": 0.00012,
        "low": 0.0001,
        "close": 0.00011,
        "volume": "1000000",
        "market_cap": 120.0  # 回调到120k，仍然保留 ✅
    },
    # ... 更多K线
]

# 检测交易（市值过滤：180k）
result = check_single_trade_from_raw(
    raw_klines,
    total_capital=2.0,
    min_market_cap=180.0  # 新增参数
)

if result["matched"]:
    print("✅ 匹配到完整交易")
    print(f"买入点数: {len(result['buy_points'])}")
    print(f"卖出点数: {len(result['sell_points'])}")
else:
    print("❌ 未匹配到完整交易")
    if "filter_reason" in result:
        print(f"原因: {result['filter_reason']}")
```

### 示例2：不使用市值过滤

```python
# 不传入 min_market_cap 参数，或传入 None
result = check_single_trade_from_raw(raw_klines, total_capital=2.0)
# 等同于
result = check_single_trade_from_raw(raw_klines, total_capital=2.0, min_market_cap=None)
```

---

## 🧪 测试用例

### 测试1：第一次达到180k

```python
def test_market_cap_first_touch():
    """测试：第一次达到180k时开始回测"""
    klines = [
        # 市值 < 180k，不参与
        create_kline(market_cap=150.0),
        create_kline(market_cap=170.0),
        # 第一次达到180k，从这里开始
        create_kline(market_cap=185.0),  # ← 起始点
        create_kline(market_cap=190.0),
        create_kline(market_cap=200.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    assert len(filtered) == 3  # 最后3根K线
    assert filtered[0].market_cap == 185.0
```

### 测试2：达到后回调

```python
def test_market_cap_pullback():
    """测试：达到180k后回调到100k仍然保留"""
    klines = [
        create_kline(market_cap=150.0),
        create_kline(market_cap=185.0),  # 第一次达到
        create_kline(market_cap=100.0),  # 回调，仍保留
        create_kline(market_cap=120.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    assert len(filtered) == 3  # 从185.0开始的所有K线
```

### 测试3：从未达到180k

```python
def test_market_cap_never_reached():
    """测试：从未达到180k"""
    klines = [
        create_kline(market_cap=150.0),
        create_kline(market_cap=170.0),
        create_kline(market_cap=175.0),
    ]
    
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    assert len(filtered) == 0  # 空列表
```

### 测试4：向后兼容（无市值数据）

```python
def test_backward_compatibility():
    """测试：向后兼容（K线无market_cap字段）"""
    klines = [
        Kline(time=1000000, open=0.1, high=0.11, low=0.09, close=0.1, volume=1000),
        Kline(time=1003600, open=0.12, high=0.13, low=0.11, close=0.12, volume=1000),
    ]
    
    # 所有market_cap默认为0，不会通过过滤
    filtered = filter_klines_by_market_cap(klines, min_market_cap=180.0)
    
    assert len(filtered) == 0
```

---

## 📝 实现步骤

### 阶段1：核心功能实现
1. ✅ 扩展 `Kline` 数据结构
2. ✅ 更新 `parse_klines` 函数
3. ✅ 实现 `filter_klines_by_market_cap` 函数
4. ✅ 更新 `check_single_trade` 函数
5. ✅ 更新 `check_single_trade_from_raw` 函数

### 阶段2：测试验证
1. ✅ 编写单元测试
2. ✅ 编写集成测试
3. ✅ 更新使用示例

### 阶段3：文档更新
1. ✅ 更新 README
2. ✅ 更新 API 文档
3. ✅ 添加使用示例

---

## ⚠️ 注意事项

1. **向后兼容性**
   - `market_cap` 字段默认为0
   - `min_market_cap` 参数默认为None（不过滤）
   - 不影响现有代码

2. **市值单位**
   - 统一使用k（千）作为单位
   - 180k = 180.0
   - 避免使用180000这样的大数字

3. **边界情况**
   - 市值正好等于180k时，应该包含该K线
   - 空K线列表应返回空列表
   - 所有K线市值都小于阈值时，返回空列表

4. **性能考虑**
   - 过滤操作在O(n)时间复杂度
   - 只遍历一次K线数据
   - 不影响后续交易检测性能

---

## ✅ 验收标准

1. ✅ 功能正确：第一次达到180k时开始回测
2. ✅ 波动支持：达到后允许市值回调
3. ✅ 向后兼容：不影响现有代码
4. ✅ 测试覆盖：所有边界情况都有测试
5. ✅ 文档完整：使用说明清晰

---

**设计完成，等待实现！** 🚀
