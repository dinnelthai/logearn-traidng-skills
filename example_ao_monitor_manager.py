#!/usr/bin/env python3
"""
AO监控管理器使用示例
支持添加、移除、查看、停止多个AO监控任务
"""

import os
import time
from trading import (
    add_ao_monitor, remove_ao_monitor, 
    stop_ao_monitor, start_ao_monitor,
    list_ao_monitors, show_ao_monitors, 
    stop_all_ao_monitors
)

# 设置环境变量
os.environ["LOGEARN_API_KEY"] = "your_api_key"


def example_basic_usage():
    """基础使用示例"""
    print("=" * 80)
    print("示例1: 基础使用")
    print("=" * 80)
    
    # 1. 添加监控
    print("\n1️⃣ 添加AO监控...")
    add_ao_monitor(
        ca="FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump",
        entry_price=0.00004,
        sell_percentage=1.0
    )
    
    # 2. 查看监控状态
    print("\n2️⃣ 查看监控状态...")
    show_ao_monitors()
    
    # 3. 等待一段时间
    print("\n3️⃣ 监控运行中...")
    time.sleep(10)
    
    # 4. 停止监控
    print("\n4️⃣ 停止监控...")
    stop_ao_monitor("FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump")
    
    # 5. 移除监控
    print("\n5️⃣ 移除监控...")
    remove_ao_monitor("FDBjQdN4Uf8rsJfn9eNRbmNjaQktCdqJ63Ptijfdpump")


def example_multiple_monitors():
    """多个监控示例"""
    print("\n" + "=" * 80)
    print("示例2: 管理多个监控")
    print("=" * 80)
    
    # 1. 添加多个监控
    print("\n1️⃣ 添加多个监控...")
    
    cas = [
        ("CA1地址", 0.00004),
        ("CA2地址", 0.00005),
        ("CA3地址", None),  # 不提供买入价
    ]
    
    for ca, entry_price in cas:
        add_ao_monitor(ca, entry_price=entry_price)
    
    # 2. 查看所有监控
    print("\n2️⃣ 查看所有监控...")
    show_ao_monitors()
    
    # 3. 列出监控（获取数据）
    print("\n3️⃣ 获取监控数据...")
    monitors = list_ao_monitors()
    for m in monitors:
        print(f"  - {m['ca_short']}: {'运行中' if m['is_running'] else '已停止'}")
    
    # 4. 停止所有监控
    print("\n4️⃣ 停止所有监控...")
    stop_all_ao_monitors()


def example_dynamic_management():
    """动态管理示例"""
    print("\n" + "=" * 80)
    print("示例3: 动态管理监控")
    print("=" * 80)
    
    ca = "CA地址"
    
    # 1. 添加监控
    print("\n1️⃣ 添加监控...")
    add_ao_monitor(ca, entry_price=0.00004)
    
    # 2. 运行一段时间
    print("\n2️⃣ 运行30秒...")
    time.sleep(30)
    
    # 3. 暂停监控
    print("\n3️⃣ 暂停监控...")
    stop_ao_monitor(ca)
    
    # 4. 查看状态
    print("\n4️⃣ 查看状态...")
    show_ao_monitors()
    
    # 5. 重新启动
    print("\n5️⃣ 重新启动...")
    start_ao_monitor(ca)
    
    # 6. 再运行一段时间
    print("\n6️⃣ 继续运行...")
    time.sleep(30)
    
    # 7. 强制移除（即使正在运行）
    print("\n7️⃣ 强制移除...")
    remove_ao_monitor(ca, force=True)


def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 80)
    print("示例4: 错误处理")
    print("=" * 80)
    
    ca = "CA地址"
    
    # 1. 重复添加
    print("\n1️⃣ 测试重复添加...")
    add_ao_monitor(ca, entry_price=0.00004)
    add_ao_monitor(ca, entry_price=0.00004)  # 会提示已存在
    
    # 2. 移除不存在的监控
    print("\n2️⃣ 测试移除不存在的监控...")
    remove_ao_monitor("不存在的CA")
    
    # 3. 停止未运行的监控
    print("\n3️⃣ 测试停止未运行的监控...")
    stop_ao_monitor(ca)
    stop_ao_monitor(ca)  # 会提示未在运行
    
    # 4. 清理
    print("\n4️⃣ 清理...")
    remove_ao_monitor(ca)


def example_interactive():
    """交互式管理示例"""
    print("\n" + "=" * 80)
    print("示例5: 交互式管理")
    print("=" * 80)
    
    while True:
        print("\n" + "=" * 80)
        print("AO监控管理器")
        print("=" * 80)
        print("1. 添加监控")
        print("2. 移除监控")
        print("3. 停止监控")
        print("4. 启动监控")
        print("5. 查看状态")
        print("6. 停止所有")
        print("0. 退出")
        print("=" * 80)
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == "1":
            ca = input("代币地址: ").strip()
            entry_price_str = input("买入价（留空跳过）: ").strip()
            entry_price = float(entry_price_str) if entry_price_str else None
            add_ao_monitor(ca, entry_price=entry_price)
        
        elif choice == "2":
            ca = input("代币地址: ").strip()
            force = input("强制移除？(y/n): ").strip().lower() == 'y'
            remove_ao_monitor(ca, force=force)
        
        elif choice == "3":
            ca = input("代币地址: ").strip()
            stop_ao_monitor(ca)
        
        elif choice == "4":
            ca = input("代币地址: ").strip()
            start_ao_monitor(ca)
        
        elif choice == "5":
            show_ao_monitors()
        
        elif choice == "6":
            stop_all_ao_monitors()
        
        elif choice == "0":
            print("\n👋 退出...")
            stop_all_ao_monitors()
            break
        
        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           AO监控管理器 - 使用示例                          ║
    ╚════════════════════════════════════════════════════════════╝
    
    功能：
    - 添加/移除AO监控
    - 启动/停止监控
    - 查看监控状态
    - 管理多个监控任务
    
    选择示例：
    1. 基础使用
    2. 多个监控
    3. 动态管理
    4. 错误处理
    5. 交互式管理
    """)
    
    choice = input("请选择示例 (1-5): ").strip()
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_multiple_monitors()
    elif choice == "3":
        example_dynamic_management()
    elif choice == "4":
        example_error_handling()
    elif choice == "5":
        example_interactive()
    else:
        print("❌ 无效选择")
