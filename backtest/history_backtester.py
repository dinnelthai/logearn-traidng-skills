#!/usr/bin/env python3
"""
历史信号回测器 v2 — 基于 max_up_ratio 反推各档位理论命中情况
数据来源: signals_3x.db / raw_tokens (1657 tokens, 含 max_up_ratio/max_up_mcap)
"""

import sqlite3, json, sys
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from statistics import mean


# ── 常量 ──────────────────────────────────────────────────────────────────────
BUY_RATIOS_MAP = {
    "buy_618": 0.618,
    "buy_786": 0.786,
    "buy_861": 0.861,
}
STOP_RATIO   = 0.920   # 止损：波峰 - 92% 回调
SELL_RATIOS_MAP = {
    "sell_100":  1.000,
    "sell_1272": 1.272,
}
SELL_PCT = {"sell_100": 0.30, "sell_1272": 0.50}
PROFIT_50_PCT  = 0.50   # 50% 目标 → 涨至 entry×1.5
PROFIT_100_PCT = 1.00   # 100% 目标 → 涨至 entry×2.0


@dataclass
class TierResult:
    tier: str
    entry_price: float
    # 理论命中情况
    hit_618: bool
    hit_786: bool
    hit_861: bool
    # 止盈/止损
    hit_profit_50: bool    # 价格涨至 entry×1.5
    hit_profit_100: bool   # 价格涨至 entry×2.0
    hit_stop: bool         # 价格跌破 entry×0.92
    # 理论收益率（若在最高点卖出）
    max_profit_rate: float
    # 实际预期收益率（保守估算）
    expected_profit_rate: float
    # 理论卖出原因
    exit_reason: str
    # 档位对应的 top_price / mcap_at_top
    tier_top_price: float  # 该档位入场后，历史最高价格
    mcap_at_top: float


@dataclass
class TokenBacktest:
    symbol: str
    ca: str
    # 信号基准
    signal_price: float   # 信号触发时价格（参考）
    mcap_at_signal: float
    pool_liquidity: float
    swap_begin_time: float
    # 历史极值
    top_price: float
    top_mcap: float
    max_up_ratio: float
    # 各档位分析
    tiers: list[TierResult]
    # 综合判断
    any_profitable: bool
    best_tier: str
    best_profit_rate: float


def calc_fib_levels(swing_high: float, swing_low: float) -> dict:
    """FIB 入场档位计算（从 fib_calculator.py 移植）"""
    diff = swing_high - swing_low
    if diff <= 0:
        return {}
    levels = {}
    for label, r in BUY_RATIOS_MAP.items():
        levels[label] = swing_high - diff * r
    levels["stop"] = swing_high - diff * STOP_RATIO
    return levels


def calc_fib_sell_levels(swing_high: float, swing_low: float) -> dict:
    """FIB 卖出档位"""
    diff = swing_high - swing_low
    if diff <= 0:
        return {}
    levels = {}
    for label, r in SELL_RATIOS_MAP.items():
        levels[label] = swing_high + diff * (r - 1.0)
    return levels


class HistoryBacktester:
    """
    基于历史极值数据，模拟 logearn-trading 各档位理论命中情况

    核心假设：
    - 波谷(swing_low)  = raw_tokens.signal_price 或 swap_begin_time 附近价格
    - 波峰(swing_high)  = top_price（历史最高）
    - max_up_ratio     = top_price / signal_price

    由于无历史 K 线，AOEexit 精确时机无法模拟。
    用 max_up_ratio 推算：若 top_price 能涨至 entry×2.0，则理论上可以在 2× 附近卖出。
    """

    def __init__(self, db_path: str = '/root/log-pharse2/data/signals_3x.db'):
        self.db_path = db_path

    def load_raw_tokens(self, min_mcap: float = 1000, min_liquidity: float = 100) -> list:
        """
        加载 raw_tokens，过滤掉流动性极低的土狗
        min_mcap: 市值至少 $1000（去除刚上线就死的）
        min_liquidity: 流动性至少 $100
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute('''
            SELECT token_address, symbol, token_name, mcap, pool_liquidity,
                   fdv, price_now, price_change_5m, price_change_1h,
                   launch_time, swap_begin_time,
                   signal_best_type, signal_max_ratio,
                   max_up_ratio, max_up_mcap,
                   hot_index, is_trench_token,
                   buy_tx_count_d1, buyer_count_d1, seller_count_d1,
                   tag_smart_vol, tag_whale_vol, tag_new_vol, tag_old_vol,
                   tag_scam_vol, tag_shit_vol, tag_freq_vol,
                   raw_json
            FROM raw_tokens
            WHERE mcap >= ?
              AND pool_liquidity >= ?
              AND max_up_ratio > 1.0
            ORDER BY mcap DESC
        ''', (min_mcap, min_liquidity)).fetchall()
        conn.close()
        return rows

    def load_signals(self, limit: int = None) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        query = '''
            SELECT s.symbol, s.token_address, s.signals_json, s.raw_json,
                   r.mcap, r.pool_liquidity, r.signal_max_ratio,
                   r.max_up_ratio, r.max_up_mcap,
                   r.swap_begin_time, r.price_now, r.signal_best_type
            FROM early_bird_3x_signals s
            LEFT JOIN raw_tokens r ON s.token_address = r.token_address
            WHERE r.mcap >= 1000 AND r.pool_liquidity >= 100
            ORDER BY s.detected_at DESC
        '''
        if limit:
            query += f' LIMIT {limit}'
        rows = c.execute(query).fetchall()
        conn.close()
        return rows

    def parse_signal_levels(self, row) -> Optional[dict]:
        """从 signals_json 提取波峰波谷（兼容两种格式）"""
        try:
            sigs = json.loads(row['signals_json'])
        except:
            return None

        v_sig = None

        if isinstance(sigs, dict):
            for key in ['v_breakout_volume_list', 'breakout_volume_10x_list',
                        'continue_breakout_volume_list']:
                if key in sigs and sigs[key]:
                    for s in sigs[key]:
                        if isinstance(s, dict):
                            v_sig = s
                            break
                    if v_sig:
                        break
        elif isinstance(sigs, list):
            for s in sigs:
                if isinstance(s, dict) and s.get('type') == 'v_breakout_volume':
                    v_sig = s
                    break
            if not v_sig:
                v_sig = sigs[0] if sigs else None

        if not v_sig or not isinstance(v_sig, dict):
            return None

        low_price    = v_sig.get('low_price')
        top_price    = v_sig.get('top_price')
        signal_price = v_sig.get('signal_price') or v_sig.get('current_price')

        if not low_price or not top_price:
            return None

        return {
            'signal_price': float(signal_price),
            'low_price':    float(low_price),
            'top_price':    float(top_price),
        }

    def analyze_tier(self, entry_price: float,
                     swing_high: float, swing_low: float,
                     top_price: float, max_up_ratio: float,
                     tier_label: str) -> TierResult:
        """
        分析单个档位的理论命中情况

        逻辑：
        1. 计算止盈/止损阈值
        2. 判断 top_price（历史最高）是否触达各阈值
        3. 用 max_up_ratio 推算各档位对应的"理论顶部"

        关键：max_up_ratio = top_price / signal_price
        因此 tier_top_price = entry_price × (top_price / signal_price)
        即 entry_price × max_up_ratio（粗略估算）

        更准确的方法：计算 top_price 对 entry_price 的倍数
        top_at_entry_ratio = top_price / entry_price

        然后判断：
        - top_at_entry_ratio >= 2.0 → hit_profit_100
        - top_at_entry_ratio >= 1.5 → hit_profit_50
        - top_at_entry_ratio <= 0.92 → hit_stop
        """
        price_50  = entry_price * (1 + PROFIT_50_PCT)   # 1.5×
        price_100 = entry_price * (1 + PROFIT_100_PCT)  # 2.0×
        stop_price = entry_price * STOP_RATIO            # 0.92×

        # top_price 是信号触发后的历史最高，不是严格对应 tier entry
        # 正确：用 top_price / entry_price 的比例
        top_at_entry_ratio = top_price / entry_price if entry_price > 0 else 0

        # 更准确的推算：该档位能涨到的理论倍数
        # max_up_ratio = top_price / signal_price
        # tier_top = entry_price × max_up_ratio / signal_price × entry_price... 太复杂
        # 直接用比例关系：
        tier_top_ratio = top_price / entry_price if entry_price > 0 else 0

        hit_profit_50  = tier_top_ratio >= 1.5
        hit_profit_100 = tier_top_ratio >= 2.0
        hit_stop       = tier_top_ratio <= 0.92  # 最高都没跌破止损，说明没触发

        # 理论最大收益率（在最高点卖出）
        max_profit_rate = tier_top_ratio - 1.0

        # 实际预期收益率（保守估算）：
        # 若 hit_profit_100: 在 2× 卖出
        # 若 hit_profit_50:  在 1.5× 卖出
        # 否则: 在 top_price 卖出（这个档位没有理想卖点）
        if hit_profit_100:
            expected_profit_rate = PROFIT_100_PCT  # 100%
            exit_reason = "profit_100"
        elif hit_profit_50:
            expected_profit_rate = PROFIT_50_PCT   # 50%
            exit_reason = "profit_50"
        elif tier_top_ratio > 1.0:
            # 涨了但没到 50%
            expected_profit_rate = tier_top_ratio - 1.0
            exit_reason = "partial"
        else:
            # 破发了（最高都没超过 entry）
            expected_profit_rate = tier_top_ratio - 1.0
            exit_reason = "loss" if expected_profit_rate < 0 else "not_triggered"

        return TierResult(
            tier=tier_label,
            entry_price=entry_price,
            hit_618=(tier_label == "buy_618"),
            hit_786=(tier_label == "buy_786"),
            hit_861=(tier_label == "buy_861"),
            hit_profit_50=hit_profit_50,
            hit_profit_100=hit_profit_100,
            hit_stop=hit_stop,
            max_profit_rate=max_profit_rate,
            expected_profit_rate=expected_profit_rate,
            exit_reason=exit_reason,
            tier_top_price=top_price,
            mcap_at_top=top_price / (row.get('price_now', 1) or 1) * (row.get('mcap', 0) or 0) if False else 0,
        )

    def backtest_token(self, row) -> Optional[TokenBacktest]:
        """回测单个代币"""
        symbol = row['symbol']
        ca     = row['token_address']
        mcap   = float(row['mcap'] or 0)
        liq    = float(row['pool_liquidity'] or 0)
        price_now    = float(row['price_now'] or 0)
        max_up_ratio = float(row['max_up_ratio'] or 0)
        # raw_tokens 没有 top_price，用 max_up_ratio 反推
        signal_price = price_now / max_up_ratio if max_up_ratio > 1 and price_now > 0 else price_now
        top_price    = signal_price * max_up_ratio  # 反推历史最高价

        swap_begin_time = float(row['swap_begin_time'] or 0)

        # 波谷 = signal_price（或最低点）
        swing_low  = signal_price
        # 波峰 = top_price（历史最高）
        swing_high = top_price

        fib_levels = calc_fib_levels(swing_high, swing_low)
        if not fib_levels or not fib_levels.get('buy_618'):
            return None

        tier_results = []
        for tier_label in BUY_RATIOS_MAP.keys():
            entry_price = fib_levels.get(tier_label, 0)
            if entry_price <= 0:
                continue
            tr = self.analyze_tier(
                entry_price=entry_price,
                swing_high=swing_high, swing_low=swing_low,
                top_price=top_price, max_up_ratio=max_up_ratio,
                tier_label=tier_label
            )
            tier_results.append(tr)

        if not tier_results:
            return None

        profitable_tiers = [t for t in tier_results if t.expected_profit_rate > 0]
        best = max(tier_results, key=lambda t: t.expected_profit_rate) if tier_results else None

        return TokenBacktest(
            symbol=symbol,
            ca=ca,
            signal_price=signal_price,
            mcap_at_signal=mcap,
            pool_liquidity=liq,
            swap_begin_time=swap_begin_time,
            top_price=top_price,
            top_mcap=float(row.get('max_up_mcap') or 0),
            max_up_ratio=max_up_ratio,
            tiers=tier_results,
            any_profitable=len(profitable_tiers) > 0,
            best_tier=best.tier if best else '',
            best_profit_rate=best.expected_profit_rate if best else 0,
        )

    def run(self, mode: Literal['signals', 'raw'] = 'raw',
            limit: int = None) -> dict:
        """
        运行回测

        mode='signals': 用 early_bird_3x_signals（684条）
        mode='raw':     用 raw_tokens（1657条，更完整）
        """
        if mode == 'signals':
            rows = self.load_signals(limit)
        else:
            rows = self.load_raw_tokens(min_mcap=1000, min_liquidity=100)
            if limit:
                rows = rows[:limit]

        tier_stats = {k: {
            'count': 0, 'profitable': 0, 'sum_profit': 0.0,
            'reasons': {}, 'ratios': []
        } for k in BUY_RATIOS_MAP}

        exit_counts = {}
        token_results = []
        total_profitable = 0

        for row in rows:
            result = self.backtest_token(row)
            if not result:
                continue
            token_results.append(result)

            for t in result.tiers:
                ts = tier_stats[t.tier]
                ts['count'] += 1
                ts['sum_profit'] += t.expected_profit_rate
                ts['ratios'].append(t.expected_profit_rate)
                if t.expected_profit_rate > 0:
                    ts['profitable'] += 1
                    total_profitable += 1
                exit_counts[t.exit_reason] = exit_counts.get(t.exit_reason, 0) + 1
                key = f"{t.tier}_{t.exit_reason}"
                ts['reasons'][key] = ts['reasons'].get(key, 0) + 1

        total_tiers = sum(ts['count'] for ts in tier_stats.values())

        win_rate_by_tier = {
            k: ts['profitable'] / ts['count'] if ts['count'] > 0 else 0
            for k, ts in tier_stats.items()
        }
        avg_prof_by_tier = {
            k: ts['sum_profit'] / ts['count'] if ts['count'] > 0 else 0
            for k, ts in tier_stats.items()
        }
        median_prof_by_tier = {}
        for k, ts in tier_stats.items():
            r = sorted(ts['ratios']) if ts['ratios'] else []
            n = len(r)
            median_prof_by_tier[k] = r[n//2] if n > 0 else 0

        # 最佳/最差代币
        sorted_tokens = sorted(token_results, key=lambda x: x.best_profit_rate, reverse=True)
        best_tokens  = sorted_tokens[:5]
        worst_tokens = sorted_tokens[-5:]

        # Tier 命中统计
        hit_stats = {}
        for tier, ts in tier_stats.items():
            c = ts['count']
            hit_stats[tier] = {
                'count': c,
                'win_rate': win_rate_by_tier[tier],
                'avg_profit': avg_prof_by_tier[tier],
                'median_profit': median_prof_by_tier[tier],
                'p50_hit_rate': sum(1 for r in ts['ratios'] if r >= 0.5) / c if c > 0 else 0,
                'p100_hit_rate': sum(1 for r in ts['ratios'] if r >= 1.0) / c if c > 0 else 0,
            }

        return {
            'mode': mode,
            'total_tokens': len(rows),
            'tokens_analyzed': len(token_results),
            'total_tiers': total_tiers,
            'overall_win_rate': total_profitable / total_tiers if total_tiers > 0 else 0,
            'tier_stats': tier_stats,
            'hit_stats': hit_stats,
            'exit_reason_counts': dict(sorted(exit_counts.items(), key=lambda x: -x[1])),
            'win_rate_by_tier': win_rate_by_tier,
            'avg_profit_by_tier': avg_prof_by_tier,
            'median_profit_by_tier': median_prof_by_tier,
            'best_tokens': [asdict(t) for t in best_tokens],
            'worst_tokens': [asdict(t) for t in worst_tokens],
            'details': token_results,
        }


def print_report(r: dict):
    mode = r['mode']
    print("=" * 72)
    print(f"📊 HISTORY BACKTEST REPORT — logearn-trading v2 ({mode} mode)")
    print("=" * 72)
    print(f"  代币总数:       {r['total_tokens']}")
    print(f"  有效分析数:     {r['tokens_analyzed']}")
    print(f"  总档位数:       {r['total_tiers']}")
    print(f"  整体胜率:       {r['overall_win_rate']*100:.1f}%")
    print()

    print("─── 各档位表现 ─────────────────────────────────────────────────────")
    hdr = f"  {'档位':<10} {'触发':>6} {'盈利':>6} {'胜率':>8} {'均收益':>9} {'中位收益':>10} {'≥50%率':>8} {'≥100%率':>9}"
    print(hdr)
    print("  " + "-"*70)
    for tier, hs in r['hit_stats'].items():
        print(f"  {tier:<10} {hs['count']:>6} "
              f"{sum(1 for x in r['tier_stats'][tier]['ratios'] if x>0):>6} "
              f"{hs['win_rate']*100:>7.1f}% "
              f"{hs['avg_profit']*100:>8.1f}% "
              f"{hs['median_profit']*100:>9.1f}% "
              f"{hs['p50_hit_rate']*100:>7.1f}% "
              f"{hs['p100_hit_rate']*100:>8.1f}%")

    print()
    print("─── 卖出原因分布 ───────────────────────────────────────────────────")
    for reason, cnt in r['exit_reason_counts'].items():
        print(f"  {reason:<20} {cnt:>5} 次")

    print()
    print("─── 最佳代币 (top 5) ─────────────────────────────────────────────")
    for t in r['best_tokens']:
        tiers_str = ', '.join([
            f"{tr['tier']}:{tr['expected_profit_rate']*100:+.0f}%"
            for tr in t['tiers']
        ])
        print(f"  {t['symbol']:<12} max_up={t['max_up_ratio']:.0f}x "
              f"最佳={t['best_tier']} {t['best_profit_rate']*100:+.0f}%")
        print(f"              [{tiers_str}]")

    print()
    print("─── 最差代币 (bottom 5) ──────────────────────────────────────────")
    for t in r['worst_tokens']:
        print(f"  {t['symbol']:<12} max_up={t['max_up_ratio']:.1f}x "
              f"最佳={t['best_tier']} {t['best_profit_rate']*100:+.0f}%")
    print()
    print("=" * 72)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'raw'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    bt = HistoryBacktester()
    print(f"加载数据中 ({mode} mode){'...' if limit else ' (全部)...'}")
    report = bt.run(mode=mode, limit=limit)
    print_report(report)
