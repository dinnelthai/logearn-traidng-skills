#!/usr/bin/env python3
"""
统一K线获取：LogEarn优先，gmgn兜底
市值计算：mcap = closeU × total_supply（单位USD，来自LogEarn）
"""
import sys, os, json, sqlite3, subprocess, time

DB = os.getenv('BACKTEST_DB', '/root/ca-backtester/data/backtest.db')
CACHE = os.getenv('BACKTEST_CACHE', '/root/ca-backtester/cache')
LOGEARN_KEY = os.getenv('LOGEARN_API_KEY', 'sk_3f5eedad86974c0a8680da154b1a8028')
LOGEARN_CLI = os.getenv('LOGEARN_CLI_PATH', '/root/.hermes/skills/logearn/logearn-cli.py')

# ── LogEarn API ─────────────────────────────────────────

def logearn_cmd(cmd_str, *args):
    cmd = ['python3', LOGEARN_CLI, cmd_str] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                      env={**os.environ, 'LOGEARN_API_KEY': LOGEARN_KEY})
    try:
        return json.loads(r.stdout)
    except:
        return []

def get_token_info(ca):
    """从 LogEarn 获取代币信息，返回 {'total_supply': float, 'symbol': str}"""
    result = logearn_cmd('log-get-token-info', '--chain', '3', '--token', ca)
    if result and isinstance(result, list) and len(result) > 0:
        t = result[0][0]
        return {
            'total_supply': t.get('total_supply', 0),
            'symbol': t.get('symbol', 'UNKNOWN'),
            'decimals': t.get('decimals', 6),
        }
    return None

def logearn_kline(ca, interval=300, size=96, end=None):
    cmd = [
        'python3', '/root/.hermes/skills/logearn/logearn-cli.py',
        'log-get-kline',
        '--chain', '3', '--token', ca,
        '--interval', str(interval), '--size', str(size),
    ]
    if end:
        cmd.extend(['--end', str(end)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                       env={**os.environ, 'LOGEARN_API_KEY': LOGEARN_KEY})
    try:
        return json.loads(r.stdout)
    except:
        return []

def fetch_logearn(ca):
    """用LogEarn拉K线，翻页到swap_begin前2小时；每根K线补充market_cap（USD）"""
    cache_file = f"{CACHE}/{ca}_logearn.json"
    
    # 先拿 supply（无论是否有缓存都需要）
    info = get_token_info(ca)
    supply = info['total_supply'] if info else 0
    print(f"  supply: {supply}")
    
    if os.path.exists(cache_file):
        print(f"  📦 LogEarn缓存命中")
        with open(cache_file) as f:
            cached_data = json.load(f)
        
        # 检查缓存是否为空
        if not cached_data or len(cached_data) == 0:
            print(f"  ⚠️ 缓存为空，删除并重新拉取")
            os.remove(cache_file)
            # 继续执行下面的拉取逻辑
        else:
            # 检查缓存是否有 market_cap 字段
            if 'market_cap' not in cached_data[0]:
                print(f"  ⚠️ 缓存无market_cap，需要补充")
                # 补充 market_cap
                if supply and supply > 0:
                    for k in cached_data:
                        closeU = k.get('closeU')
                        if closeU is not None and closeU > 0:
                            k['market_cap'] = round(closeU * supply / 1000, 4)
                    print(f"  💹 市值已补充到缓存数据")
            
            return cached_data

    swap_begin = _get_swap_begin(ca)
    print(f"  swap_begin: {swap_begin}")

    all_klines = []
    current_end = int(time.time())
    max_pages = 100  # 防止无限循环
    page_count = 0

    while page_count < max_pages:
        klines = logearn_kline(ca, interval=300, size=96, end=current_end)
        if not klines:
            print(f"    ⚠️ 第{page_count+1}页无数据，停止翻页")
            break
        
        all_klines.extend(klines)
        oldest = klines[0]['time']
        print(f"    第{page_count+1}页: {len(klines)} 条，最早 {oldest}")
        
        # 检查是否已经拉到足够早的数据
        target_time = (swap_begin - 7200) if swap_begin else 0
        if oldest <= target_time:
            print(f"    ✅ 已拉到目标时间 {target_time}")
            break
        
        # 如果返回的数据少于请求的size，说明已经到头了
        if len(klines) < 96:
            print(f"    ✅ 已拉到最早数据")
            break
        
        current_end = oldest - 1
        page_count += 1

    if page_count >= max_pages:
        print(f"    ⚠️ 达到最大翻页数 {max_pages}，停止")

    # 去重排序（使用字典保证顺序，同时去重）
    seen = {}
    for k in all_klines:
        t = k['time']
        if t not in seen:
            seen[t] = k
    
    # 按时间排序
    unique = sorted(seen.values(), key=lambda x: x['time'])

    # 过滤到swap_begin前2小时
    if swap_begin:
        cutoff = swap_begin - 7200
        unique = [k for k in unique if k['time'] >= cutoff]
        print(f"  过滤后: {len(unique)} 条")
    
    # 验证K线连续性（5分钟间隔=300秒）
    if len(unique) > 1:
        gaps = []
        for i in range(1, len(unique)):
            time_diff = unique[i]['time'] - unique[i-1]['time']
            if time_diff > 600:  # 超过10分钟认为有间隙
                gaps.append({
                    'from': unique[i-1]['time'],
                    'to': unique[i]['time'],
                    'gap_minutes': time_diff / 60
                })
        
        if gaps:
            print(f"  ⚠️ 发现 {len(gaps)} 个时间间隙:")
            for gap in gaps[:3]:  # 只显示前3个
                print(f"     {gap['from']} → {gap['to']} (间隔{gap['gap_minutes']:.0f}分钟)")
            if len(gaps) > 3:
                print(f"     ... 还有 {len(gaps)-3} 个间隙")
        else:
            print(f"  ✅ K线连续性检查通过")

    # 补充 market_cap（closeU × supply，转k单位）
    # closeU 是 USD 价格，市值 = USD价格 × 总量
    if supply and supply > 0:
        for k in unique:
            closeU = k.get('closeU')
            if closeU is not None and closeU > 0:
                k['market_cap'] = round(closeU * supply / 1000, 4)
        
        # 前几条可能closeU=0，用第一个有效值填充
        first_valid_mcap = None
        for k in unique:
            if k.get('market_cap', 0) > 0:
                first_valid_mcap = k['market_cap']
                break
        if first_valid_mcap:
            for k in unique:
                if k.get('market_cap', 0) == 0:
                    k['market_cap'] = first_valid_mcap
        print(f"  💹 市值已补充 (supply={supply:.0f}, 单位k)")
    else:
        print(f"  ⚠️ 无法获取supply，跳过市值字段")

    # 只缓存非空数据
    if unique and len(unique) > 0:
        os.makedirs(CACHE, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(unique, f)
        print(f"  ✅ LogEarn缓存写入: {len(unique)} 条")
    else:
        print(f"  ⚠️ K线数据为空，不写入缓存")
    
    return unique

# ── gmgn 兜底 ───────────────────────────────────────────

def fetch_gmgn(ca):
    """gmgn-cli 拉K线"""
    cache_file = f"{CACHE}/{ca}_gmgn.json"
    if os.path.exists(cache_file):
        print(f"  📦 gmgn缓存命中")
        with open(cache_file) as f:
            return json.load(f)

    swap_begin = _get_swap_begin(ca)

    r = subprocess.run([
        'gmgn-cli', 'market', 'kline',
        '--chain', 'sol', '--address', ca,
        '--resolution', '5m', '--raw'
    ], capture_output=True, text=True, timeout=20)
    try:
        latest = json.loads(r.stdout).get('list', [])
    except:
        return []

    if not latest:
        return []

    newest_ts = latest[-1]['time'] // 1000
    open_ts = (swap_begin - 3600) if swap_begin else (newest_ts - 86400)
    print(f"  时间范围: {open_ts} ~ {newest_ts}")

    all_klines = []
    current_to = newest_ts + 300

    while current_to > open_ts:
        r = subprocess.run([
            'gmgn-cli', 'market', 'kline',
            '--chain', 'sol', '--address', ca,
            '--resolution', '5m', '--to', str(current_to), '--raw'
        ], capture_output=True, text=True, timeout=20)
        try:
            lst = json.loads(r.stdout).get('list', [])
        except:
            break
        if not lst:
            break
        all_klines.extend(lst)
        oldest = lst[0]['time'] // 1000
        print(f"    拉到 {len(lst)} 条，最早 {oldest}")
        if len(lst) < 100:
            break
        current_to = oldest - 300

    seen = set()
    unique = []
    for k in reversed(all_klines):
        t = k['time'] // 1000
        if t not in seen and (not swap_begin or t >= swap_begin - 7200):
            seen.add(t)
            unique.append(k)
    unique.sort(key=lambda x: x['time'])

    os.makedirs(CACHE, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(unique, f)
    print(f"  ✅ gmgn缓存写入: {len(unique)} 条")
    return unique

def _get_swap_begin(ca):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT swap_begin_time FROM raw_tokens WHERE token_address = ?", (ca,))
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row and row[0] else None

# ── 统一入口 ────────────────────────────────────────────

def fetch_klines(ca):
    """优先LogEarn，兜底gmgn"""
    print(f"  [LogEarn] 尝试获取K线...")
    raw = fetch_logearn(ca)

    if raw and len(raw) >= 50:
        print(f"  ✅ LogEarn获取到 {len(raw)} 条")
        return raw

    print(f"  ⚠️ LogEarn数据不足({len(raw) if raw else 0}条)，尝试gmgn...")
    raw_gmgn = fetch_gmgn(ca)
    if raw_gmgn and len(raw_gmgn) >= 50:
        print(f"  ✅ gmgn获取到 {len(raw_gmgn)} 条")
        return raw_gmgn

    print(f"  ❌ 两个数据源都失败")
    return raw or []

def validate_klines_integrity(klines, interval=300):
    """
    验证K线完整性
    
    Args:
        klines: K线列表
        interval: K线间隔（秒），默认300（5分钟）
    
    Returns:
        dict: {
            'is_complete': bool,
            'total_count': int,
            'gaps': list,
            'missing_count': int
        }
    """
    if not klines or len(klines) < 2:
        return {
            'is_complete': True,
            'total_count': len(klines),
            'gaps': [],
            'missing_count': 0
        }
    
    gaps = []
    missing_count = 0
    
    for i in range(1, len(klines)):
        expected_time = klines[i-1]['time'] + interval
        actual_time = klines[i]['time']
        time_diff = actual_time - klines[i-1]['time']
        
        if time_diff > interval * 1.5:  # 允许50%的误差
            missing = (time_diff // interval) - 1
            gaps.append({
                'index': i,
                'from_time': klines[i-1]['time'],
                'to_time': actual_time,
                'gap_seconds': time_diff,
                'missing_bars': int(missing)
            })
            missing_count += int(missing)
    
    return {
        'is_complete': len(gaps) == 0,
        'total_count': len(klines),
        'gaps': gaps,
        'missing_count': missing_count
    }


def normalize_klines(raw, supply=None):
    """raw_klines → list[dict]，market_cap单位k（千美元）"""
    result = []
    for k in raw:
        item = {
            'time': k['time'] // 1000 if isinstance(k['time'], int) and k['time'] > 1e12 else k['time'],
            'open': float(k['open']),
            'high': float(k['high']),
            'low': float(k['low']),
            'close': float(k['close']),
            'volume': float(k.get('volume', 0)),
        }
        if 'market_cap' in k:
            item['market_cap'] = k['market_cap']  # USD
        result.append(item)
    
    # 验证完整性
    integrity = validate_klines_integrity(result)
    if not integrity['is_complete']:
        print(f"  ⚠️ K线不完整: 缺失 {integrity['missing_count']} 根，{len(integrity['gaps'])} 个间隙")
    
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 fetch_klines.py <CA>")
        sys.exit(1)
    ca = sys.argv[1]
    klines = fetch_klines(ca)
    print(f"共 {len(klines)} 条K线")
