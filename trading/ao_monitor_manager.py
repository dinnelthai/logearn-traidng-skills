#!/usr/bin/env python3
"""
AO监控管理器 - 管理多个AO监控任务
支持添加、移除、查看、停止监控
"""

import time
import threading
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from .executor import TradeExecutor
from .kline_service import get_klines
from .fib_calculator import parse_klines, calc_ao, ao_sell_signal


@dataclass
class AOMonitorTask:
    """AO监控任务"""
    ca: str                              # 代币地址
    entry_price: Optional[float] = None  # 买入均价
    sell_percentage: float = 1.0         # 卖出比例
    interval: str = '5m'                 # K线周期
    check_interval: int = 60             # 检查间隔
    
    # 运行时状态
    thread: Optional[threading.Thread] = None
    is_running: bool = False
    is_sold: bool = False
    start_time: Optional[datetime] = None
    last_check_time: Optional[datetime] = None
    check_count: int = 0
    
    def __post_init__(self):
        self.start_time = datetime.now()


class AOMonitorManager:
    """AO监控管理器（单例）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.tasks: Dict[str, AOMonitorTask] = {}
            self.executor = TradeExecutor()
            self.initialized = True
    
    def add_monitor(self, 
                    ca: str,
                    entry_price: Optional[float] = None,
                    sell_percentage: float = 1.0,
                    interval: str = '5m',
                    check_interval: int = 60,
                    auto_start: bool = True) -> bool:
        """
        添加AO监控任务
        
        Args:
            ca: 代币地址
            entry_price: 买入均价（可选）
            sell_percentage: 卖出比例
            interval: K线周期
            check_interval: 检查间隔（秒）
            auto_start: 是否自动启动
        
        Returns:
            bool: 是否添加成功
        """
        # 检查是否已存在
        if ca in self.tasks:
            print(f"⚠️ [{ca[:8]}...] 已在监控列表中")
            return False
        
        # 验证持仓
        print(f"\n🔍 验证持仓: {ca[:8]}...")
        positions = self.executor.get_positions()
        has_position = any(p.get("token_address") == ca for p in positions)
        
        if not has_position:
            print(f"❌ [{ca[:8]}...] 无持仓，无法添加监控")
            return False
        
        position = next(p for p in positions if p.get("token_address") == ca)
        balance = float(position.get("balance", 0))
        print(f"✅ [{ca[:8]}...] 持仓: {balance:.2f} tokens")
        
        # 创建任务
        task = AOMonitorTask(
            ca=ca,
            entry_price=entry_price,
            sell_percentage=sell_percentage,
            interval=interval,
            check_interval=check_interval
        )
        
        self.tasks[ca] = task
        
        if auto_start:
            self.start_monitor(ca)
        
        print(f"✅ [{ca[:8]}...] 已添加到监控列表")
        return True
    
    def remove_monitor(self, ca: str, force: bool = False) -> bool:
        """
        移除AO监控任务
        
        Args:
            ca: 代币地址
            force: 是否强制移除（即使正在运行）
        
        Returns:
            bool: 是否移除成功
        """
        if ca not in self.tasks:
            print(f"⚠️ [{ca[:8]}...] 不在监控列表中")
            return False
        
        task = self.tasks[ca]
        
        # 如果正在运行，先停止
        if task.is_running:
            if not force:
                print(f"⚠️ [{ca[:8]}...] 正在运行，请先停止或使用 force=True")
                return False
            self.stop_monitor(ca)
        
        # 移除任务
        del self.tasks[ca]
        print(f"✅ [{ca[:8]}...] 已从监控列表移除")
        return True
    
    def start_monitor(self, ca: str) -> bool:
        """
        启动AO监控任务
        
        Args:
            ca: 代币地址
        
        Returns:
            bool: 是否启动成功
        """
        if ca not in self.tasks:
            print(f"❌ [{ca[:8]}...] 不在监控列表中")
            return False
        
        task = self.tasks[ca]
        
        if task.is_running:
            print(f"⚠️ [{ca[:8]}...] 已在运行中")
            return False
        
        if task.is_sold:
            print(f"⚠️ [{ca[:8]}...] 已卖出，无法重新启动")
            return False
        
        # 创建并启动线程
        task.thread = threading.Thread(
            target=self._monitor_loop,
            args=(ca,),
            daemon=True
        )
        task.is_running = True
        task.thread.start()
        
        print(f"✅ [{ca[:8]}...] 监控已启动")
        return True
    
    def stop_monitor(self, ca: str) -> bool:
        """
        停止AO监控任务
        
        Args:
            ca: 代币地址
        
        Returns:
            bool: 是否停止成功
        """
        if ca not in self.tasks:
            print(f"❌ [{ca[:8]}...] 不在监控列表中")
            return False
        
        task = self.tasks[ca]
        
        if not task.is_running:
            print(f"⚠️ [{ca[:8]}...] 未在运行")
            return False
        
        # 停止任务
        task.is_running = False
        
        # 等待线程结束
        if task.thread and task.thread.is_alive():
            task.thread.join(timeout=5)
        
        print(f"✅ [{ca[:8]}...] 监控已停止")
        return True
    
    def stop_all(self):
        """停止所有监控任务"""
        print("\n🛑 停止所有监控任务...")
        for ca in list(self.tasks.keys()):
            if self.tasks[ca].is_running:
                self.stop_monitor(ca)
        print("✅ 所有监控已停止")
    
    def list_monitors(self) -> List[Dict]:
        """
        列出所有监控任务
        
        Returns:
            List[Dict]: 任务列表
        """
        result = []
        for ca, task in self.tasks.items():
            result.append({
                'ca': ca,
                'ca_short': ca[:8] + '...',
                'entry_price': task.entry_price,
                'sell_percentage': task.sell_percentage,
                'is_running': task.is_running,
                'is_sold': task.is_sold,
                'start_time': task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else None,
                'last_check': task.last_check_time.strftime('%H:%M:%S') if task.last_check_time else None,
                'check_count': task.check_count
            })
        return result
    
    def print_status(self):
        """打印所有监控任务状态"""
        tasks = self.list_monitors()
        
        if not tasks:
            print("\n📋 当前无监控任务")
            return
        
        print(f"\n{'='*100}")
        print(f"📋 AO监控任务列表 ({len(tasks)}个)")
        print(f"{'='*100}")
        print(f"{'CA':<12} {'买入价':<12} {'卖出%':<8} {'状态':<8} {'已卖':<6} {'启动时间':<20} {'检查次数':<10}")
        print(f"{'-'*100}")
        
        for task in tasks:
            status = "🟢 运行中" if task['is_running'] else "⚪ 已停止"
            sold = "✅" if task['is_sold'] else "❌"
            entry = f"{task['entry_price']:.8f}" if task['entry_price'] else "未知"
            
            print(f"{task['ca_short']:<12} {entry:<12} {task['sell_percentage']*100:<7.0f}% {status:<8} {sold:<6} {task['start_time']:<20} {task['check_count']:<10}")
        
        print(f"{'='*100}\n")
    
    def get_task(self, ca: str) -> Optional[AOMonitorTask]:
        """获取任务"""
        return self.tasks.get(ca)
    
    def _monitor_loop(self, ca: str):
        """监控循环（在独立线程中运行）"""
        task = self.tasks[ca]
        
        print(f"\n🤖 [{ca[:8]}...] 开始监控AO信号...")
        print(f"   买入价: {task.entry_price if task.entry_price else '未知（保守模式）'}")
        print(f"   卖出比例: {task.sell_percentage*100:.0f}%")
        print(f"   检查间隔: {task.check_interval}秒\n")
        
        while task.is_running and not task.is_sold:
            try:
                task.check_count += 1
                task.last_check_time = datetime.now()
                
                # 1. 获取K线
                klines_data = get_klines(ca, interval=task.interval, page_size=200)
                if not klines_data:
                    print(f"⚠️ [{ca[:8]}...] 无法获取K线数据")
                    time.sleep(task.check_interval)
                    continue
                
                # 2. 解析K线
                klines = parse_klines(klines_data)
                if len(klines) < 50:
                    print(f"⚠️ [{ca[:8]}...] K线数据不足")
                    time.sleep(task.check_interval)
                    continue
                
                # 3. 计算AO
                ao_values = calc_ao(klines)
                
                # 4. 检测AO卖出信号
                current_price = klines[-1].close
                signal = ao_sell_signal(
                    ao_values=ao_values,
                    entry_price=task.entry_price,
                    current_price=current_price
                )
                
                # 5. 处理信号
                if signal and signal.get("action") == "sell":
                    print(f"\n🔔 [{ca[:8]}...] AO卖出信号触发！")
                    print(f"   原因: {signal.get('reason')}")
                    print(f"   AO值: {signal.get('ao_value'):.8f}")
                    print(f"   当前价: {current_price:.8f}")
                    
                    if task.entry_price:
                        profit_rate = (current_price - task.entry_price) / task.entry_price
                        print(f"   收益率: {profit_rate*100:.2f}%")
                    
                    # 执行卖出
                    print(f"\n📉 执行卖出 {task.sell_percentage*100:.0f}%...")
                    result = self.executor.sell(ca=ca, percentage=task.sell_percentage)
                    
                    if result.success:
                        print(f"   ✅ 卖出成功！\n")
                        task.is_sold = True
                        task.is_running = False
                    else:
                        print(f"   ❌ 卖出失败: {result.message}\n")
                
                # 6. 等待下次检查
                time.sleep(task.check_interval)
                
            except KeyboardInterrupt:
                print(f"\n⚠️ [{ca[:8]}...] 用户中断，退出...")
                task.is_running = False
                break
            except Exception as e:
                print(f"❌ [{ca[:8]}...] 错误: {e}")
                time.sleep(task.check_interval)
        
        print(f"🛑 [{ca[:8]}...] 监控已停止")


# 全局管理器实例
_manager: Optional[AOMonitorManager] = None


def get_monitor_manager() -> AOMonitorManager:
    """获取全局监控管理器实例（单例）"""
    global _manager
    if _manager is None:
        _manager = AOMonitorManager()
    return _manager


# ========== 便捷接口 ==========

def add_ao_monitor(ca: str,
                   entry_price: Optional[float] = None,
                   sell_percentage: float = 1.0,
                   interval: str = '5m',
                   check_interval: int = 60) -> bool:
    """
    添加AO监控
    
    Example:
        add_ao_monitor("CA地址", entry_price=0.00004)
    """
    manager = get_monitor_manager()
    return manager.add_monitor(ca, entry_price, sell_percentage, interval, check_interval)


def remove_ao_monitor(ca: str, force: bool = False) -> bool:
    """
    移除AO监控
    
    Example:
        remove_ao_monitor("CA地址")
        remove_ao_monitor("CA地址", force=True)  # 强制移除
    """
    manager = get_monitor_manager()
    return manager.remove_monitor(ca, force)


def stop_ao_monitor(ca: str) -> bool:
    """
    停止AO监控（不移除）
    
    Example:
        stop_ao_monitor("CA地址")
    """
    manager = get_monitor_manager()
    return manager.stop_monitor(ca)


def start_ao_monitor(ca: str) -> bool:
    """
    启动AO监控
    
    Example:
        start_ao_monitor("CA地址")
    """
    manager = get_monitor_manager()
    return manager.start_monitor(ca)


def list_ao_monitors() -> List[Dict]:
    """
    列出所有AO监控任务
    
    Example:
        monitors = list_ao_monitors()
        for m in monitors:
            print(m['ca_short'], m['is_running'])
    """
    manager = get_monitor_manager()
    return manager.list_monitors()


def show_ao_monitors():
    """
    显示所有AO监控任务状态
    
    Example:
        show_ao_monitors()
    """
    manager = get_monitor_manager()
    manager.print_status()


def stop_all_ao_monitors():
    """
    停止所有AO监控
    
    Example:
        stop_all_ao_monitors()
    """
    manager = get_monitor_manager()
    manager.stop_all()
