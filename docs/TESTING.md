# 测试文档

## 概述

本项目使用pytest进行单元测试，目标覆盖率>=90%。

## 测试结构

```
tests/
├── test_kline_service.py      # K线服务测试
├── test_indicators.py          # 技术指标测试
├── test_fibonacci_trade.py     # Fibonacci交易入口测试
├── test_rsi_dca_bot.py        # RSI定投机器人测试
├── test_executor.py           # 交易执行器测试
├── test_fib_calculator.py     # Fibonacci计算测试（已有）
├── test_position_manager.py   # 仓位管理测试（已有）
├── test_profit_manager.py     # 盈亏管理测试（已有）
└── test_trade_checker.py      # 交易检测测试（已有）
```

## 运行测试

### 方式1: 使用脚本（推荐）

```bash
# 运行所有测试并生成覆盖率报告
./run_tests_coverage.sh
```

### 方式2: 使用pytest命令

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_kline_service.py

# 运行特定测试类
pytest tests/test_kline_service.py::TestKlineService

# 运行特定测试函数
pytest tests/test_kline_service.py::TestKlineService::test_init_with_api_key

# 生成覆盖率报告
pytest --cov=trading --cov-report=term-missing

# 生成HTML覆盖率报告
pytest --cov=trading --cov-report=html
```

### 方式3: 使用原有脚本

```bash
# 运行所有测试（不含覆盖率）
./run_tests.sh
```

## 覆盖率要求

- **目标覆盖率**: >=90%
- **覆盖模块**: `trading/` 目录下所有模块
- **排除文件**: 测试文件、`__pycache__`、虚拟环境

## 测试覆盖

### 1. K线服务测试 (`test_kline_service.py`)

**覆盖功能**:
- ✅ 初始化（有/无API Key）
- ✅ 获取原始K线（成功/失败）
- ✅ 获取K线对象
- ✅ 获取最新K线
- ✅ 获取所有历史K线（翻页）
- ✅ 全局单例
- ✅ 便捷函数
- ✅ 错误处理（无效周期、API错误、无数据）

**测试用例**: 15个

### 2. 技术指标测试 (`test_indicators.py`)

**覆盖功能**:
- ✅ RSI计算（上涨/下跌/横盘）
- ✅ RSI序列计算
- ✅ 不同周期RSI
- ✅ 边界情况（数据不足、全部上涨/下跌、价格不变）

**测试用例**: 12个

### 3. Fibonacci交易入口测试 (`test_fibonacci_trade.py`)

**覆盖功能**:
- ✅ 基本运行
- ✅ K线提供函数
- ✅ 默认参数
- ✅ 自定义参数

**测试用例**: 4个

### 4. RSI定投机器人测试 (`test_rsi_dca_bot.py`)

**覆盖功能**:
- ✅ 初始化（基本/自定义参数）
- ✅ 获取状态
- ✅ 执行买入（成功/失败）
- ✅ 快捷函数

**测试用例**: 6个

### 5. 交易执行器测试 (`test_executor.py`)

**覆盖功能**:
- ✅ 初始化（有/无API Key）
- ✅ 买入（成功/失败/超时/价格超限）
- ✅ 卖出（成功/失败/未找到持仓/持仓为0/部分卖出）
- ✅ 获取持仓（成功/失败/不同格式）
- ✅ 交易结果对象

**测试用例**: 14个

### 6. 已有测试

- `test_fib_calculator.py` - Fibonacci计算测试
- `test_position_manager.py` - 仓位管理测试
- `test_profit_manager.py` - 盈亏管理测试
- `test_trade_checker.py` - 交易检测测试

## 覆盖率报告

### 查看终端报告

```bash
pytest --cov=trading --cov-report=term-missing
```

输出示例:
```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
trading/__init__.py                  10      0   100%
trading/executor.py                  85      5    94%   45-47
trading/fib_calculator.py           250     12    95%
trading/indicators.py                45      2    96%
trading/kline_service.py             78      4    95%
trading/rsi_dca_bot.py              120      8    93%
---------------------------------------------------------------
TOTAL                               588     31    95%
```

### 查看HTML报告

```bash
pytest --cov=trading --cov-report=html
open htmlcov/index.html
```

HTML报告提供:
- 每个文件的覆盖率
- 未覆盖的代码行高亮显示
- 交互式浏览

## Mock策略

### 1. Mock外部依赖

```python
@patch('trading.kline_service.requests.post')
def test_get_klines(self, mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"code": 200, "data": {...}}
    mock_post.return_value = mock_response
    # 测试代码...
```

### 2. Mock环境变量

```python
with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test_key'}):
    # 测试代码...
```

### 3. Mock subprocess

```python
@patch('subprocess.run')
def test_buy(self, mock_run):
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"code": 200})
    mock_run.return_value = mock_result
    # 测试代码...
```

## 测试最佳实践

### 1. 测试命名

```python
def test_<功能>_<场景>():
    """测试<功能>（<场景>）"""
    pass
```

示例:
```python
def test_buy_success():
    """测试买入（成功）"""
    pass

def test_buy_price_exceeded():
    """测试买入（价格超限）"""
    pass
```

### 2. 测试结构

```python
def test_something():
    # 1. Arrange - 准备测试数据
    service = KlineService(api_key="test")
    
    # 2. Act - 执行被测试的代码
    result = service.get_klines("ca", interval='5m')
    
    # 3. Assert - 验证结果
    assert len(result) > 0
```

### 3. 使用Fixtures

```python
@pytest.fixture
def kline_service():
    with patch.dict('os.environ', {'LOGEARN_API_KEY': 'test'}):
        return KlineService()

def test_with_fixture(kline_service):
    result = kline_service.get_klines("ca")
    assert result is not None
```

## 持续集成

### GitHub Actions配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest --cov=trading --cov-fail-under=90
```

## 常见问题

### Q1: 如何提高覆盖率？

1. 查看HTML报告，找到未覆盖的代码行
2. 为未覆盖的代码添加测试用例
3. 重点关注边界情况和错误处理

### Q2: 如何测试异步代码？

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Q3: 如何跳过某些测试？

```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass

@pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+")
def test_something_else():
    pass
```

### Q4: 如何测试异常？

```python
def test_exception():
    with pytest.raises(ValueError, match="错误信息"):
        function_that_raises()
```

## 总结

- ✅ **覆盖率目标**: >=90%
- ✅ **测试框架**: pytest
- ✅ **Mock工具**: unittest.mock
- ✅ **覆盖率工具**: pytest-cov
- ✅ **HTML报告**: htmlcov/index.html

运行测试:
```bash
./run_tests_coverage.sh
```

查看报告:
```bash
open htmlcov/index.html
```
