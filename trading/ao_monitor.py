#!/usr/bin/env python3
"""
AO监控器 - 接管现有持仓，监控AO信号并自动卖出
"""

import time
from typing import Optional, List, Dict
from dataclasses import dataclass
from .executor import TradeExecutor
from .kline_service import get_klines
from .fib_calculator import parse_klines, calc_ao, ao_sell_signal


@dataclass
class AOMonitorConfig:
    """AO监控配置"""
    ca: str                              # 代币地址
    entry_price: Optional[float] = None  # 买入均价（可选）
    sell_percentage: float = 1.0         # 卖出比例（默认100%）


def run_ao_monitor(ca: str,
                   entry_price: Optional[float] = None,
                   interval: str = '5m',
                   check_interval: int = 60,
                   sell_percentage: float = 1.0):
    """
    监控单个CA的AO信号并自动卖出
    
    Args:
        ca: 代币地址
        entry_price: 买入均价（可选）
                    - 提供：AO<35k时需要收益率>50%才卖
                    - 不提供：只在AO>=35k时卖出
        interval: K线周期（默认5m）
        check_interval: 检查间隔（秒，默认60）
        sell_percentage: 卖出比例（默认1.0=全部）
    
    Example:
        # 不知道买入价
        run_ao_monitor(ca="代币地址")
        
        # 知道买入价
        run_ao_monitor(ca="代币地址", entry_price=0.00004)
    """
    executor = TradeExecutor()
    
    # 验证持仓
    print(f"\n{'='*80}")
    print(f"🔍 检查持仓: {ca}")
    positions = executor.get_positions()
    found = False
    for p in positions:
        if p.get("token_address", "").lower() == ca.lower():
            hold_amount = float(p.get("hold_amount", 0))
            if hold_amount > 0:
                print(f"✅ 找到持仓: {hold_amount} tokens")
                found = True
                break
    
    if not found:
        print(f"❌ 未找到持仓: {ca}")
        return
    
    print(f"🤖 开始监控AO信号")
    print(f"买入价: {entry_price if entry_price else '未提供（仅AO>=35k时卖）'}")
    print(f"卖出比例: {sell_percentage*100:.0f}%")
    print(f"{'='*80}\n")
    
    sold = False
    while not sold:
        try:
            # 1. 获取K线
            klines_raw = get_klines(ca, interval=interval, page_size=200)
            if not klines_raw:
                print(f"⚠️ [{ca[:8]}...] 未获取到K线，等待...")
                time.sleep(check_interval)
                continue
            
            # 2. 解析K线
            klines = parse_klines([{
                'time': k.time,
                'open': k.open,
                'high': k.high,
                'low': k.low,
                'close': k.close,
                'volume': k.volume,
                'market_cap': k.market_cap
            } for k in klines_raw])
            
            current_price = klines[-1].close
            
            # 3. 计算AO
            ao_values = calc_ao(klines)
            
            # 4. 检测AO卖出信号
            signal = ao_sell_signal(
                ao_values=ao_values,
                entry_price=entry_price,
                current_price=current_price
            )
            
            # 5. 处理信号
            if signal and signal.get("action") == "sell":
                print(f"\n🔔 [{ca[:8]}...] AO卖出信号触发！")
                print(f"   原因: {signal.get('reason')}")
                print(f"   AO值: {signal.get('ao_value'):.8f}")
                print(f"   当前价: {current_price:.8f}")
                
                if entry_price:
                    profit_rate = (current_price - entry_price) / entry_price
                    print(f"   收益率: {profit_rate*100:.2f}%")
                
                # 执行卖出
                print(f"\n📉 执行卖出 {sell_percentage*100:.0f}%...")
                result = executor.sell(ca=ca, percentage=sell_percentage)
                
                if result.success:
                    print(f"   ✅ 卖出成功！\n")
                    sold = True
                else:
                    print(f"   ❌ 卖出失败: {result.message}\n")
            
            # 6. 等待下次检查
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print(f"\n⚠️ [{ca[:8]}...] 用户中断，退出...")
            break
        except Exception as e:
            print(f"❌ [{ca[:8]}...] 错误: {e}")
            time.sleep(check_interval)
    
    print(f"✅ [{ca[:8]}...] 监控结束\n")


def run_ao_monitor_multi(configs: List[AOMonitorConfig],
                         interval: str = '5m',
                         check_interval: int = 60):
    """
    监控多个CA的AO信号并自动卖出（轮询模式）
    
    Args:
        configs: AO监控配置列表
        interval: K线周期（默认5m）
        check_interval: 检查间隔（秒，默认60）
    
    Example:
        from trading import run_ao_monitor_multi, AOMonitorConfig
        
        configs = [
            AOMonitorConfig(ca="CA1", entry_price=0.00004),
            AOMonitorConfig(ca="CA2", entry_price=None),
        ]
        
        run_ao_monitor_multi(configs)
    """
    executor = TradeExecutor()
    
    # 验证所有持仓
    print(f"\n{'='*80}")
    print(f"🔍 验证持仓...")
    print(f"{'='*80}")
    
    positions = executor.get_positions()
    valid_configs = []
    
    for config in configs:
        found = False
        for p in positions:
            if p.get("token_address", "").lower() == config.ca.lower():
                hold_amount = float(p.get("hold_amount", 0))
                if hold_amount > 0:
                    print(f"✅ [{config.ca[:8]}...] 持仓: {hold_amount} tokens")
                    valid_configs.append(config)
                    found = True
                    break
        
        if not found:
            print(f"❌ [{config.ca[:8]}...] 未找到持仓，跳过")
    
    if not valid_configs:
        print("\n❌ 没有有效的持仓，退出")
        return
    
    print(f"\n{'='*80}")
    print(f"🤖 开始监控 {len(valid_configs)} 个代币的AO信号")
    print(f"K线周期: {interval}")
    print(f"检查间隔: {check_interval}秒")
    print(f"{'='*80}\n")
    
    # 跟踪已卖出的CA
    sold_cas = set()
    
    while len(sold_cas) < len(valid_configs):
        try:
            for config in valid_configs:
                # 跳过已卖出的
                if config.ca in sold_cas:
                    continue
                
                try:
                    # 1. 获取K线
                    klines_raw = get_klines(config.ca, interval=interval, page_size=200)
                    if not klines_raw:
                        continue
                    
                    # 2. 解析K线
                    klines = parse_klines([{
                        'time': k.time, 'open': k.open, 'high': k.high,
                        'low': k.low, 'close': k.close, 'volume': k.volume,
                        'market_cap': k.market_cap
                    } for k in klines_raw])
                    
                    current_price = klines[-1].close
                    
                    # 3. 计算AO
                    ao_values = calc_ao(klines)
                    
                    # 4. 检测AO卖出信号
                    signal = ao_sell_signal(
                        ao_values=ao_values,
                        entry_price=config.entry_price,
                        current_price=current_price
                    )
                    
                    # 5. 处理信号
                    if signal and signal.get("action") == "sell":
                        print(f"\n🔔 [{config.ca[:8]}...] AO卖出信号触发！")
                        print(f"   原因: {signal.get('reason')}")
                        print(f"   AO值: {signal.get('ao_value'):.8f}")
                        print(f"   当前价: {current_price:.8f}")
                        
                        if config.entry_price:
                            profit_rate = (current_price - config.entry_price) / config.entry_price
                            print(f"   收益率: {profit_rate*100:.2f}%")
                        
                        # 执行卖出
                        print(f"\n📉 执行卖出 {config.sell_percentage*100:.0f}%...")
                        result = executor.sell(ca=config.ca, percentage=config.sell_percentage)
                        
                        if result.success:
                            print(f"   ✅ 卖出成功！")
                            sold_cas.add(config.ca)
                            print(f"   进度: {len(sold_cas)}/{len(valid_configs)}\n")
                        else:
                            print(f"   ❌ 卖出失败: {result.message}\n")
                
                except Exception as e:
                    print(f"❌ [{config.ca[:8]}...] 错误: {e}")
            
            # 等待下次检查
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断，退出...")
            break
    
    print(f"\n{'='*80}")
    print(f"✅ 所有监控完成！已卖出 {len(sold_cas)}/{len(valid_configs)} 个代币")
    print(f"{'='*80}\n")
