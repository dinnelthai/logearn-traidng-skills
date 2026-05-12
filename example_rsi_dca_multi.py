#!/usr/bin/env python3
"""
RSI定投示例（多代币） - 内部轮询模式

支持同时监控多个代币，内部每5分钟轮询一次
"""

from trading import run_rsi_dca_multi, DCAConfig


if __name__ == "__main__":
    # 配置多个代币定投
    configs = [
        DCAConfig(
            ca="代币1地址",
            dca_amount=0.1,          # 每次定投0.1 SOL
            max_buy_count=10,        # 最多买10次
            rsi_buy_threshold=30.0,  # RSI<30买入
            rsi_reset_threshold=50.0 # RSI>50重置
        ),
        DCAConfig(
            ca="代币2地址",
            dca_amount=0.2,          # 每次定投0.2 SOL
            max_buy_count=5          # 最多买5次
        ),
        DCAConfig(
            ca="代币3地址",
            dca_amount=0.15,         # 每次定投0.15 SOL
            max_buy_count=8          # 最多买8次
        ),
    ]
    
    # 运行定投管理器
    # 会一直运行，每5分钟检查一次所有代币
    run_rsi_dca_multi(
        configs=configs,
        interval='1h',           # 使用1小时K线
        poll_interval=300        # 每5分钟轮询一次
    )
