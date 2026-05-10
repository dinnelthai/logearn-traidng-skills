# LogEarn Skills 配置指南

## 1. 安装 LogEarn Skills

```bash
npx skills add logearn/logearn-skills
```

## 2. 设置环境变量

安装完成后，需要设置 LogEarn CLI 路径：

### macOS/Linux

```bash
# 找到 logearn-cli.py 路径
# 通常在 ~/.hermes/skills/logearn/logearn-cli.py

# 设置环境变量（临时）
export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"
export LOGEARN_API_KEY="your_api_key"

# 或添加到 ~/.zshrc 或 ~/.bashrc（永久）
echo 'export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"' >> ~/.zshrc
echo 'export LOGEARN_API_KEY="your_api_key"' >> ~/.zshrc
source ~/.zshrc
```

### Windows

```cmd
set LOGEARN_CLI_PATH=C:\Users\YourName\.hermes\skills\logearn\logearn-cli.py
set LOGEARN_API_KEY=your_api_key
```

## 3. 验证安装

```bash
# 测试 LogEarn CLI
python3 $LOGEARN_CLI_PATH log-get-token-info --chain 3 --token HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump

# 测试 papertrading
papertrading HSznAnNhSFgyRWiZh4m7pBmtjHsSLi4Dbmjp18zppump 180k
```

## 4. 可选配置

```bash
# 数据库路径（可选）
export BACKTEST_DB="$HOME/backtest/data/backtest.db"

# 缓存路径（可选）
export BACKTEST_CACHE="$HOME/backtest/cache"
```

## 5. 完整示例

```bash
# ~/.zshrc 或 ~/.bashrc
export LOGEARN_CLI_PATH="$HOME/.hermes/skills/logearn/logearn-cli.py"
export LOGEARN_API_KEY="sk_your_api_key_here"
export BACKTEST_DB="$HOME/backtest/data/backtest.db"
export BACKTEST_CACHE="$HOME/backtest/cache"
```

重新加载配置：

```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

## 6. 故障排查

### 问题：无法获取代币信息

```bash
# 检查 LOGEARN_CLI_PATH 是否设置
echo $LOGEARN_CLI_PATH

# 检查文件是否存在
ls -l $LOGEARN_CLI_PATH

# 检查 API Key 是否设置
echo $LOGEARN_API_KEY

# 手动测试 CLI
python3 $LOGEARN_CLI_PATH log-get-token-info --chain 3 --token <CA地址>
```

### 问题：找不到 logearn-cli.py

```bash
# 查找文件位置
find ~ -name "logearn-cli.py" 2>/dev/null

# 或使用 locate
locate logearn-cli.py
```

---

**提示**: 如果你还没有 LogEarn API Key，请访问 LogEarn 官网获取。
