#!/usr/bin/env python3
"""
Fibonacci交易示例 - 对外公开接口

只需传递CA地址，内部自动处理K线获取
"""

import os
from trading import run_fibonacci_trade


def main():
    """主函数"""
    # 从环境变量获取配置
    ca = os.getenv("TOKEN_CA")
    
    if not ca:
        print("❌ 请设置环境变量:")
        print("   export TOKEN_CA='代币地址'")
        print("   export LOGEARN_API_KEY='你的API Key'")
        print("")
        print("注意: LogEarn skill与token绑定，不需要指定钱包地址")
        return
    
    # 配置参数
    total_capital = 2.0  # 总资金 2 SOL
    check_interval = 60  # 每60秒检查一次
    
    print("="*80)
    print("🤖 Fibonacci交易")
    print("="*80)
    print(f"代币地址: {ca}")
    print(f"总资金: {total_capital} SOL")
    print(f"检查间隔: {check_interval}秒")
    print(f"K线周期: 5分钟（自动获取）")
    print("="*80)
    print()
    
    # 运行Fibonacci交易（K线自动获取）
    try:
        run_fibonacci_trade(
            ca=ca,
            total_capital=total_capital,
            check_interval=check_interval
        )
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
