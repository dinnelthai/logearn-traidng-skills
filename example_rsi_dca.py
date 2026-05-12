#!/usr/bin/env python3
"""
RSI定投示例 - 展示如何使用RSI定投机器人
"""

import os
from trading.rsi_dca_bot import run_rsi_dca


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
    dca_amount = 0.1        # 每次定投0.1 SOL
    max_buy_count = 10      # 最多定投10次
    interval = '1h'         # 1小时K线
    check_interval = 300    # 每5分钟检查一次
    
    print("="*80)
    print("🤖 RSI定投机器人")
    print("="*80)
    print(f"代币地址: {ca}")
    print(f"定投金额: {dca_amount} SOL")
    print(f"最大次数: {max_buy_count}")
    print(f"K线周期: {interval}")
    print(f"检查间隔: {check_interval}秒")
    print("="*80)
    print()
    
    # 运行RSI定投
    try:
        run_rsi_dca(
            ca=ca,
            dca_amount=dca_amount,
            max_buy_count=max_buy_count,
            interval=interval,
            check_interval=check_interval
        )
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
