#!/usr/bin/env python3
"""
zuemen 個人頁「活的」動圖產生器（只用 Python 標準函式庫，GitHub Actions 直接跑）

每次執行會抓真實資料，重畫 assets/live/ 底下的 SVG 動圖：
  1. header.svg            頁首：區塊吉祥物 + 量子軌道 + 即時跑馬燈（區塊高度、BTC、VaR）
  2. chain-of-commits.svg  區塊鏈：把每週 GitHub 貢獻當成一個區塊「挖」出來，雜湊鏈接前一塊
  3. quantum-finance.svg   量子金融：BTC 日報酬分佈 → 3 qubit 振幅載入電路（QAE 的第一步）
  4. onchain-pulse.svg     鏈上脈動：Base Sepolia / Ethereum Sepolia / Monad 測試網即時區塊

資料抓不到時改用 data/cache.json 的上一次結果，確保 README 永遠有圖。
"""
import hashlib
import html
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

# ── 基本設定 ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo 根目錄
OUT = os.path.join(ROOT, "assets", "live")                             # 輸出資料夾
CACHE_PATH = os.path.join(ROOT, "data", "cache.json")                  # 失敗時的備援快取
USER = os.environ.get("GH_USER", "zuemen")                             # GitHub 帳號
TOKEN = os.environ.get("GH_TOKEN", "")                                 # Actions 內建 GITHUB_TOKEN
FIXTURE = os.environ.get("PROFILE_FIXTURE", "")                        # 本機測試用假資料
TPE = timezone(timedelta(hours=8))                                     # 台北時區
NOW = datetime.now(TPE)

# 我實際部署過合約的測試網（顏色對應各鏈品牌色）
CHAINS = [
    {"key": "base", "name": "Base Sepolia", "rpc": "https://sepolia.base.org", "color": "#2f6bff"},
    {"key": "sepolia", "name": "Ethereum Sepolia", "rpc": "https://ethereum-sepolia-rpc.publicnode.com", "color": "#8b949e"},
    {"key": "monad", "name": "Monad Testnet", "rpc": "https://testnet-rpc.monad.xyz", "color": "#a371f7"},
]

# 共用配色（GitHub 深色主題）
C = {"bg": "#0a0a0b", "panel": "#111114", "line": "#222228", "rule": "#34343b", "text": "#ecebe6",
     "text2": "#a6a59f", "muted": "#8a8a93", "label": "#8f8e88",
     "cyan": "#9bb6d8", "green": "#8cc9a1", "amber": "#e3c07a", "red": "#f0907a", "purple": "#b4a6d6"}
MONO = 'font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"'
SANS = 'font-family="IBM Plex Sans,-apple-system,BlinkMacSystemFont,Segoe UI,Microsoft JhengHei,PingFang TC,sans-serif"'
SERIF = 'font-family="Newsreader,Georgia,Times New Roman,Microsoft JhengHei,PingFang TC,serif"'


# ── 抓資料 ──────────────────────────────────────────────────────────────────
def http_json(url, payload=None, headers=None, timeout=20):
    """發 HTTP 請求並解析 JSON；payload 不為 None 時用 POST"""
    h = {"User-Agent": "zuemen-profile-bot", "Accept": "application/json"}
    if headers:
        h.update(headers)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fetch_contrib():
    """GitHub GraphQL：過去一年的每日貢獻數（需要 token）"""
    if not TOKEN:
        raise RuntimeError("GH_TOKEN 未設定")
    q = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
         "totalContributions weeks{contributionDays{date contributionCount}}}}}}")
    r = http_json("https://api.github.com/graphql", {"query": q, "variables": {"login": USER}},
                  {"Authorization": f"bearer {TOKEN}"})
    cal = r["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [{"date": d["date"], "count": d["contributionCount"]} for w in cal["weeks"] for d in w["contributionDays"]]
    return {"total": cal["totalContributions"], "days": days}


def fetch_commits():
    """GitHub REST：取最近有推送的公開 repo，各拿最新 commit，組成「mempool」
    （事件 API 已不再附 commit 內容，所以改讀 repos → commits）"""
    h = {"Authorization": f"bearer {TOKEN}"} if TOKEN else {}
    repos = http_json(f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=8&type=owner", headers=h)
    out = []
    for r in repos:
        if r.get("fork") or r["name"].lower() == USER.lower():   # 略過 fork 與個人頁 repo 本身
            continue
        try:
            cs = http_json(f"https://api.github.com/repos/{USER}/{r['name']}/commits?per_page=1", headers=h)
        except Exception:
            continue
        if cs:
            out.append({"repo": r["name"], "msg": cs[0]["commit"]["message"].splitlines()[0], "sha": cs[0]["sha"][:7]})
        if len(out) >= 5:
            break
    if not out:
        raise RuntimeError("找不到最近的公開 commit")
    return out


def fetch_btc():
    """BTC/USD 日收盤價：CoinGecko 為主，Coinbase 為備援（Actions 主機在美國，避開 Binance）"""
    try:
        r = http_json("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
                      "?vs_currency=usd&days=120&interval=daily")
        prices, src = [p[1] for p in r["prices"]], "CoinGecko"
    except Exception:
        r = http_json("https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400")
        r = sorted(r, key=lambda x: x[0])[-121:]
        prices, src = [c[4] for c in r], "Coinbase"
    if len(prices) < 30:
        raise RuntimeError("價格資料不足")
    return {"prices": prices[-121:], "source": src}


def rpc(url, method, params=None):
    """以太坊 JSON-RPC 呼叫"""
    r = http_json(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []})
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def fetch_chain(chain):
    """最新區塊高度、gas、交易數，以及最近 100 塊的平均出塊時間"""
    blk = rpc(chain["rpc"], "eth_getBlockByNumber", ["latest", False])
    n = int(blk["number"], 16)
    old = rpc(chain["rpc"], "eth_getBlockByNumber", [hex(n - 100), False])
    gas = int(rpc(chain["rpc"], "eth_gasPrice"), 16)
    bt = (int(blk["timestamp"], 16) - int(old["timestamp"], 16)) / 100
    return {"number": n, "gwei": gas / 1e9, "txs": len(blk["transactions"]),
            "block_time": max(bt, 0.1), "hash": blk["hash"]}


def get(key, fn, cache, status, fixture):
    """抓資料的統一入口：fixture → 即時 → 快取 → None，並記錄狀態"""
    if key in fixture:
        status[key] = "fixture"
        return fixture[key]
    try:
        value = fn()
        cache[key] = {"value": value, "at": NOW.isoformat()}
        status[key] = "live"
        return value
    except Exception as e:
        print(f"[warn] {key}: {e}", file=sys.stderr)
        if key in cache:
            status[key] = "cached"
            return cache[key]["value"]
        status[key] = "missing"
        return None


# ── 數學：量子振幅載入 ──────────────────────────────────────────────────────
def log_returns(prices):
    """r_t = ln(P_t / P_{t-1})"""
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def amplitude_loading(returns, n_qubits=3):
    """
    把報酬分佈 p_i 載入量子態 |ψ⟩ = Σ √p_i |i⟩（Grover–Rudolph 二元樹法）
    第 l 層第 j 個節點的 Ry 角度：θ = 2·arccos( √(P_左 / P_節點) )
    因為 Ry(θ)|0⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩，cos²(θ/2) 正好等於「走左邊」的機率
    """
    k = 2 ** n_qubits
    lo, hi = min(returns), max(returns)
    width = (hi - lo) / k or 1e-12
    counts = [0] * k
    for r in returns:
        counts[min(int((r - lo) / width), k - 1)] += 1
    p = [c / len(returns) for c in counts]

    angles = []
    for lvl in range(n_qubits):
        size, row = k >> lvl, []
        for j in range(2 ** lvl):
            seg = p[j * size:(j + 1) * size]
            tot, left = sum(seg), sum(seg[:size // 2])
            row.append(2 * math.acos(math.sqrt(min(1.0, left / tot))) if tot > 0 else 0.0)
        angles.append(row)

    # 驗算：用角度重建每個基底態的機率，跟目標分佈比較（保真度應為 1）
    rebuilt = []
    for i in range(k):
        amp, node = 1.0, 0
        for lvl in range(n_qubits):
            bit = (i >> (n_qubits - 1 - lvl)) & 1
            th = angles[lvl][node]
            amp *= math.sin(th / 2) if bit else math.cos(th / 2)
            node = node * 2 + bit
        rebuilt.append(amp * amp)
    fidelity = sum(math.sqrt(a * b) for a, b in zip(p, rebuilt)) ** 2
    edges = [lo + i * width for i in range(k + 1)]
    return p, angles, edges, fidelity


def var95(returns):
    """歷史模擬法 1 日 VaR(95%)：報酬的第 5 百分位數取負號"""
    s = sorted(returns)
    return -s[max(0, int(0.05 * len(s)) - 1)]


# ── SVG 小工具 ─────────────────────────────────────────────────────────────
def esc(s):
    return html.escape(str(s), quote=True)


def window(w, h, title, body, footer=""):
    """統一的「終端機視窗」外框"""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<style>@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect width="{w}" height="{h}" rx="6" fill="{C['bg']}" stroke="{C['line']}"/>
<path d="M6 0H{w-6}A6 6 0 0 1 {w} 6V34H0V6A6 6 0 0 1 6 0z" fill="{C['panel']}"/>
<circle cx="20" cy="17" r="5" fill="{C['red']}"/><circle cx="38" cy="17" r="5" fill="{C['amber']}"/><circle cx="56" cy="17" r="5" fill="{C['green']}"/>
<text x="80" y="22" {MONO} font-size="13" fill="{C['muted']}">{esc(title)}</text>
{body}
<text x="{w-16}" y="{h-12}" text-anchor="end" {MONO} font-size="10" fill="{C['muted']}">{esc(footer)}</text>
</svg>
'''


def stamp(status_keys, status):
    """右下角時間戳：顯示更新時間與資料狀態（live / cached）"""
    states = {status.get(k, "missing") for k in status_keys}
    tag = "live" if states <= {"live", "fixture"} else ("cached" if "missing" not in states else "partial")
    return f"updated {NOW:%Y-%m-%d %H:%M} UTC+8 · {tag}"


# ── 1. 區塊鏈：每週貢獻 = 一個區塊 ─────────────────────────────────────────
def render_chain(contrib, commits, status):
    w, h = 900, 330
    if not contrib:
        return window(w, h, "chain-of-commits", f'<text x="450" y="170" text-anchor="middle" {MONO} fill="{C["muted"]}">waiting for first sync…</text>')
    days = contrib["days"]
    # 依週分組，取最近 6 週（最後一週 = 正在挖的區塊）
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)][-6:]
    total = contrib["total"]
    streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            streak += 1
        elif d["date"] != days[-1]["date"]:
            break

    body, prev = [], "0" * 64
    height0 = len(days) // 7 - len(weeks)        # 區塊高度 = 一年內的週序號
    bw, gap, x0, y0 = 118, 28, 24, 58
    for i, wk in enumerate(weeks):
        tx = sum(d["count"] for d in wk)
        digest = hashlib.sha256(f"{prev}{wk[0]['date']}{tx}".encode()).hexdigest()
        x = x0 + i * (bw + gap)
        mining = i == len(weeks) - 1
        stroke = C["amber"] if mining else C["cyan"]
        dash = ' stroke-dasharray="8 6"' if mining else ""
        anim = '<animate attributeName="stroke-dashoffset" values="0;-28" dur="1.2s" repeatCount="indefinite"/>' if mining else ""
        # 區塊本體
        body.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="132" rx="12" fill="{C["panel"]}" stroke="{stroke}" stroke-width="2"{dash}>{anim}</rect>')
        body.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="26" rx="12" fill="{stroke}" opacity=".18"/>')
        body.append(f'<text x="{x+10}" y="{y0+18}" {MONO} font-size="12" font-weight="700" fill="{stroke}">#{height0+i+1}</text>')
        body.append(f'<text x="{x+bw-10}" y="{y0+18}" text-anchor="end" {MONO} font-size="10" fill="{C["muted"]}">{wk[0]["date"][5:]}</text>')
        body.append(f'<text x="{x+10}" y="{y0+48}" {MONO} font-size="11" fill="{C["muted"]}">txs</text>')
        body.append(f'<text x="{x+bw-10}" y="{y0+48}" text-anchor="end" {MONO} font-size="16" font-weight="700" fill="{C["text"]}">{tx}</text>')
        # 每日貢獻做成 7 格小熱度條
        for j, d in enumerate(wk):
            lv = min(d["count"], 8) / 8
            body.append(f'<rect x="{x+10+j*14}" y="{y0+60}" width="11" height="11" rx="2" fill="{C["green"]}" opacity="{0.12+0.88*lv:.2f}"/>')
        body.append(f'<text x="{x+10}" y="{y0+92}" {MONO} font-size="10" fill="{C["muted"]}">prev 0x{prev[:8]}</text>')
        if mining:
            # 正在挖：nonce 輪播，最後找到雜湊變綠
            for k in range(4):
                nonce = hashlib.sha256(f"{digest}{k}".encode()).hexdigest()[:8]
                body.append(f'<text x="{x+10}" y="{y0+110}" {MONO} font-size="10" fill="{C["amber"]}" opacity="0">nonce 0x{nonce}'
                            f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;{0.01+k*0.15:.2f};{0.15+k*0.15:.2f};1" dur="4s" repeatCount="indefinite"/></text>')
            body.append(f'<text x="{x+10}" y="{y0+110}" {MONO} font-size="10" fill="{C["green"]}" opacity="0">hash 0x{digest[:8]} ✓'
                        f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;.62;.66;1" dur="4s" repeatCount="indefinite"/></text>')
            body.append(f'<text x="{x+bw/2}" y="{y0+150}" text-anchor="middle" {MONO} font-size="10" fill="{C["amber"]}">mining this week…</text>')
        else:
            body.append(f'<text x="{x+10}" y="{y0+110}" {MONO} font-size="10" fill="{C["cyan"]}">hash 0x{digest[:8]}</text>')
        # 區塊之間的鏈結
        if i < len(weeks) - 1:
            lx = x + bw
            body.append(f'<g fill="none" stroke="{C["line"]}" stroke-width="3"><rect x="{lx+2}" y="{y0+58}" width="16" height="12" rx="6"/><rect x="{lx+10}" y="{y0+58}" width="16" height="12" rx="6"/></g>')
        prev = digest

    # mempool：最近的 commit 一筆筆飛進正在挖的區塊
    mx = x0 + (len(weeks) - 1) * (bw + gap) + bw / 2
    body.append(f'<text x="{x0}" y="{y0+182}" {MONO} font-size="11" fill="{C["muted"]}">mempool · recent public commits</text>')
    for i, cm in enumerate(commits or []):
        label = f'{cm["repo"]} · {cm["msg"]}'
        label = label if len(label) <= 46 else label[:45] + "…"
        y = y0 + 198 + i * 18
        t0, t1 = 0.1 + i * 0.12, 0.3 + i * 0.12
        body.append(f'<g><text x="{x0}" y="{y}" {MONO} font-size="11" fill="{C["text"]}">'
                    f'<tspan fill="{C["green"]}">{esc(cm["sha"])}</tspan> {esc(label)}</text>'
                    f'<animate attributeName="opacity" values="1;1;.25;.25;1" keyTimes="0;{t0:.2f};{t1:.2f};.95;1" dur="6s" repeatCount="indefinite"/></g>')
        body.append(f'<circle r="4" fill="{C["green"]}" opacity="0"><animateMotion dur="6s" repeatCount="indefinite" calcMode="linear" '
                    f'keyPoints="0;0;1;1" keyTimes="0;{t0:.2f};{t1:.2f};1" path="M{x0+390} {y-4} Q {mx-60} {y0+170} {mx} {y0+132}"/>'
                    f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{t0-0.01:.2f};{t0:.2f};{t1:.2f};{t1+0.01:.2f};1" dur="6s" repeatCount="indefinite"/></circle>')
    body.append(f'<text x="{w-24}" y="{y0+182}" text-anchor="end" {MONO} font-size="11" fill="{C["muted"]}">'
                f'1y contributions <tspan fill="{C["text"]}" font-weight="700">{total}</tspan> · streak <tspan fill="{C["text"]}" font-weight="700">{streak}d</tspan></text>')
    return window(w, h, f"chain-of-commits — weekly blocks mined from github.com/{USER}", "\n".join(body),
                  stamp(["contrib", "commits"], status))


# ── 2. 量子金融：BTC 報酬分佈的振幅載入 ─────────────────────────────────────
def render_quantum(btc, status):
    w, h = 900, 360
    if not btc:
        return window(w, h, "quantum-finance", f'<text x="450" y="180" text-anchor="middle" {MONO} fill="{C["muted"]}">waiting for first sync…</text>')
    rets = log_returns(btc["prices"])
    p, angles, edges, fid = amplitude_loading(rets, 3)
    v95 = var95(rets)
    tail = sum(pi for pi, hi in zip(p, edges[1:]) if hi <= -v95 + 1e-12)
    price = btc["prices"][-1]
    b = []

    # 電路：3 條 qubit 線
    wires = [96, 156, 216]
    for qi, y in enumerate(wires):
        b.append(f'<text x="26" y="{y+4}" {MONO} font-size="12" fill="{C["muted"]}">q{qi} |0⟩</text>')
        b.append(f'<line x1="80" y1="{y}" x2="420" y2="{y}" stroke="{C["line"]}" stroke-width="2"/>')

    def gate(x, y, label, glow_t):
        """畫一個 Ry 閘，量子訊號經過時發光"""
        return (f'<rect x="{x-17}" y="{y-14}" width="34" height="28" rx="6" fill="{C["panel"]}" stroke="{C["purple"]}" stroke-width="2">'
                f'<animate attributeName="fill" values="{C["panel"]};{C["panel"]};#3b2a5c;{C["panel"]};{C["panel"]}" '
                f'keyTimes="0;{max(glow_t-0.04,0):.2f};{glow_t:.2f};{min(glow_t+0.06,0.99):.2f};1" dur="5s" repeatCount="indefinite"/></rect>'
                f'<text x="{x}" y="{y+4}" text-anchor="middle" {MONO} font-size="11" fill="{C["text"]}">{label}</text>')

    def ctrl(x, y, on):
        """控制點：實心 = 控制在 |1⟩，空心 = 控制在 |0⟩"""
        return f'<circle cx="{x}" cy="{y}" r="5" fill="{C["purple"] if on else C["bg"]}" stroke="{C["purple"]}" stroke-width="2"/>'

    span = 420 - 80
    def t_at(x):
        return (x - 80) / span * 0.8          # 訊號從左到右走完 80% 時間

    # 第 0 層：q0 上的 Ry(θ0)
    b.append(gate(112, wires[0], "Ry", t_at(112)))
    # 第 1 層：q1 上兩個受 q0 控制的 Ry
    for j, x in enumerate([176, 226]):
        b.append(f'<line x1="{x}" y1="{wires[0]}" x2="{x}" y2="{wires[1]}" stroke="{C["purple"]}" stroke-width="2"/>')
        b.append(ctrl(x, wires[0], j)); b.append(gate(x, wires[1], "Ry", t_at(x)))
    # 第 2 層：q2 上四個受 (q0,q1) 控制的 Ry
    for j, x in enumerate([276, 312, 348, 384]):
        b.append(f'<line x1="{x}" y1="{wires[0]}" x2="{x}" y2="{wires[2]}" stroke="{C["purple"]}" stroke-width="2"/>')
        b.append(ctrl(x, wires[0], (j >> 1) & 1)); b.append(ctrl(x, wires[1], j & 1))
        b.append(f'<rect x="{x-14}" y="{wires[2]-14}" width="28" height="28" rx="6" fill="{C["panel"]}" stroke="{C["purple"]}" stroke-width="2">'
                 f'<animate attributeName="fill" values="{C["panel"]};{C["panel"]};#3b2a5c;{C["panel"]};{C["panel"]}" '
                 f'keyTimes="0;{t_at(x)-0.04:.2f};{t_at(x):.2f};{t_at(x)+0.06:.2f};1" dur="5s" repeatCount="indefinite"/></rect>'
                 f'<text x="{x}" y="{wires[2]+4}" text-anchor="middle" {MONO} font-size="9" fill="{C["text"]}">Ry</text>')
    # 量測符號
    for y in wires:
        b.append(f'<rect x="404" y="{y-13}" width="30" height="26" rx="5" fill="{C["panel"]}" stroke="{C["muted"]}"/>'
                 f'<path d="M409 {y+6}a10 10 0 0 1 20 0" fill="none" stroke="{C["muted"]}" stroke-width="1.6"/>'
                 f'<line x1="419" y1="{y+6}" x2="427" y2="{y-6}" stroke="{C["muted"]}" stroke-width="1.6"/>')
    # 量子訊號在三條線上同步往右跑
    for y in wires:
        b.append(f'<circle cx="80" cy="{y}" r="4" fill="{C["cyan"]}"><animate attributeName="cx" values="80;420;420" keyTimes="0;.8;1" dur="5s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;.8;.82" dur="5s" repeatCount="indefinite"/></circle>')
    # 角度表
    fmt = lambda row: ", ".join(f"{a:.2f}" for a in row)
    b.append(f'<text x="26" y="262" {MONO} font-size="11" fill="{C["muted"]}">θ₀ = {fmt(angles[0])}</text>')
    b.append(f'<text x="26" y="280" {MONO} font-size="11" fill="{C["muted"]}">θ₁ = {fmt(angles[1])}</text>')
    b.append(f'<text x="26" y="298" {MONO} font-size="11" fill="{C["muted"]}">θ₂ = {fmt(angles[2])}</text>')
    b.append(f'<text x="26" y="320" {MONO} font-size="11" fill="{C["green"]}">fidelity ⟨ψ|target⟩² = {fid:.4f}</text>')

    # 右側：|ψ⟩ 量測機率直方圖（尾端風險標紅）
    hx, hy, hw, hh = 476, 70, 396, 190
    bar_w = hw / 8
    pmax = max(p) or 1
    b.append(f'<text x="{hx}" y="60" {MONO} font-size="11" fill="{C["muted"]}">P(|i⟩) = |amplitude|²  ·  {len(rets)} daily log-returns</text>')
    b.append(f'<line x1="{hx}" y1="{hy+hh}" x2="{hx+hw}" y2="{hy+hh}" stroke="{C["line"]}" stroke-width="2"/>')
    for i, pi in enumerate(p):
        bh = pi / pmax * (hh - 24)
        x = hx + i * bar_w + 6
        is_tail = edges[i + 1] <= -v95 + 1e-12
        col = C["red"] if is_tail else C["cyan"]
        b.append(f'<rect x="{x:.1f}" y="{hy+hh-bh:.1f}" width="{bar_w-12:.1f}" height="{bh:.1f}" rx="4" fill="{col}" opacity=".85">'
                 f'<animate attributeName="height" values="0;{bh:.1f};{bh:.1f};0" keyTimes="0;.3;.9;1" dur="5s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{hy+hh};{hy+hh-bh:.1f};{hy+hh-bh:.1f};{hy+hh}" keyTimes="0;.3;.9;1" dur="5s" repeatCount="indefinite"/></rect>')
        b.append(f'<text x="{x+(bar_w-12)/2:.1f}" y="{hy+hh+16}" text-anchor="middle" {MONO} font-size="10" fill="{C["muted"]}">|{i:03b}⟩</text>')
        b.append(f'<text x="{x+(bar_w-12)/2:.1f}" y="{hy+hh-bh-6:.1f}" text-anchor="middle" {MONO} font-size="10" fill="{C["text"]}">{pi:.2f}</text>')
    b.append(f'<text x="{hx}" y="{hy+hh+34}" {MONO} font-size="10" fill="{C["muted"]}">{edges[0]*100:+.1f}%</text>')
    b.append(f'<text x="{hx+hw}" y="{hy+hh+34}" text-anchor="end" {MONO} font-size="10" fill="{C["muted"]}">{edges[-1]*100:+.1f}%</text>')
    b.append(f'<text x="{hx}" y="{hy+hh+56}" {MONO} font-size="12" fill="{C["text"]}">BTC ${price:,.0f}  ·  1-day VaR(95%) <tspan fill="{C["red"]}" font-weight="700">{v95*100:.2f}%</tspan></text>')
    b.append(f'<text x="{hx}" y="{hy+hh+74}" {MONO} font-size="11" fill="{C["muted"]}">tail mass in |ψ⟩ = {tail:.3f} → the quantity QAE estimates</text>')
    return window(w, h, "quantum-finance — BTC return distribution loaded into 3 qubits (Grover–Rudolph)", "\n".join(b),
                  f"source {btc.get('source','?')} · " + stamp(["btc"], status))


# ── 3. 鏈上脈動：測試網即時區塊 ─────────────────────────────────────────────
def render_onchain(chains, status):
    w, h = 900, 64 + 56 * len(CHAINS)
    b = []
    for i, ch in enumerate(CHAINS):
        y = 60 + i * 56
        d = chains.get(ch["key"])
        b.append(f'<circle cx="34" cy="{y+12}" r="6" fill="{ch["color"]}"><animate attributeName="opacity" values="1;.3;1" dur="{max(min((d or {}).get("block_time",2),4),0.6):.1f}s" repeatCount="indefinite"/></circle>')
        b.append(f'<text x="50" y="{y+17}" {MONO} font-size="13" font-weight="700" fill="{C["text"]}">{esc(ch["name"])}</text>')
        if not d:
            b.append(f'<text x="250" y="{y+17}" {MONO} font-size="12" fill="{C["muted"]}">rpc unreachable</text>')
            continue
        b.append(f'<text x="230" y="{y+17}" {MONO} font-size="12" fill="{C["cyan"]}">#{d["number"]:,}</text>')
        b.append(f'<text x="360" y="{y+17}" {MONO} font-size="11" fill="{C["muted"]}">{(f"{d['gwei']:.3f}" if d["gwei"] >= 0.001 else "<0.001")} gwei · {d["txs"]} tx · {d["block_time"]:.2f}s/blk</text>')
        # 傳送帶：每個「出塊間隔」往左移一格（間隔夾在 0.6–4 秒內方便觀看）
        step, n = 30, 12
        dur = max(min(d["block_time"], 4), 0.6)
        lane_x = 600
        b.append(f'<clipPath id="lane{i}"><rect x="{lane_x}" y="{y-4}" width="{w-lane_x-20}" height="34"/></clipPath>')
        blocks = "".join(f'<rect x="{lane_x+k*step}" y="{y}" width="22" height="22" rx="5" fill="{ch["color"]}" opacity="{0.25+0.75*k/n:.2f}"/>' for k in range(n + 1))
        b.append(f'<g clip-path="url(#lane{i})"><g>{blocks}<animateTransform attributeName="transform" type="translate" values="0 0;-{step} 0" dur="{dur:.2f}s" repeatCount="indefinite"/></g></g>')
    return window(w, h, "onchain-pulse — testnets I deploy to (live JSON-RPC)", "\n".join(b),
                  stamp([c["key"] for c in CHAINS], status))


# ── 4. 頁首：定位 + 職位 + 經驗證的得獎紀錄（風格對齊 zuemen.net） ─────────
RECOGNITION = [   # (獎項, 對應專案)
    ("FinTech Taipei Awards 2026 — Winner", "ChainLens · Campus Division"),
    ("GLEIF Appreciation Award", "Evidence at Source · vLEI"),
    ("MODA Digital Credential Challenge — Merit", "MedSSI · team PepeLab"),
    ("Chunghwa Telecom Smart Innovation — Finalist", "ChainTrust · grand final 2026"),
    ("NTU–IBM Qiskit Hackathon 2026 — Selected", "quantum machine learning"),
]
ROLES = [
    ("Blockchain Technology Development", "Cathay Financial Holdings"),
    ("Research Assistant, AI+QC Program", "NCCU MIS · QNN on IBM Quantum"),
]


def render_header(chains, btc, status):
    w, h = 1200, 372
    b = []
    # 左欄：小標、名字、一句話定位
    b.append(f'<text x="56" y="70" {MONO} font-size="12" letter-spacing="2.2" fill="{C["label"]}">DIGITAL TRUST · NCCU MIS ’27</text>')
    b.append(f'<text x="54" y="138" {SERIF} font-size="66" fill="{C["text"]}">Zuemen Chu<tspan dx="18" font-size="34" fill="{C["muted"]}">朱廷翊</tspan></text>')
    statement = ["I work on digital trust — making a credential verifiable",
                 "without trusting whoever hands it to you, and making",
                 "the contracts underneath it safe to rely on."]
    for i, line in enumerate(statement):
        b.append(f'<text x="56" y="{184+i*27}" {SANS} font-size="18" fill="{C["text2"]}">{esc(line)}</text>')
    # 職位
    for i, (role, org) in enumerate(ROLES):
        y = 286 + i * 22
        b.append(f'<rect x="56" y="{y-9}" width="6" height="6" fill="{C["cyan"]}"/>')
        b.append(f'<text x="72" y="{y-2}" {MONO} font-size="12.5" fill="{C["text"]}">{esc(role)}<tspan fill="{C["muted"]}">  ·  {esc(org)}</tspan></text>')

    # 分隔線
    b.append(f'<line x1="742" y1="52" x2="742" y2="318" stroke="{C["line"]}"/>')

    # 右欄：得獎紀錄，逐條「驗證」打勾（呼應 verifiable credentials）
    rx, cyc = 772, 9
    b.append(f'<text x="{rx}" y="70" {MONO} font-size="12" letter-spacing="2.2" fill="{C["label"]}">RECOGNITION</text>')
    for i, (award, proj) in enumerate(RECOGNITION):
        y = 108 + i * 44
        t0 = 0.08 + i * 0.1
        k = lambda a: f"{min(max(a, 0), 1):.3f}"
        # 驗證掃描線
        b.append(f'<rect x="{rx}" y="{y+10}" width="0" height="1.5" fill="{C["cyan"]}">'
                 f'<animate attributeName="width" values="0;0;372;372;0" keyTimes="0;{k(t0-.06)};{k(t0)};.92;1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.8;0;0" keyTimes="0;{k(t0-.06)};{k(t0+.05)};1" dur="{cyc}s" repeatCount="indefinite"/></rect>')
        # 打勾
        b.append(f'<g opacity=".18"><animate attributeName="opacity" values=".18;.18;1;1;.18" keyTimes="0;{k(t0-.01)};{k(t0)};.92;1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<rect x="{rx}" y="{y-13}" width="18" height="18" fill="none" stroke="{C["green"]}" stroke-width="1.4"/>'
                 f'<path d="M{rx+4} {y-4}l4 4 7-8" fill="none" stroke="{C["green"]}" stroke-width="1.8" stroke-linecap="square"/></g>')
        b.append(f'<text x="{rx+30}" y="{y+1}" {SANS} font-size="15" fill="{C["text"]}">{esc(award)}</text>')
        b.append(f'<text x="{rx+30}" y="{y+19}" {MONO} font-size="11" fill="{C["muted"]}">{esc(proj)}</text>')

    # 右下：即時狀態列（每次 Actions 更新）
    parts = []
    base = chains.get("base")
    if base:
        parts.append(f"base-sepolia #{base['number']:,}")
    if btc:
        parts.append(f"BTC VaR95 {var95(log_returns(btc['prices']))*100:.2f}%")
    parts.append(f"updated {NOW:%Y-%m-%d %H:%M} UTC+8")
    live = "  ·  ".join(parts)
    b.append(f'<line x1="56" y1="{h-46}" x2="{w-56}" y2="{h-46}" stroke="{C["line"]}"/>')
    b.append(f'<circle cx="60" cy="{h-24}" r="3.5" fill="{C["green"]}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="72" y="{h-20}" {MONO} font-size="11" fill="{C["muted"]}">{esc(live)}</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Zuemen Chu 朱廷翊 — digital trust: verifiable credentials and contracts safe to rely on">
<style>@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect width="{w}" height="{h}" rx="6" fill="{C['bg']}" stroke="{C['line']}"/>
<line x1="56" y1="258" x2="700" y2="258" stroke="{C['line']}"/>
{chr(10).join(b)}
</svg>
"""


# ── 主程式 ─────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    cache = json.load(open(CACHE_PATH)) if os.path.exists(CACHE_PATH) else {}
    fixture = json.load(open(FIXTURE)) if FIXTURE else {}
    status = {}

    contrib = get("contrib", fetch_contrib, cache, status, fixture)
    commits = get("commits", fetch_commits, cache, status, fixture)
    btc = get("btc", fetch_btc, cache, status, fixture)
    chains = {c["key"]: get(c["key"], lambda c=c: fetch_chain(c), cache, status, fixture) for c in CHAINS}

    files = {
        "header.svg": render_header(chains, btc, status),
        "chain-of-commits.svg": render_chain(contrib, commits, status),
        "quantum-finance.svg": render_quantum(btc, status),
        "onchain-pulse.svg": render_onchain(chains, status),
    }
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
    if not FIXTURE:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    print("status:", json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
