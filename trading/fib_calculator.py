"""
FIB + AO 模块 — TradingView 风格
FIB: 波谷 = klines[0]["low"]，波峰 = 窗口最高价
AO:  标准 Bill Williams 实现
"""

from dataclasses import dataclass, field
from .config import DEFAULT_CONFIG


# ─── 内部类型 ───────────────────────────────────────────────────────────────

@dataclass
class FibLevel:
    ratio: float
    price: float
    label: str
    is_retracement: bool


@dataclass
class Kline:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_cap: float = 0.0  # 市值（单位：k，即千美元），默认0表示无市值数据


# ─── K线解析 ───────────────────────────────────────────────────────────────

def parse_klines(raw: list[dict]) -> list[Kline]:
    return [
        Kline(
            time=int(r["time"]),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            volume=float(r["volume"]) if r.get("volume") else 0.0,
            market_cap=float(r.get("market_cap", 0.0)),  # 支持市值字段，默认0
        )
        for r in raw
    ]


# ─── AO 计算 ────────────────────────────────────────────────────────────────

def median_price(k: Kline) -> float:
    # 使用 SOL 价格（highU/lowU）与其他计算保持一致
    high = k.highU if hasattr(k, 'highU') else k.high
    low = k.lowU if hasattr(k, 'lowU') else k.low
    return (high + low) / 2


def sma(values: list[float], period: int) -> list:
    """Simple Moving Average，None 表示前 period-1 根K无法计算"""
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1:i + 1]) / period)
    return result


def calc_ao(klines: list[Kline], fast: int = 5, slow: int = 34) -> list:
    """
    AO = SMA(median_price, fast) - SMA(median_price, slow)
    前 slow-1 根K返回 None
    """
    medians = [median_price(k) for k in klines]
    fast_sma = sma(medians, fast)
    slow_sma = sma(medians, slow)

    result = []
    for f, s in zip(fast_sma, slow_sma):
        if f is None or s is None:
            result.append(None)
        else:
            result.append(f - s)
    return result


def ao_bars(ao_values: list) -> list[dict]:
    """
    渲染AO柱状图所需数据
    color: green(同色) / red(异色) / dim(NA)
    """
    bars = []
    for i, v in enumerate(ao_values):
        if v is None:
            bars.append({"index": i, "value": 0, "color": "dim"})
            continue
        if i == 0 or ao_values[i - 1] is None:
            prev = v
        else:
            prev = ao_values[i - 1]
        color = "green" if v >= prev else "red"
        bars.append({"index": i, "value": round(v, 8), "color": color})
    return bars


def ao_report(klines: list[Kline]) -> str:
    ao = calc_ao(klines)
    valid = [(i, v) for i, v in enumerate(ao) if v is not None]
    if not valid:
        return "K线不足，无法计算AO"

    latest_ao = valid[-1][1]
    prev_ao = valid[-2][1] if len(valid) >= 2 else latest_ao
    trend = "↑ 零轴上方" if latest_ao > 0 else "↓ 零轴下方"
    cross = "✓ 金叉" if (latest_ao > 0 and prev_ao < 0) else ("✗ 死叉" if (latest_ao < 0 and prev_ao > 0) else "— 延续")

    lines = [
        f"AO (5, 34) 最新值: {latest_ao:.8f}",
        f"前一值:            {prev_ao:.8f}",
        f"趋势:              {trend}",
        f"零轴交叉:          {cross}",
    ]
    return "\n".join(lines)


# ─── 仓位管理 ───────────────────────────────────────────────────────────────

# 单币最大持仓占总资金比例
MAX_POSITION_RATIO = 0.30    # 30%（提升风险承受能力）

# 三档分配（总目标仓位 = MAX_POSITION_RATIO × 总资金）
ENTRY_TIERS = [
    ("buy_618", 0.50),   # 50% @ 618
    ("buy_786", 0.25),   # 25% @ 786
    ("buy_861", 0.25),   # 25% @ 861
]

# 每次买入最低金额（SOL）
MIN_POSITION_SOL = 0.05  # 约 $4.5，避免过小交易


def position_size(total_capital: float, tier: str) -> float:
    """计算某档建仓的目标金额（SOL）"""
    for label, ratio in ENTRY_TIERS:
        if label == tier:
            size = total_capital * MAX_POSITION_RATIO * ratio
            return max(size, MIN_POSITION_SOL)
    return 0.0


def position_report(total_capital: float, levels: dict) -> str:
    lines = [
        f"总目标仓位: {MAX_POSITION_RATIO*100:.0f}% ({total_capital*MAX_POSITION_RATIO:.4f} SOL)",
        "",
    ]
    for label, ratio in ENTRY_TIERS:
        price = levels.get(label, 0)
        size  = position_size(total_capital, label)
        tier_name = label.replace("buy_", "buy")
        lines.append(f"  {tier_name}  {ratio*100:.0f}%  价格={price:.8f}  金额={size:.4f} SOL")
    stop_price = levels.get("stop", 0)
    lines.append(f"  stop      止损    价格={stop_price:.8f}  全部平仓")
    return "\n".join(lines)

BUY_RATIOS   = [
    ("buy_618", 0.618),
    ("buy_786", 0.786),
    ("buy_861", 0.861),
]
STOP_RATIO   = 0.920

# Fibonacci 卖出档位（扩展位）
SELL_RATIOS = [
    ("sell_100", 1.000),   # 100% 回撤（回到波峰）→ 卖出 30%
    ("sell_1272", 1.272),  # 127.2% 扩展 → 卖出 50%
]
SELL_PERCENTAGES = {
    "sell_100": 0.30,   # 卖出 30%
    "sell_1272": 0.50,  # 卖出 50%
}


def fib_entry_levels(swing_high: float, swing_low: float) -> dict:
    """
    返回三个买点 + 止损点的价格
    swing_high: 波峰（窗口最高价）
    swing_low:  波谷（klines[0].low，固定）
    """
    diff = swing_high - swing_low
    if diff <= 0:
        return {}

    levels = {}
    for label, r in BUY_RATIOS:
        levels[label] = swing_high - diff * r
    levels["stop"] = swing_high - diff * STOP_RATIO

    return levels


def fib_sell_levels(swing_high: float, swing_low: float) -> dict:
    """
    返回 Fibonacci 卖出档位价格（扩展位）
    swing_high: 波峰（买入时的波峰）
    swing_low:  波谷（买入时的波谷）
    
    sell_100:  回到波峰（100% 回撤）
    sell_1272: 127.2% 扩展（黄金分割扩展位）
    """
    diff = swing_high - swing_low
    if diff <= 0:
        return {}
    
    levels = {}
    for label, r in SELL_RATIOS:
        # 扩展位计算：波峰 + diff × (r - 1)
        # sell_100:  swing_high + diff × 0 = swing_high
        # sell_1272: swing_high + diff × 0.272
        levels[label] = swing_high + diff * (r - 1.0)
    
    return levels


def zigzag_pivots(highs: list[float], lows: list[float],
                  deviation: float = 5.0, depth: int = 10, lookback: int = 5) -> list[tuple]:
    """
    ZIGZAG 拐点检测。
    deviation: 两拐点之间最小波动百分比（%），低于此值忽略
    depth:     两拐点之间最小K线根数
    lookback:  右侧需要多少根K线确认（默认5根，避免最后一根被误判）
    返回 [(bar_idx, 'H'|'L', price)]
    """
    n = len(highs)
    pivots = []
    i = depth
    # 确保右侧至少有 lookback 根K线用于确认
    while i < n - lookback:
        # 左侧检查：depth 根K线都低于/高于当前
        # 右侧检查：lookback 根K线都低于/高于当前
        is_high = all(highs[i] > highs[i - d] for d in range(1, depth + 1)) and \
                  all(highs[i] >= highs[i + d] for d in range(1, min(lookback + 1, n - i)))
        is_low  = all(lows[i] <  lows[i - d]  for d in range(1, depth + 1)) and \
                  all(lows[i] <= lows[i + d]  for d in range(1, min(lookback + 1, n - i)))
        if not (is_high or is_low):
            i += 1
            continue
        # 互斥：同一根K不会同时高低点
        if is_high and is_low:
            i += 1
            continue
        price = highs[i] if is_high else lows[i]
        hl = 'H' if is_high else 'L'
        if pivots:
            pct = abs(price - pivots[-1][2]) / pivots[-1][2] * 100
            if pct < deviation:
                i += 1
                continue
        pivots.append((i, hl, price))
        i += 1
    return pivots


def _swing_from_klines(klines, deviation: float = 5.0, depth: int = 10):
    """
    ZIGZAG 波峰波谷。
    返回 (swing_high, swing_low)

    - swing_high: 当前下降波段的起始波峰。
                  若 ZIGZAG 波峰序列为 A < B > C（B 最高，C 更低），
                  则在 C 下方买入时应以 B 为参考，而非 C。
                  算法：从最近 H 往前回溯，只要前一个 H 更高就继续累积，
                  遇到前一个 H 更低即停止——此时所累积的最大值即为本轮下降起始峰。
    - swing_low:  klines[0].low（固定锚点，不可更改）
    """
    # 使用 SOL 价格（highU/lowU）而非 USD 价格（high/low）
    # 因为市值计算用的是 closeU × supply，需要保持单位一致
    highs = [k.highU if hasattr(k, 'highU') else k.high for k in klines]
    lows  = [k.lowU if hasattr(k, 'lowU') else k.low for k in klines]
    pivots = zigzag_pivots(highs, lows, deviation=deviation, depth=depth)

    h_prices = [price for _, hl, price in pivots if hl == 'H']
    if not h_prices:
        return max(highs), lows[0]

    # 从最近 H 往前，找本轮下降序列的起始峰（连续递降中的最高值）
    # 例: [A=0.1, B=0.5, C=0.3] → dominant=0.5=B
    # 例: [A=0.1, B=0.3, C=0.5] → dominant=0.5=C（上升，直接取最近）
    dominant = h_prices[-1]
    for price in reversed(h_prices[:-1]):
        if price > dominant:
            dominant = price
        else:
            break  # 前一个 H 更低，说明 dominant 已是本轮下降起点

    return dominant, lows[0]


def ao_sell_signal(ao_values: list,
                    entry_price: float = None,
                    current_price: float = None,
                    config = None) -> dict:
    """
    AO 卖出信号判断
    - AO >= 阈值：绿转红直接卖出
    - AO < 阈值：需绿转红 + 收益率 > 阈值 才卖出
    返回 {'action': 'sell', 'ao_value': float, 'threshold': float, 'reason': str} 或 {}
    
    Bug Fix: 当 entry_price 为 None 时，如果 AO < 阈值，仍然记录信号但不执行卖出
    """
    if config is None:
        config = DEFAULT_CONFIG.ao
    
    valid = [(i, v) for i, v in enumerate(ao_values) if v is not None]
    if len(valid) < 3:
        return {}

    ao_n2 = valid[-3][1]
    ao_n1 = valid[-2][1]
    ao_0  = valid[-1][1]
    color_n1 = "green" if ao_n1 >= ao_n2 else "red"
    color_0  = "green" if ao_0  >= ao_n1 else "red"

    # 绿转红：n1绿且n0红，且当前AO在0轴上方
    if not (color_n1 == "green" and color_0 == "red" and ao_0 > 0):
        return {}

    # AO >= 阈值 → 直接卖出
    if ao_0 >= config.threshold_normal:
        return {"action": "sell", "ao_value": ao_0,
                "threshold": config.threshold_normal, 
                "reason": f"ao≥{config.threshold_normal*1e6:.0f}k绿转红"}

    # AO < 阈值 → 需收益率 > 阈值才卖出
    if entry_price and entry_price > 0 and current_price:
        ret = (current_price - entry_price) / entry_price
        if ret >= config.profit_threshold:
            return {"action": "sell", "ao_value": ao_0,
                    "threshold": config.threshold_normal,
                    "reason": f"ao<{config.threshold_normal*1e6:.0f}k但收益率>{config.profit_threshold*100:.0f}%({ret*100:.1f}%)"}
    
    # Bug Fix: entry_price 为 None 时，记录警告但不卖出
    # 这样可以在日志中看到潜在的卖出信号
    return {"action": "watch", "ao_value": ao_0,
            "threshold": config.threshold_normal,
            "reason": f"ao<{config.threshold_normal*1e6:.0f}k绿转红但无持仓价格信息"}


def fib_sell_signal(swing_high: float, swing_low: float, current_price: float,
                     fib_sold_tiers: list = None) -> dict:
    """
    Fibonacci 卖出信号检测（作为 AO 卖出的补充）
    
    参数:
        swing_high: 买入时锁定的波峰
        swing_low: 买入时锁定的波谷
        current_price: 当前价格
        fib_sold_tiers: 已经通过 Fib 卖出的档位列表
    
    返回:
        - 触发卖出: {"action": "fib_sell", "tier": "sell_100"|"sell_1272", 
                     "percentage": 0.3|0.5, "price": float, "level": float}
        - 未触发: {}
    
    卖出规则:
        1. 价格回到 1.0（波峰）→ 卖出 30%
        2. 价格突破 1.272 扩展位 → 卖出 50%
        3. 每个档位只触发一次
    """
    if not swing_high or not swing_low or not current_price:
        return {}
    
    fib_sold_tiers = fib_sold_tiers or []
    
    # 计算 Fib 卖出档位
    sell_levels = fib_sell_levels(swing_high, swing_low)
    if not sell_levels:
        return {}
    
    # SELL_RATIOS 已按价格从低到高排列（sell_100 < sell_1272），优先触发低档
    for tier_label, _ in SELL_RATIOS:
        if tier_label in fib_sold_tiers:
            continue
        level_price = sell_levels.get(tier_label)
        if not level_price:
            continue
        if current_price >= level_price:
            pct = int(SELL_PERCENTAGES[tier_label] * 100)
            return {
                "action": "fib_sell",
                "tier": tier_label,
                "percentage": SELL_PERCENTAGES[tier_label],
                "price": current_price,
                "level": level_price,
                "reason": f"价格触达 {tier_label} 位 {level_price:.8f}，卖出 {pct}%",
            }

    return {}


def check_penetration_with_tolerance(latest_low: float, latest_close: float, level_price: float, 
                                     config = None) -> bool:
    """
    检查是否穿透档位（带动态容差）
    
    逻辑：
    1. 日内最低价必须触及档位（latest_low <= level_price）
    2. 收盘价允许回升，但不超过动态容差：
       - 插针深度 < 3%：允许收盘价回升 2%
       - 插针深度 >= 3%：允许收盘价回升 5%
    
    Args:
        latest_low: 当前 K 线最低价
        latest_close: 当前 K 线收盘价
        level_price: 档位价格
    
    Returns:
        True: 确认穿透，False: 未穿透或假突破
    
    示例：
        - 浅插针收回: low=0.00004950, close=0.00005100, level=0.00005000 → True（插针1%，收盘回升2%）
        - 深插针收回: low=0.00004800, close=0.00005200, level=0.00005000 → True（插针4%，收盘回升4%）
        - 假突破: low=0.00004990, close=0.00005300, level=0.00005000 → False（收盘回升6%）
    """
    # 条件1: 日内最低价必须触及档位
    if latest_low > level_price:
        return False
    
    if config is None:
        config = DEFAULT_CONFIG.fibonacci
    
    # 计算插针深度（穿透幅度）
    penetration_depth = (level_price - latest_low) / level_price if level_price > 0 else 0
    
    # 动态容差：根据插针深度调整
    if penetration_depth < config.shallow_penetration_threshold:
        tolerance = config.shallow_tolerance
    else:
        tolerance = config.deep_tolerance
    
    # 条件2: 收盘价在容差范围内
    max_close = level_price * (1 + tolerance)
    return latest_close <= max_close


def fib_signal(
    klines: List[Kline],
    entry_price: float = None,
    tiers_bought: List[str] = None,
    pending_tiers: List[str] = None,
    skip_ao: bool = False,
    entry_swing_high: float = None,
    entry_stop_price: float = None,
    fib_sold_tiers: List[str] = None
) -> Dict:
    """
    根据最新收盘价，判断是否触发买入/止损/卖出
    entry_price: 持仓均价，用于 AO<50k 时的收益率判断
    tiers_bought: 已买入的档位列表
    pending_tiers: 已穿透待买的档位列表（下次轮询买）
    entry_swing_high: 买入时锁定的波峰（持仓期间不允许下移止损）
    entry_stop_price: 买入时锁定的止损价（持仓期间不允许下移）
    fib_sold_tiers: 已通过 Fib 卖出的档位列表
    返回:
      - 止损触发: {"action": "stop", "price": float, "level": float}
      - AO卖出触发: {"action": "sell", ...}
      - Fib卖出触发: {"action": "fib_sell", "tier": str, "percentage": float, ...}
      - 买点触发（单档）: {"action": "buy_618"|"buy_786"|"buy_861", "price": float, "level": float,
                          "pending": [剩余待买档位], "swing_high": float, "stop_price": float}
      - 观察: {"action": "watch", "price": float, "levels": dict,
               "penetrated": [本次新穿透档位], "pending": [所有待买档位]}
    """
    if len(klines) < 2:
        return {}

    swing_high, swing_low = _swing_from_klines(klines)
    levels = fib_entry_levels(swing_high, swing_low)
    # 使用 SOL 价格（closeU/lowU）与波峰计算保持一致
    latest_close = klines[-1].closeU if hasattr(klines[-1], 'closeU') else klines[-1].close
    latest_low   = klines[-1].lowU if hasattr(klines[-1], 'lowU') else klines[-1].low

    # AO 卖出信号优先（持仓中才判断，空仓跳过）
    if not skip_ao:
        ao_values = calc_ao(klines)
        sell = ao_sell_signal(ao_values, entry_price=entry_price, current_price=latest_close)
        if sell and sell.get("action") == "sell":
            # AO 触发 → 全部托管给 AO，忽略 Fib 卖出
            return {
                "action": "sell",
                "price": latest_close,
                "level": latest_close,
                "ao_value": sell["ao_value"],
                "ao_threshold": sell["threshold"],
                "ao_reason": sell.get("reason", ""),
            }
    
    # Fib 卖出信号（AO 未触发时才检查，作为补充）
    if tiers_bought and entry_swing_high:
        fib_sell = fib_sell_signal(entry_swing_high, swing_low, latest_close, fib_sold_tiers)
        if fib_sell:
            return fib_sell

    # 止损价逻辑：持仓期间始终使用买入时锁定的止损价（不随后续波峰更新）
    if tiers_bought and entry_stop_price is not None:
        stop_price = entry_stop_price
    else:
        # 空仓：使用当前计算的止损价
        stop_price = levels.get("stop", float("inf"))
    
    # 止损优先：日内低点穿透止损价 → 直接止损
    if latest_low <= stop_price:
        return {"action": "stop", "price": latest_low, "level": stop_price}

    # 找出本次新穿透的档位（排除已持仓 + 已 pending 的）
    all_tiers = [label for label, _ in BUY_RATIOS]  # ['buy_618', 'buy_786', 'buy_861']
    tiers_bought = tiers_bought or []
    pending_tiers = pending_tiers or []

    newly_penetrated = []
    for label in all_tiers:
        if label in tiers_bought or label in pending_tiers:
            continue
        lp = levels.get(label)
        # 使用动态容差检查穿透
        if lp and check_penetration_with_tolerance(latest_low, latest_close, lp):
            newly_penetrated.append(label)

    if not newly_penetrated:
        # 无新穿透，但有之前 pending 的档位 → 继续买最前面的 pending
        if pending_tiers:
            # 过滤掉已买入的档位（防止价格反弹后重复触发）
            remaining_pending = [t for t in pending_tiers if t not in tiers_bought]
            
            if remaining_pending:
                next_tier = remaining_pending[0]
                next_price = levels.get(next_tier)
                # 使用动态容差检查穿透
                if next_price and check_penetration_with_tolerance(latest_low, latest_close, next_price):
                    return {
                        "action": next_tier,
                        "price": next_price,
                        "level": next_price,
                        "penetrated": [],
                        "pending": remaining_pending[1:],
                        "swing_high": swing_high,
                        "stop_price": stop_price
                    }
                else:
                    # 价格已反弹，不在穿透位，pending 保留
                    return {
                        "action": "watch",
                        "price": latest_close,
                        "levels": levels,
                        "penetrated": [],
                        "pending": remaining_pending,
                    }
        return {
            "action": "watch",
            "price": latest_close,
            "levels": levels,
            "penetrated": [],
            "pending": pending_tiers,
        }

    # 合并：之前 pending + 本次新穿透
    all_pending = pending_tiers + newly_penetrated

    # 按价格从高到低排序（优先买浅档 = 价格高的档位）
    all_pending_sorted = sorted(
        all_pending,
        key=lambda t: levels.get(t, 0),
        reverse=True  # 价格从高到低
    )

    # 买入价格最高的档位（最浅档，风险最小）
    next_tier = all_pending_sorted[0]
    next_price = levels[next_tier]

    # 其余档位留给后续轮询
    remaining_pending = all_pending_sorted[1:]

    return {
        "action": next_tier,
        "price": next_price,
        "level": next_price,
        "penetrated": newly_penetrated,
        "pending": remaining_pending,
        "swing_high": swing_high,      # 买入时的波峰（用于锁定止损）
        "stop_price": stop_price       # 买入时的止损价（用于锁定止损）
    }


def fib_signal_report(klines: list[Kline]) -> str:
    result = fib_signal(klines)
    if not result:
        return "K线不足"

    if result["action"] == "watch":
        lv = result["levels"]
        lines = [
            "─── FIB 买入/止损位（当前: watch）───",
            f"  当前收盘:  {result['price']:.8f}",
        ]
        for label, _ in BUY_RATIOS:
            lines.append(f"  {label}  {lv.get(label, 0):.8f}")
    elif result["action"] == "sell":
        lines = [
            f"─── 信号: sell ───",
            f"  触发价格:  {result['price']:.8f}",
            f"  AO值:      {result.get('ao_value', 0):.8f}",
            f"  AO阈值:    {result.get('ao_threshold', 0):.8f}",
            f"  触发说明:  AO零轴上方 >50k，绿转红第二根，全平",
        ]
    else:
        lines = [
            f"─── 信号: {result['action']} ───",
            f"  触发价格: {result['price']:.8f}",
            f"  触发价位: {result['level']:.8f}",
        ]
    return "\n".join(lines)

def calc_fib(klines: list[Kline]) -> list[FibLevel]:
    """
    klines: 按时间正序的K线列表，每条含 open/high/low/close/volume
    return: 所有FIB价位，按ratio升序排列
    """
    if len(klines) < 2:
        return []

    # 使用 SOL 价格（openU/highU/lowU/closeU）与其他计算保持一致
    opens  = [k.openU if hasattr(k, 'openU') else k.open for k in klines]
    highs  = [k.highU if hasattr(k, 'highU') else k.high for k in klines]
    lows   = [k.lowU if hasattr(k, 'lowU') else k.low for k in klines]
    closes = [k.closeU if hasattr(k, 'closeU') else k.close for k in klines]

    # 波谷 = 第一根K的最低价（固定），波峰 = 窗口内最高价
    swing_low  = lows[0]   # 第一根K的low，固定不变
    swing_high = max(highs)

    # 起始点 = 第一根K的open
    start_price = opens[0]

    # ── 回撤位（从波峰往波谷方向，起始于start_price）───────────────
    #
    #  如果 start_price 更接近 swing_high（处于高位）：
    #    从 start_price 往下看支撑，用 swing_high - swing_low 区间
    #  如果 start_price 更接近 swing_low（处于低位）：
    #    从 start_price 往上看阻力
    #
    #  TradingView 标准：比率固定为 swing_high - swing_low
    diff = swing_high - swing_low
    if diff <= 0:
        return []

    levels = []

    # 回撤比率（正值 = 从波峰往波谷回撤的比例）
    retracements = {
        0.236: "23.6%",
        0.382: "38.2%",
        0.500: "50.0%",
        0.618: "61.8%",
        0.786: "78.6%",
    }

    for ratio, label in retracements.items():
        # 回撤位 = 波峰 - (diff × ratio)
        price = swing_high - diff * ratio
        levels.append(FibLevel(
            ratio=ratio,
            price=price,
            label=label,
            is_retracement=True,
        ))
        # 延伸位 = 波谷 + (diff × ratio)
        price_ext = swing_low + diff * ratio
        levels.append(FibLevel(
            ratio=ratio,
            price=price_ext,
            label=f"{label}",
            is_retracement=False,
        ))

    # 关键延伸位（TradingView 默认）
    extensions = {
        -0.272: "-27.2%",   # 1 - 0.786 + 0.5 ≈ 0.714... 这里直接写
        1.000: "100%",
        1.272: "127.2%",
        1.618: "161.8%",
        2.618: "261.8%",
    }

    for ratio, label in extensions.items():
        price = start_price + diff * ratio
        levels.append(FibLevel(
            ratio=ratio,
            price=price,
            label=label,
            is_retracement=False,
        ))

    return levels


def fib_report(klines: list[Kline]) -> str:
    result = fib_signal(klines)
    if not result:
        return "K线不足，无法计算FIB"
    return fib_signal_report(klines)


# ─── 注意 ────────────────────────────────────────────────────────────────
# K线获取应由外部提供（如 phase2_cache.py 或 GMGN API）
# 本模块只负责计算，不依赖外部API


def fmt_mcap(price: float, supply: float) -> str:
    v = price * supply
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}m"
    elif v >= 1_000:
        return f"${v/1_000:.0f}k"
    return f"${v:,.0f}"


if __name__ == "__main__":
    import subprocess, json, time as time_module
    from datetime import datetime

    CA = "Gv2i54czMSYbkygCKhLRYc59JNVtfrofFwd9mPqZpump"
    CHAIN = "sol"

    # ── 获取 K线（需要外部提供）──────────────────────────────
    # 示例：从phase2_fib导入或使用GMGN CLI
    print("注意：K线获取应由外部提供")
    print("示例：from phase2_fib import get_gmgn_klines")
    exit(0)

    # ── 获取当前市值锚点（GMGN token info）──────────
    r = subprocess.run(
        f"gmgn-cli token info --chain {CHAIN} --address {CA} --raw",
        shell=True, capture_output=True, text=True,
    )
    try:
        info = json.loads(r.stdout)
        price_now = float(info.get("price") or 0)
        supply = float(info.get("circulating_supply") or 0)
        mcap_now = price_now * supply
        mcap_str = fmt_mcap(price_now, supply)
    except Exception:
        price_now = 0
        supply = 0
        mcap_str = "?"

    print(f"GMGN K线: {len(klines)} 根")
    if raw:
        print(f"  覆盖: {datetime.fromtimestamp(raw[0]['time']//1000)} → {datetime.fromtimestamp(raw[-1]['time']//1000)}")
    print(f"当前价格: {price_now:.8f} SOL  市值: {mcap_str}")
    print()
    print(fib_report(klines))
    print()
    print(ao_report(klines))
    print()

    # ── 市值换算（用 GMGN 锚点）────────────────────
    total = 1.0
    result = fib_signal(klines)
    if result.get("action") == "watch" and result.get("levels"):
        lv = result["levels"]
        lines = ["─── FIB 买入/止损位（当前: watch）───",
                 f"  当前收盘:  {result['price']:.8f}  {fmt_mcap(result['price'], supply)}"]
        for label, _ in BUY_RATIOS:
            p = lv.get(label, 0)
            lines.append(f"  {label}  {p:.8f}  {fmt_mcap(p, supply)}")
        lines.append(f"  stop      {lv.get('stop', 0):.8f}  {fmt_mcap(lv.get('stop', 0), supply)}")
        print("\n".join(lines))
        print()
        print(position_report(total, lv))
    elif result.get("action") in ("buy_618", "buy_786", "buy_861"):
        lv = fib_entry_levels(*_swing_from_klines(klines))
        print(position_report(total, lv))
        print(f"\n  → 触发 {result['action']}！ 价格={result['price']:.8f}  需在{result['level']:.8f}入场")
    elif result.get("action") == "stop":
        lv = fib_entry_levels(*_swing_from_klines(klines))
        print(position_report(total, lv))
        print(f"\n  ⚠ 触发止损！ 当前价={result['price']:.8f} <= {result['level']:.8f}")
