#!/usr/bin/env python3
"""
AO监控示例 - 接管现有持仓并监控AO卖出信号
"""

import os
from trading import run_ao_monitor_multi, AOMonitorConfig

# 设置环境变量
os.environ["LOGEARN_API_KEY"] = "your_api_key"

# ========== 配置要监控的代币 ==========
configs = [
    # CA1: 提供买入价（推荐）
    # - AO >= 35k 绿转红 → 卖出
    # - AO < 35k 绿转红 + 收益率 > 50% → 卖出
    AOMonitorConfig(
        ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
        entry_price=0.00004,      # 提供买入价
        sell_percentage=1.0       # 卖出100%
    ),
    
    # CA2: 不提供买入价（保守模式）
    # - AO >= 35k 绿转红 → 卖出
    # - AO < 35k 绿转红 → 不卖出
    AOMonitorConfig(
        ca="另一个代币地址",
        entry_price=None,         # 不提供买入价
        sell_percentage=1.0
    ),
]

# ========== 启动监控 ==========
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           AO监控机器人 - 接管持仓自动卖出                    ║
    ╚════════════════════════════════════════════════════════════╝
    
    功能：
    - 自动监控多个代币的AO信号
    - AO绿转红时自动卖出
    
    卖出条件：
    1. 提供买入价时：
       - AO >= 35k 绿转红 → 卖出
       - AO < 35k 绿转红 + 收益率 > 50% → 卖出
    
    2. 不提供买入价时（保守模式）：
       - AO >= 35k 绿转红 → 卖出
       - AO < 35k 绿转红 → 不卖出
    
    按 Ctrl+C 可随时停止
    """)
    
    # 启动监控（会自动验证持仓）
    run_ao_monitor_multi(
        configs=configs,
        interval='5m',        # K线周期
        check_interval=60     # 检查间隔（秒）
    )
