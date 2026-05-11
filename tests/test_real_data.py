#!/usr/bin/env python3
"""
使用真实K线数据测试交易检测逻辑
数据来源: FRZdAqPfrTbx264tRhVDSoGExUvYg5C6wwZSzCqypump
"""
import unittest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.trade_checker import check_single_trade_from_raw


class TestRealData(unittest.TestCase):
    """使用真实数据测试交易检测"""

    @classmethod
    def setUpClass(cls):
        """加载真实K线数据"""
        test_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(test_dir, "FRZdAq_klines_raw.json")
        
        with open(json_path, 'r') as f:
            cls.raw_klines = json.load(f)
        
        print(f"\n加载了 {len(cls.raw_klines)} 根真实K线数据")
        print(f"时间范围: {cls.raw_klines[0]['time']} - {cls.raw_klines[-1]['time']}")
        print(f"市值范围: {min(k['market_cap'] for k in cls.raw_klines):.2f}k - {max(k['market_cap'] for k in cls.raw_klines):.2f}k")

    def test_real_data_structure(self):
        """测试真实数据结构"""
        self.assertGreater(len(self.raw_klines), 0)
        
        # 检查必需字段
        required_fields = ['time', 'open', 'high', 'low', 'close', 'volume', 'market_cap']
        for k in self.raw_klines[:10]:  # 检查前10根
            for field in required_fields:
                self.assertIn(field, k, f"K线缺少字段: {field}")
        
        print("\n✅ 数据结构验证通过")

    def test_real_data_trade_detection(self):
        """测试真实数据的交易检测"""
        print("\n开始交易检测...")
        
        result = check_single_trade_from_raw(self.raw_klines, total_capital=2.0)
        
        print(f"\n检测结果:")
        print(f"  matched: {result['matched']}")
        print(f"  买入点数: {len(result['buy_points'])}")
        print(f"  卖出点数: {len(result['sell_points'])}")
        
        if result['matched']:
            from datetime import datetime, timezone, timedelta
            
            print(f"\n买入点:")
            for i, bp in enumerate(result['buy_points'], 1):
                kline_idx = bp['kline_index']
                kline = self.raw_klines[kline_idx]
                k_time = datetime.fromtimestamp(kline['time'], tz=timezone.utc)
                k_time_beijing = k_time.astimezone(timezone(timedelta(hours=8)))
                print(f"  {i}. {bp['tier']}: {bp['price']:.8f}")
                print(f"     时间(UTC): {k_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"     时间(北京): {k_time_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     市值: {kline['market_cap']:.2f}k USD")
                print(f"     K线索引: {kline_idx}")
            
            print(f"\n卖出点:")
            for i, sp in enumerate(result['sell_points'], 1):
                kline_idx = sp['kline_index']
                kline = self.raw_klines[kline_idx]
                k_time = datetime.fromtimestamp(kline['time'], tz=timezone.utc)
                k_time_beijing = k_time.astimezone(timezone(timedelta(hours=8)))
                print(f"  {i}. {sp['type']}: {sp['price']:.8f} ({sp['percentage']*100:.0f}%)")
                print(f"     时间(UTC): {k_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"     时间(北京): {k_time_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     市值: {kline['market_cap']:.2f}k USD")
                print(f"     K线索引: {kline_idx}")
            
            print(f"\n利润:")
            profit = result['profit']
            print(f"  投入: {profit['invested']:.4f} SOL")
            print(f"  回报: {profit['returned']:.4f} SOL")
            print(f"  利润: {profit['profit_sol']:.4f} SOL")
            print(f"  收益率: {profit['profit_rate']*100:+.2f}%")
        
        # 基本断言
        self.assertIsInstance(result, dict)
        self.assertIn('matched', result)
        self.assertIn('buy_points', result)
        self.assertIn('sell_points', result)
        
        print("\n✅ 交易检测完成")

    def test_real_data_with_mcap_threshold(self):
        """测试带市值门槛的真实数据检测"""
        print("\n测试市值门槛过滤...")
        
        # 测试不同的市值门槛
        thresholds = [10.0, 50.0, 100.0, 180.0]
        
        for threshold in thresholds:
            # 筛选达到市值门槛的K线
            filtered_klines = [k for k in self.raw_klines if k['market_cap'] >= threshold]
            
            if len(filtered_klines) < 10:
                print(f"  市值门槛 {threshold}k: K线不足 ({len(filtered_klines)} 根)")
                continue
            
            result = check_single_trade_from_raw(filtered_klines, total_capital=2.0)
            
            print(f"  市值门槛 {threshold}k:")
            print(f"    K线数: {len(filtered_klines)}")
            print(f"    matched: {result['matched']}")
            print(f"    买入点: {len(result['buy_points'])}")
            print(f"    卖出点: {len(result['sell_points'])}")
            
            # 如果180k门槛有交易，显示详情
            if threshold == 180.0 and result['matched']:
                from datetime import datetime, timezone, timedelta
                print(f"    买入详情:")
                for i, bp in enumerate(result['buy_points'], 1):
                    kline_idx = bp['kline_index']
                    kline = filtered_klines[kline_idx]
                    k_time = datetime.fromtimestamp(kline['time'], tz=timezone.utc)
                    k_time_beijing = k_time.astimezone(timezone(timedelta(hours=8)))
                    print(f"      {i}. {bp['tier']}: {bp['price']:.8f}")
                    print(f"         时间(北京): {k_time_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"         市值: {kline['market_cap']:.2f}k USD")
        
        print("\n✅ 市值门槛测试完成")

    def test_real_data_first_swing_high(self):
        """测试第一个波峰检测"""
        from trading.fib_calculator import fib_signal, parse_klines
        from datetime import datetime, timezone
        
        print("\n测试第一个波峰检测...")
        
        # 解析K线
        parsed = parse_klines(self.raw_klines)
        print(f"解析后K线数: {len(parsed)}")
        
        # 查找第一个波峰
        for i in range(50, min(100, len(parsed))):
            signal = fib_signal(parsed[:i+1])
            
            if signal.get('swing_high') and signal.get('swing_high') > 0:
                k_time = datetime.fromtimestamp(parsed[i].time, tz=timezone.utc)
                print(f"\n第一个波峰 @ K[{i}]")
                print(f"  时间: {k_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"  波峰: {signal['swing_high']:.8f}")
                print(f"  当前价格: {parsed[i].close:.8f}")
                print(f"  当前市值: {parsed[i].market_cap:.2f}k")
                print(f"  信号: {signal['action']}")
                break
        
        print("\n✅ 波峰检测测试完成")


if __name__ == '__main__':
    unittest.main(verbosity=2)
