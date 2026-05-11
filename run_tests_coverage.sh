#!/bin/bash
# 运行测试并生成覆盖率报告

echo "=================================="
echo "运行测试并生成覆盖率报告"
echo "=================================="
echo ""

# 设置测试环境变量
export LOGEARN_API_KEY="test_key_for_testing"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 运行测试
pytest tests/ \
    -v \
    --cov=trading \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=90

# 检查退出码
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ 测试通过！覆盖率达标（>=90%）"
    echo "=================================="
    echo ""
    echo "HTML覆盖率报告: htmlcov/index.html"
    echo "打开报告: open htmlcov/index.html"
else
    echo ""
    echo "=================================="
    echo "❌ 测试失败或覆盖率不达标"
    echo "=================================="
    exit 1
fi
