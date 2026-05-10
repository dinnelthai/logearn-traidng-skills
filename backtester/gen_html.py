#!/usr/bin/env python3
"""生成 HTML 报表"""
import sqlite3, json, os, time, requests

DB = '/root/ca-backtester/data/backtest.db'
OUT = '/root/ca-backtester/reports/backtest_report.html'
DEX_URL = 'https://api.dexscreener.com/latest/dex/tokens'

# 缓存 dexscreener 的 mcap+supply 数据（每个 CA 只查一次）
_mcap_cache = {}

def get_mcap_supply(ca):
    """从 dexscreener 拿当前 mcap 和 supply（USD mcap / priceUsd）"""
    if ca in _mcap_cache:
        return _mcap_cache[ca]
    try:
        r = requests.get(f'{DEX_URL}/{ca}', timeout=8)
        if r.status_code == 200:
            data = r.json()
            pairs = data.get('pairs', [])
            if pairs:
                top = pairs[0]
                mc = top.get('marketCap') or 0
                pu = top.get('priceUsd') or 0
                supply = mc / float(pu) if pu else 0
                result = (mc, supply)
                _mcap_cache[ca] = result
                return result
    except Exception:
        pass
    _mcap_cache[ca] = (None, None)
    return (None, None)

def price_to_mcap(price_sol, supply):
    """把 SOL 价格 + 供应量 转成市值（USD）"""
    if price_sol and supply:
        try:
            r = requests.get(f'{DEX_URL}/So11111111111111111111111111111111111111112', timeout=5)
            if r.status_code == 200:
                pairs = r.json().get('pairs', [])
                if pairs:
                    sol_usd = float(pairs[0].get('priceUsd', 0))
                    if sol_usd:
                        return price_sol * sol_usd * supply
        except Exception:
            pass
    return None

def fmt_pct(v):
    color = '#00ff88' if v >= 0 else '#ff4444'
    return f"<span style='color:{color}'>{v:+.2f}%</span>"

def fmt_mcap(mc):
    if mc is None:
        return '—'
    if mc >= 1_000_000:
        return f'${mc/1_000_000:.1f}M'
    if mc >= 1_000:
        return f'${mc/1_000:.1f}K'
    return f'${mc:,.0f}'

def _fmt_mcap_k(v):
    """格式化市值（单位k），输出 $X.XK 或 $X.XM"""
    if not v or v <= 0:
        return '—'
    # v 已经是以k为单位，不需要再乘1000
    if v >= 1000:
        # >= 1000k = >= 1M
        return f"${v/1000:.1f}M"
    else:
        # < 1000k
        return f"${v:.1f}K"

def trades_html(tjson, ca, supply):
    """
    适配新版 win_rate_analyzer 返回的交易格式（只有摘要，无详细买卖点）。
    trades: [{trade_number, matched, profit_sol, profit_rate, is_win,
              buy_time, sell_time, market_cap_at_buy, market_cap_at_sell,
              buy_count, sell_count}, ...]
    """
    if not tjson:
        return "无"
    try:
        trades = json.loads(tjson)
    except:
        return "解析失败"
    if not trades:
        return "无交易"

    # 获取 SOL USD 价格
    sol_usd = None
    try:
        r = requests.get(f'{DEX_URL}/So11111111111111111111111111111111111111112', timeout=5)
        if r.status_code == 200:
            pairs = r.json().get('pairs', [])
            if pairs:
                sol_usd = float(pairs[0].get('priceUsd', 0))
    except Exception:
        pass
    if not sol_usd:
        return "无 SOL 价格"

    rows_t = []
    for t in trades:
        i = t.get('trade_number', 0)
        buy_time = t.get('buy_time')
        sell_time = t.get('sell_time')
        buy_str = time.strftime('%m-%d %H:%M', time.localtime(buy_time)) if buy_time else '—'
        sell_str = time.strftime('%m-%d %H:%M', time.localtime(sell_time)) if sell_time else '—'
        buy_count = t.get('buy_count', 0)
        sell_count = t.get('sell_count', 0)
        is_win = t.get('is_win', False)
        win_tag = '🟢' if is_win else '🔴'
        mcap_buy = t.get('market_cap_at_buy', 0)
        mcap_sell = t.get('market_cap_at_sell', 0)
        rows_t.append(
            f"<tr>"
            f"<td>#{i} {win_tag}</td>"
            f"<td>{buy_str}</td>"
            f"<td>{sell_str}</td>"
            f"<td>{buy_count}档</td>"
            f"<td>{sell_count}次</td>"
            f"<td>{_fmt_mcap_k(mcap_buy)}</td>"
            f"<td>{_fmt_mcap_k(mcap_sell)}</td>"
            f"<td>{t['profit_rate']*100:+.2f}%</td>"
            f"<td>{t.get('profit_sol', 0):+.4f} SOL</td>"
            f"</tr>"
        )
    header = "<tr><th>#</th><th>买入时间</th><th>卖出时间</th><th>买入档</th><th>卖出次</th><th>买入市值</th><th>卖出市值</th><th>收益率</th><th>SOL盈亏</th></tr>"
    return f"<table class='trade-table'>{header}{''.join(rows_t)}</table>"

def render():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # 只保留K线完整的CA（无缺口）
    cur.execute("""
        SELECT p.token_address, p.symbol, p.mcap, p.swap_begin_time,
               p.bt_trade_count, p.bt_win_count, p.bt_win_rate,
               p.bt_total_profit_pct, p.bt_min_profit_pct, p.bt_max_profit_pct,
               p.bt_trades_json, p.bt_klines_count
        FROM phase2_signals p
        WHERE p.symbol IN ('Clawd', 'GAYTES', 'UFO')
        ORDER BY p.bt_total_profit_pct DESC
    """)
    rows = cur.fetchall()
    conn.close()

    total_cas = len(rows)
    total_trades = sum(r[4] for r in rows)
    winning_cas = sum(1 for r in rows if r[6] and r[6] > 0)
    total_profit = sum(r[7] for r in rows)
    profit_color = '#00ff88' if total_profit >= 0 else '#ff4444'
    
    # 计算每次交易的胜率统计
    trades_by_number = {}  # {trade_number: {"total": 0, "wins": 0, "profit_sum": 0}}
    
    for r in rows:
        tjson = r[10]  # bt_trades_json
        if not tjson:
            continue
        try:
            trades = json.loads(tjson)
            for t in trades:
                trade_num = t.get('trade_number', 0)
                if trade_num not in trades_by_number:
                    trades_by_number[trade_num] = {"total": 0, "wins": 0, "profit_sum": 0}
                
                trades_by_number[trade_num]["total"] += 1
                if t.get('is_win', False):
                    trades_by_number[trade_num]["wins"] += 1
                trades_by_number[trade_num]["profit_sum"] += t.get('profit_rate', 0) * 100
        except:
            pass
    
    # 计算胜率
    win_rate_stats = {}
    for trade_num in sorted(trades_by_number.keys()):
        stat = trades_by_number[trade_num]
        total = stat["total"]
        wins = stat["wins"]
        win_rate = (wins / total * 100) if total > 0 else 0
        avg_profit = stat["profit_sum"] / total if total > 0 else 0
        win_rate_stats[trade_num] = {
            "total": total,
            "wins": wins,
            "win_rate": win_rate,
            "avg_profit": avg_profit
        }

    # 静态CSS（不用f-string嵌套）
    css = """
body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }
h1 { color: #00d4ff; }
h2 { color: #00d4ff; margin-top: 30px; }
.card-grid { display: flex; gap: 20px; margin-bottom: 30px; }
.card { background: #16213e; padding: 20px; border-radius: 10px; text-align: center; flex: 1; }
.card .val { font-size: 2em; font-weight: bold; color: #00d4ff; }
.card .label { color: #aaa; margin-top: 5px; }
.win-rate-section { background: #16213e; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
.win-rate-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }
.win-rate-card { background: #0f3460; padding: 15px; border-radius: 8px; border-left: 4px solid #00d4ff; }
.win-rate-card h3 { margin: 0 0 10px 0; color: #00d4ff; font-size: 1.2em; }
.win-rate-bar { background: #1a1a2e; height: 30px; border-radius: 5px; overflow: hidden; margin: 10px 0; position: relative; }
.win-rate-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #00ff88); display: flex; align-items: center; justify-content: center; color: #000; font-weight: bold; transition: width 0.3s; }
.win-rate-stats { display: flex; justify-content: space-between; font-size: 0.9em; color: #aaa; }
.stat-item { text-align: center; }
.stat-item .val { color: #00d4ff; font-size: 1.3em; font-weight: bold; display: block; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
th { background: #0f3460; padding: 10px; text-align: left; }
td { padding: 8px; border-bottom: 1px solid #333; }
tr:hover { background: #1f4068; }
.ca-link { color: #00d4ff; text-decoration: none; }
.trade-table { font-size: 0.85em; margin-top: 5px; }
.trade-table th, .trade-table td { padding: 4px 8px; }
button { cursor: pointer; background: #0f3460; color: #00d4ff; border: none; padding: 4px 8px; border-radius: 4px; }
"""

    body = "<h1>📊 CA 回测报表</h1>\n"
    body += f"""<div class="card-grid">
  <div class="card"><div class="val">{total_cas}</div><div class="label">CA 总数</div></div>
  <div class="card"><div class="val">{total_trades}</div><div class="label">总交易笔数</div></div>
  <div class="card"><div class="val">{winning_cas}</div><div class="label">盈利 CA 数</div></div>
  <div class="card"><div class="val" style="color:{profit_color}">{total_profit:+.2f}%</div><div class="label">净盈亏</div></div>
</div>"""
    
    # 添加胜率统计展示
    if win_rate_stats:
        body += '<div class="win-rate-section">'
        body += '<h2>📈 交易次数胜率分析</h2>'
        body += '<div class="win-rate-grid">'
        
        for trade_num in sorted(win_rate_stats.keys()):
            stat = win_rate_stats[trade_num]
            win_rate = stat['win_rate']
            total = stat['total']
            wins = stat['wins']
            losses = total - wins
            avg_profit = stat['avg_profit']
            
            # 胜率颜色
            if win_rate >= 60:
                bar_color = 'linear-gradient(90deg, #00ff88, #00d4ff)'
                emoji = '🟢'
            elif win_rate >= 50:
                bar_color = 'linear-gradient(90deg, #ffaa00, #ff8800)'
                emoji = '🟡'
            else:
                bar_color = 'linear-gradient(90deg, #ff4444, #ff6666)'
                emoji = '🔴'
            
            profit_color_val = '#00ff88' if avg_profit >= 0 else '#ff4444'
            
            body += f'''
<div class="win-rate-card">
  <h3>{emoji} 第{trade_num}次交易</h3>
  <div class="win-rate-bar">
    <div class="win-rate-fill" style="width: {win_rate}%; background: {bar_color};">
      {win_rate:.1f}%
    </div>
  </div>
  <div class="win-rate-stats">
    <div class="stat-item">
      <span class="val">{total}</span>
      <span>总数</span>
    </div>
    <div class="stat-item">
      <span class="val" style="color: #00ff88">{wins}</span>
      <span>盈利</span>
    </div>
    <div class="stat-item">
      <span class="val" style="color: #ff4444">{losses}</span>
      <span>亏损</span>
    </div>
    <div class="stat-item">
      <span class="val" style="color: {profit_color_val}">{avg_profit:+.1f}%</span>
      <span>平均</span>
    </div>
  </div>
</div>'''
        
        body += '</div></div>'

    table_header = """<table>
<thead><tr>
  <th>CA</th><th>Symbol</th><th>Mcap</th><th>Swap_begin</th>
  <th>笔数</th><th>胜率</th><th>总盈亏</th><th>区间</th>
  <th>K线数</th><th>交易明细</th>
</tr></thead>
<tbody>"""
    body += table_header

    for r in rows:
        addr, sym, mcap, sbt, tc, wc, wr, tp, minp, maxp, tjson, kcnt = r
        # 从 dexscreener 拿当前 mcap 和 supply
        cur_mcap, supply = get_mcap_supply(addr)
        wr_str = f"{wr*100:.1f}%" if wr else "—"
        mcap_str = fmt_mcap(cur_mcap)  # 用实时市值
        sbt_str = str(int(sbt)) if sbt else "—"
        klines_str = str(kcnt) if kcnt else "—"
        addr_short = addr[:12]
        addr_key = addr[:8].replace(' ', '_')

        logearn_url = f"https://logearn.com/en/solana/tokens/{addr}"
        row = f"""<tr>
  <td><a class="ca-link" href="{logearn_url}" target="_blank">{addr_short}...</a></td>
  <td><b>{sym or '?'}</b></td>
  <td>{mcap_str}</td>
  <td>{sbt_str}</td>
  <td>{tc}</td>
  <td>{wr_str}</td>
  <td>{fmt_pct(tp)}</td>
  <td>{fmt_pct(minp)} ~ {fmt_pct(maxp)}</td>
  <td>{klines_str}</td>
  <td><button onclick="toggle('{addr_key}')">展开</button>
    <div id="t{addr_key}" style="display:none;margin-top:5px">{trades_html(tjson, addr, supply)}</div></td>
</tr>"""
        body += row

    body += "</tbody></table>"

    js = """<script>
function toggle(id) {
  var el = document.getElementById('t' + id);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}
</script>"""

    html = f"<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'><title>CA 回测报表</title><style>{css}</style></head><body>{body}{js}</body></html>"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write(html)
    print(f"✅ 报表已生成: {OUT}")

if __name__ == '__main__':
    render()
