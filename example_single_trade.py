#!/usr/bin/env python3
"""
单次交易示例 - 展示如何使用交易接口只交易1次
"""

import os
from trading.single_trade_bot import run_single_trade


def get_klines_from_gmgn(ca: str):
    """
    从GMGN获取K线数据（示例）
    
    Args:
        ca: 代币地址
    
    Returns:
        List[dict]: K线数据
    """
    # TODO: 实现从GMGN API获取K线
    # 这里需要调用实际的API
    import requests
    
    try:
        # 示例API调用（需要替换为实际API）
        url = f"https://gmgn.ai/api/v1/klines/{ca}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("klines", [])
        else:
            print(f"获取K线失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"获取K线异常: {e}")
        return []


def main():
    """主函数"""
    # 从环境变量获取配置
    wallet = os.getenv("WALLET_ADDRESS")
    ca = os.getenv("TOKEN_CA")
    
    if not wallet or not ca:
        print("❌ 请设置环境变量:")
        print("   export WALLET_ADDRESS='你的钱包地址'")
        print("   export TOKEN_CA='代币地址'")
        print("   export LOGEARN_API_KEY='你的API Key'")
        return
    
    # 配置参数
    total_capital = 2.0  # 总资金 2 SOL
    check_interval = 60  # 每60秒检查一次
    
    print("="*80)
    print("🤖 单次交易机器人")
    print("="*80)
    print(f"钱包地址: {wallet}")
    print(f"代币地址: {ca}")
    print(f"总资金: {total_capital} SOL")
    print(f"检查间隔: {check_interval}秒")
    print("="*80)
    print()
    
    # 创建K线提供函数
    def klines_provider():
        return get_klines_from_gmgn(ca)
    
    # 运行单次交易
    try:
        run_single_trade(
            wallet=wallet,
            ca=ca,
            klines_provider=klines_provider,
            total_capital=total_capital,
            check_interval=check_interval
        )
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
