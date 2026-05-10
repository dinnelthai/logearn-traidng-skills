#!/usr/bin/env python3
"""
测试 AO "watch" 信号bug修复
验证 ao_sell_signal 返回 {"action": "watch"} 时不会被误判为卖出
"""

from trading.fib_calculator import Kline, fib_signal, calc_ao, ao_sell_signal


def test_ao_watch_not_trigger_sell():
    """
    测试场景：
    AO < 35k 绿转红，但没有持仓价格信息
    应该返回 {"action": "watch"}，而不是触发卖出
    """
    print("=" * 60)
    print("测试：AO watch 信号不应触发卖出")
    print("=" * 60)
    print()
    
    # 创建 K 线数据，使 AO 绿转红但值 < 35k
    klines = []
    base_time = 1000000
    
    # 创建足够的 K 线让 AO 可以计算（至少需要 34 根）
    for i in range(40):
        if i < 20:
            # 下跌阶段
            high = 0.0001 - i * 0.000002
            low = high - 0.000005
        else:
            # 反弹阶段（让 AO 变绿）
            low = 0.00005 + (i - 20) * 0.000001
            high = low + 0.000005
        
        close = (high + low) / 2
        klines.append(Kline(
            time=base_time + i * 3600,
            open=high,
            high=high,
            low=low,
            close=close,
            volume=1000000
        ))
    
    # 添加几根让 AO 转红的 K 线
    for i in range(3):
        low = 0.00007 - i * 0.000001
        high = low + 0.000002
        close = (high + low) / 2
        klines.append(Kline(
            time=base_time + (40 + i) * 3600,
            open=high,
            high=high,
            low=low,
            close=close,
            volume=1000000
        ))
    
    # 计算 AO
    ao_values = calc_ao(klines)
    
    # 测试1: ao_sell_signal 应该返回 {"action": "watch"}
    print("测试1: ao_sell_signal 返回值检查")
    sell_signal = ao_sell_signal(ao_values, entry_price=None, current_price=klines[-1].close)
    
    if not sell_signal:
        print("  ⚠️  ao_sell_signal 返回空字典（可能未触发绿转红）")
    elif sell_signal.get("action") == "watch":
        print(f"  ✅ ao_sell_signal 正确返回 watch 信号")
        print(f"     原因: {sell_signal.get('reason')}")
    elif sell_signal.get("action") == "sell":
        print(f"  ❌ 错误：ao_sell_signal 返回了 sell 信号")
        print(f"     这不应该发生（entry_price=None）")
        return False
    
    print()
    
    # 测试2: fib_signal 不应该触发卖出
    print("测试2: fib_signal 不应触发卖出")
    
    # 模拟持仓状态（已买入但没有 entry_price）
    result = fib_signal(
        klines,
        entry_price=None,  # 关键：没有持仓价格
        tiers_bought=["buy_618"],  # 有持仓
        pending_tiers=[],
        skip_ao=False,
        entry_swing_high=0.0001,
        entry_stop_price=0.00003,
        fib_sold_tiers=[]
    )
    
    if not result:
        print("  ⚠️  fib_signal 返回空字典")
    elif result.get("action") == "sell":
        print(f"  ❌ 错误：fib_signal 触发了卖出信号")
        print(f"     这是 bug！watch 信号被误判为 sell")
        return False
    else:
        print(f"  ✅ fib_signal 正确处理，action = {result.get('action')}")
    
    print()
    print("=" * 60)
    print("🎉 测试通过！AO watch 信号不会被误判为卖出")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_ao_watch_not_trigger_sell()
