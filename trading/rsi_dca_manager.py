#!/usr/bin/env python3
"""
RSI定投管理器 - 支持多代币定投

支持同时监控多个代币，内部轮询检查RSI，自动执行定投
"""

import time
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .rsi_dca_bot import RSIDCABot


@dataclass
class DCAConfig:
    """定投配置"""
    ca: str                          # 代币地址
    dca_amount: float                # 每次定投金额（SOL）
    max_buy_count: int               # 最大买入次数
    rsi_period: int = 14             # RSI周期
    rsi_buy_threshold: float = 30.0  # RSI买入阈值
    rsi_reset_threshold: float = 50.0  # RSI重置阈值
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


class RSIDCAManager:
    """RSI定投管理器 - 支持多代币定投"""
    
    def __init__(self, configs: List[DCAConfig], 
                 interval: str = '1h',
                 poll_interval: int = 300,
                 state_file: str = None,
                 max_workers: int = 10):
        """
        初始化RSI定投管理器
        
        Args:
            configs: 定投配置列表
            interval: K线周期（默认1h）
            poll_interval: 轮询间隔（秒，默认300=5分钟）
            state_file: 状态文件路径（用于持久化，可选）
            max_workers: 并发线程数（默认10，建议10-50）
        """
        self.configs = configs
        self.interval = interval
        self.poll_interval = poll_interval
        self.state_file = state_file or f".rsi_dca_state_{int(time.time())}.json"
        self.max_workers = max_workers
        
        # 创建机器人实例
        self.bots: Dict[str, RSIDCABot] = {}
        self.locks: Dict[str, Lock] = {}  # 每个代币一个锁
        for config in configs:
            self.bots[config.ca] = RSIDCABot(
                ca=config.ca,
                dca_amount=config.dca_amount,
                max_buy_count=config.max_buy_count,
                rsi_period=config.rsi_period,
                rsi_buy_threshold=config.rsi_buy_threshold,
                rsi_reset_threshold=config.rsi_reset_threshold
            )
            self.locks[config.ca] = Lock()  # 为每个代币创建锁
        
        # 加载状态
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                for ca, bot_state in state.items():
                    if ca in self.bots:
                        self.bots[ca].buy_count = bot_state.get('buy_count', 0)
                        self.bots[ca].waiting_for_reset = bot_state.get('waiting_for_reset', False)
                        self.bots[ca].last_rsi = bot_state.get('last_rsi', None)
                
                print(f"✅ 加载状态: {self.state_file}")
            except Exception as e:
                print(f"⚠️ 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        try:
            state = {}
            for ca, bot in self.bots.items():
                state[ca] = {
                    'buy_count': bot.buy_count,
                    'waiting_for_reset': bot.waiting_for_reset,
                    'last_rsi': bot.last_rsi,
                    'max_buy_count': bot.max_buy_count
                }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ 保存状态失败: {e}")
    
    def _check_single_token(self, config: DCAConfig, index: int, total: int) -> dict:
        """
        检查单个代币（用于并发，线程安全）
        
        Args:
            config: 定投配置
            index: 索引
            total: 总数
        
        Returns:
            检查结果字典
        """
        bot = self.bots[config.ca]
        lock = self.locks[config.ca]
        
        result = {
            'ca': config.ca,
            'index': index,
            'completed': False,
            'success': False,
            'message': ''
        }
        
        # 使用锁保护状态读取
        with lock:
            # 检查是否已完成
            if bot.buy_count >= bot.max_buy_count:
                result['completed'] = True
                return result
        
        try:
            # 获取K线（不需要锁，只读操作）
            from .kline_service import get_klines
            klines = get_klines(config.ca, self.interval, page_size=200)
            
            # 计算RSI（不需要锁，只读操作）
            from .indicators import calculate_rsi
            rsi = calculate_rsi(klines, config.rsi_period)
            
            # 使用锁保护状态修改
            with lock:
                bot.last_rsi = rsi
                
                result['rsi'] = rsi
                result['buy_count'] = bot.buy_count
                result['max_buy_count'] = bot.max_buy_count
                
                # 状态判断
                if bot.waiting_for_reset:
                    if rsi >= config.rsi_reset_threshold:
                        bot.waiting_for_reset = False
                        result['message'] = f"RSI回到{config.rsi_reset_threshold}以上({rsi:.2f})"
                    else:
                        result['message'] = f"等待RSI回到{config.rsi_reset_threshold}以上"
                else:
                    # 检查是否触发买入
                    if rsi < config.rsi_buy_threshold:
                        # 执行买入（在锁内执行，确保买入操作原子性）
                        from .executor import TradeExecutor
                        executor = TradeExecutor()
                        buy_result = executor.buy(
                            ca=config.ca,
                            amount_sol=config.dca_amount,
                            current_price=klines[0].close
                        )
                        
                        if buy_result.success:
                            bot.buy_count += 1
                            bot.waiting_for_reset = True
                            result['success'] = True
                            result['message'] = f"✅ 买入成功 ({bot.buy_count}/{bot.max_buy_count})"
                        else:
                            result['message'] = f"❌ 买入失败: {buy_result.message}"
                    else:
                        result['message'] = f"未触发买入: RSI({rsi:.2f}) >= {config.rsi_buy_threshold}"
            
            return result
            
        except Exception as e:
            result['message'] = f"错误: {e}"
            return result
    
    def run(self):
        """
        运行定投管理器（会一直运行）
        
        内部轮询所有代币，检查RSI并执行定投
        """
        print("="*80)
        print("🤖 RSI定投管理器启动（并发模式）")
        print("="*80)
        print(f"监控代币数: {len(self.configs)}")
        print(f"K线周期: {self.interval}")
        print(f"轮询间隔: {self.poll_interval}秒 ({self.poll_interval//60}分钟)")
        print(f"并发线程数: {self.max_workers}")
        print(f"状态文件: {self.state_file}")
        print(f"预计每轮耗时: ~{len(self.configs) / self.max_workers * 0.5:.1f}秒")
        print("="*80)
        print()
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                start_time = time.time()
                
                print(f"\n{'='*80}")
                print(f"[轮询 #{cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*80}\n")
                
                # 并发检查所有代币
                active_count = 0
                completed_count = 0
                buy_success_count = 0
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # 提交所有任务
                    futures = {}
                    for i, config in enumerate(self.configs, 1):
                        future = executor.submit(self._check_single_token, config, i, len(self.configs))
                        futures[future] = config
                    
                    # 收集结果
                    for future in as_completed(futures):
                        result = future.result()
                        
                        if result['completed']:
                            completed_count += 1
                        else:
                            active_count += 1
                            
                            # 显示结果
                            ca_short = f"{result['ca'][:8]}...{result['ca'][-6:]}"
                            if result.get('rsi'):
                                print(f"[{result['index']}/{len(self.configs)}] {ca_short} | RSI:{result['rsi']:.2f} | {result['message']}")
                            else:
                                print(f"[{result['index']}/{len(self.configs)}] {ca_short} | {result['message']}")
                            
                            if result['success']:
                                buy_success_count += 1
                
                # 保存状态
                self._save_state()
                
                # 计算耗时
                elapsed = time.time() - start_time
                
                # 显示总结
                print(f"\n{'='*80}")
                print(f"本轮总结:")
                print(f"  活跃: {active_count} | 已完成: {completed_count} | 总计: {len(self.configs)}")
                print(f"  本轮买入: {buy_success_count}次")
                print(f"  耗时: {elapsed:.1f}秒")
                print(f"{'='*80}\n")
                
                # 检查是否全部完成
                if completed_count == len(self.configs):
                    print("🎉 所有代币定投已完成！")
                    break
                
                # 等待下一次轮询
                print(f"⏰ 等待{self.poll_interval}秒后进行下一轮检查...")
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断，保存状态并退出...")
                self._save_state()
                break
            except Exception as e:
                print(f"❌ 轮询错误: {e}")
                print(f"等待{self.poll_interval}秒后重试...")
                time.sleep(self.poll_interval)
        
        print("\n" + "="*80)
        print("RSI定投管理器已停止")
        print("="*80)
    
    def get_status(self) -> Dict[str, dict]:
        """
        获取所有代币的状态
        
        Returns:
            状态字典 {ca: status}
        """
        status = {}
        for ca, bot in self.bots.items():
            status[ca] = bot.get_status()
        return status


def run_rsi_dca_multi(configs: List[DCAConfig], 
                      interval: str = '1h',
                      poll_interval: int = 300,
                      max_workers: int = 10):
    """
    运行多代币RSI定投（对外公开接口）
    
    支持同时监控多个代币，内部轮询检查RSI，自动执行定投。
    支持并发检查，大幅提升大规模代币监控效率。
    
    Args:
        configs: 定投配置列表
        interval: K线周期（默认'1h'）
        poll_interval: 轮询间隔（秒，默认300=5分钟）
        max_workers: 并发线程数（默认10，建议10-50）
    
    性能说明:
        - 单线程: 15000个代币需要~2小时/轮
        - 10线程: 15000个代币需要~12分钟/轮
        - 50线程: 15000个代币需要~2.5分钟/轮
    
    Example:
        >>> from trading import run_rsi_dca_multi, DCAConfig
        >>> 
        >>> # 配置多个代币定投
        >>> configs = [
        ...     DCAConfig(ca="代币1地址", dca_amount=0.1, max_buy_count=10),
        ...     DCAConfig(ca="代币2地址", dca_amount=0.2, max_buy_count=5),
        ...     DCAConfig(ca="代币3地址", dca_amount=0.15, max_buy_count=8),
        ... ]
        >>> 
        >>> # 运行定投管理器（会一直运行）
        >>> run_rsi_dca_multi(configs, interval='1h', poll_interval=300)
    
    Note:
        - 会一直运行，每5分钟检查一次所有代币
        - 自动保存状态，支持中断恢复
        - 按Ctrl+C可随时停止
        - 必须设置LOGEARN_API_KEY环境变量
        - 支持大规模代币监控（15000+）
    """
    manager = RSIDCAManager(configs, interval, poll_interval, max_workers=max_workers)
    manager.run()


if __name__ == "__main__":
    import sys
    
    # 示例用法
    if len(sys.argv) < 2:
        print("用法: python rsi_dca_manager.py <配置文件.json>")
        print()
        print("配置文件格式:")
        print(json.dumps([
            {
                "ca": "代币1地址",
                "dca_amount": 0.1,
                "max_buy_count": 10,
                "rsi_buy_threshold": 30.0,
                "rsi_reset_threshold": 50.0
            },
            {
                "ca": "代币2地址",
                "dca_amount": 0.2,
                "max_buy_count": 5
            }
        ], indent=2))
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # 加载配置
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    configs = [DCAConfig(**c) for c in config_data]
    
    # 运行
    run_rsi_dca_multi(configs, interval='1h', poll_interval=300)
