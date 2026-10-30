#!/usr/bin/env python3
"""
代表專案動圖產生器 —— 輸出 assets/projects/<slug>.svg

每張圖都依照 zuemen.net/projects 的專案描述，演出「這個系統實際怎麼運作」。
風格對齊 zuemen.net：暖黑底、霧藍強調色、Newsreader 襯線標題、JetBrains Mono 標籤、2px 圓角。
動畫全部用 SVG SMIL（GitHub README 以 <img> 載入時可正常播放，且無限循環）。

用法：python scripts/render_projects.py
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "projects")

# ── 網站色票（與 src/app/globals.css 相同） ─────────────────────────────────
P = {"bg": "#0a0a0b", "panel": "#111114", "panel2": "#17171c", "line": "#222228", "rule": "#34343b",
     "text": "#ecebe6", "text2": "#a6a59f", "muted": "#8a8a93", "label": "#8f8e88",
     "accent": "#9bb6d8", "soft": "#141b24", "pass": "#8cc9a1", "refuse": "#f0907a", "warn": "#e3c07a"}
MONO = 'font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"'
SANS = 'font-family="IBM Plex Sans,-apple-system,BlinkMacSystemFont,Segoe UI,Microsoft JhengHei,sans-serif"'
SERIF = 'font-family="Newsreader,Georgia,Times New Roman,serif"'
W, H = 600, 340


# ── 動畫小工具 ─────────────────────────────────────────────────────────────
def _norm(pts):
    """時間點排序、補上 0 與 1，並強制嚴格遞增（SMIL keyTimes 的規定）"""
    pts = sorted(pts, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts = [(0.0, pts[0][1])] + pts
    out, last = [], -1.0
    for t, v in pts:
        t = min(max(t, last + 0.001), 0.999)
        out.append((t, v))
        last = t
    out.append((1.0, out[-1][1]))
    return out


def tl(attr, pts, dur):
    """通用時間軸：pts = [(0~1 的時間點, 值), ...]"""
    o = _norm(pts)
    return (f'<animate attributeName="{attr}" values="{";".join(str(v) for _, v in o)}" '
            f'keyTimes="{";".join(f"{t:.3f}" for t, _ in o)}" dur="{dur}s" repeatCount="indefinite"/>')


def tlt(pts, dur, kind="translate"):
    """位移 / 旋轉的時間軸"""
    o = _norm(pts)
    return (f'<animateTransform attributeName="transform" type="{kind}" values="{";".join(str(v) for _, v in o)}" '
            f'keyTimes="{";".join(f"{t:.3f}" for t, _ in o)}" dur="{dur}s" repeatCount="indefinite"/>')


def vis(t0, t1, dur, f=0.015):
    """在 t0~t1 之間顯示（淡入淡出），元素本身要設 opacity="0" """
    return tl("opacity", [(t0 - f, 0), (t0, 1), (t1, 1), (t1 + f, 0)], dur)


def move(path, t0, t1, dur):
    """沿路徑在 t0~t1 移動"""
    return (f'<animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" '
            f'keyTimes="0;{t0:.3f};{t1:.3f};1" path="{path}"/>')


# ── 繪圖小工具 ─────────────────────────────────────────────────────────────
def t(x, y, s, size=11, color=None, font=MONO, anchor="start", weight="400", extra=""):
    return (f'<text x="{x}" y="{y}" {font} font-size="{size}" fill="{color or P["text"]}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{extra}>{s}</text>')


def box(x, y, w, h, stroke=None, fill=None, rx=2, extra="", inner=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill or P["panel"]}" '
            f'stroke="{stroke or P["line"]}" stroke-width="1.2"{extra}>{inner}</rect>')


def chip(cx, cy, s, color, fill=None):
    """以中心點畫一個小標籤"""
    w = len(s) * 6.4 + 16
    return (box(cx - w / 2, cy - 10, w, 20, color, fill or P["bg"]) +
            t(cx, cy + 4, s, 10.5, color, anchor="middle"))


def tick(x, y, color=None):
    c = color or P["pass"]
    return f'<path d="M{x} {y}l4 4 8-9" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="square"/>'


def cross(x, y, color=None):
    c = color or P["refuse"]
    return f'<path d="M{x} {y-4}l8 8M{x+8} {y-4}l-8 8" stroke="{c}" stroke-width="1.8"/>'


def frame(label, title, tag, caption, body):
    """統一外框：上方獎項小標 + 襯線標題，下方一句機制說明"""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title} — {caption}">
<rect width="{W}" height="{H}" rx="6" fill="{P['bg']}" stroke="{P['line']}"/>
{t(24, 30, label, 10, P['label'], extra=' letter-spacing="1.6"')}
{t(W-24, 30, tag, 10, P['muted'], anchor="end")}
{t(23, 60, title, 24, P['text'], SERIF)}
<line x1="24" y1="74" x2="{W-24}" y2="74" stroke="{P['line']}"/>
<line x1="24" y1="306" x2="{W-24}" y2="306" stroke="{P['line']}"/>
{t(24, 326, caption, 10.5, P['muted'])}
{body}
</svg>
'''


# ── 1. ChainLens ───────────────────────────────────────────────────────────
def chainlens():
    D = 9
    S = [(52, 112), (52, 176), (52, 240)]
    Hb = (150, 176)
    F = [(250, 112), (250, 176), (250, 240)]
    Dst = (344, 176)
    b = []
    edges = []   # (路徑, 正向流動時間, 回溯高亮時間)
    for i, s in enumerate(S):
        edges.append((f"M{s[0]} {s[1]}L{Hb[0]} {Hb[1]}", 0.02 + i * 0.02, 0.40))
    for i, f in enumerate(F):
        edges.append((f"M{Hb[0]} {Hb[1]}L{f[0]} {f[1]}", 0.12, 0.35))
    for i, f in enumerate(F):
        edges.append((f"M{f[0]} {f[1]}L{Dst[0]} {Dst[1]}", 0.20, 0.30))
    for path, _, back in edges:
        b.append(f'<path d="{path}" stroke="{P["line"]}" stroke-width="1.6" fill="none">'
                 + tl("stroke", [(back - .01, P["line"]), (back, P["accent"]), (.9, P["accent"]), (.92, P["line"])], D) + '</path>')
    # 資金點正向流動
    for path, t0, _ in edges:
        b.append(f'<circle r="3.5" fill="{P["text2"]}" opacity="0">{move(path, t0, t0 + .08, D)}{vis(t0, t0 + .08, D, .005)}</circle>')
    # 節點
    for x, y in S + F:
        b.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{P["panel"]}" stroke="{P["rule"]}" stroke-width="1.4"/>')
    b.append(f'<circle cx="{Hb[0]}" cy="{Hb[1]}" r="12" fill="{P["panel"]}" stroke="{P["warn"]}" stroke-width="1.6"/>')
    b.append(t(Hb[0], 208, "fan-in", 10, P["warn"], anchor="middle"))
    b.append(t(F[2][0], 268, "fan-out", 10, P["warn"], anchor="middle"))
    b.append(t(S[2][0], 268, "sources", 10, P["muted"], anchor="middle"))
    # GraphSAGE 鄰域擴散圈
    for k in range(2):
        t0 = .46 + k * .07
        b.append(f'<circle cx="{Dst[0]}" cy="{Dst[1]}" r="14" fill="none" stroke="{P["accent"]}" stroke-width="1.2" opacity="0">'
                 + tl("r", [(t0, 14), (t0 + .12, 64)], D) + tl("opacity", [(t0 - .005, 0), (t0, .9), (t0 + .12, 0)], D) + '</circle>')
    b.append(f'<rect x="{Dst[0]-13}" y="{Dst[1]-13}" width="26" height="26" rx="2" fill="{P["panel"]}" stroke="{P["text2"]}" stroke-width="1.6">'
             + tl("stroke", [(.6, P["text2"]), (.62, P["warn"]), (.9, P["warn"]), (.92, P["text2"])], D) + '</rect>')
    b.append(t(Dst[0], 208, "withdrawal", 10, P["muted"], anchor="middle"))
    # 右側審查面板
    x0 = 404
    b.append(box(x0, 88, 172, 206))
    b.append(t(x0 + 12, 106, "WITHDRAWAL #4821", 10, P["label"], extra=' letter-spacing="1"'))
    b.append(t(x0 + 12, 132, "rule engine", 11, P["text2"]))
    b.append(f'<g opacity="0">{vis(.42, .92, D)}{t(x0+160, 132, "pattern hit", 10, P["warn"], anchor="end")}</g>')
    b.append(t(x0 + 12, 156, "GraphSAGE", 11, P["text2"]))
    b.append(f'<g opacity="0">{vis(.56, .92, D)}{t(x0+160, 156, "0.87", 11, P["warn"], anchor="end", weight="700")}</g>')
    b.append(f'<line x1="{x0+12}" y1="170" x2="{x0+160}" y2="170" stroke="{P["line"]}"/>')
    b.append(f'<g>{tl("opacity", [(.6, 1), (.61, 0), (.92, 0), (.93, 1)], D)}{t(x0+12, 194, "release", 13, P["muted"])}</g>')
    b.append(f'<g opacity="0">{vis(.61, .92, D)}{t(x0+12, 194, "→ enhanced review", 13, P["warn"], weight="700")}'
             f'{t(x0+12, 212, "may escalate, never hold", 9.5, P["muted"])}</g>')
    b.append(f'<g opacity="0">{vis(.7, .92, D)}{chip(x0+86, 238, "evidence chain", P["pass"])}</g>')
    b.append(f'<g opacity="0">{vis(.76, .92, D)}{chip(x0+86, 266, "STR draft → analyst", P["accent"])}</g>')
    return frame("FINTECH TAIPEI AWARDS 2026 — WINNER", "ChainLens", "SNA · GNN · AML",
                 "rule engine traces the path upstream · GNN may only escalate · a person decides", "\n".join(b))


# ── 2. Evidence at Source ──────────────────────────────────────────────────
def evidence():
    D = 10
    b = []
    # 移工錢包
    b.append(box(28, 88, 178, 206))
    b.append(t(40, 106, "WORKER-HELD WALLET", 10, P["label"], extra=' letter-spacing="1"'))
    b.append(box(40, 118, 154, 96, P["rule"], P["panel2"]))
    for i, s in enumerate(["employment start", "wages on time", "housing provided"]):
        b.append(t(50, 140 + i * 22, s, 10.5, P["text2"]))
        b.append(f'<rect x="164" y="{132+i*22}" width="22" height="9" fill="{P["rule"]}"/>')
    b.append(f'<g opacity="0">{vis(.04, .95, D)}{chip(88, 232, "sig · employer", P["pass"])}</g>')
    b.append(f'<g opacity="0">{vis(.1, .95, D)}{chip(82, 258, "sig · worker", P["pass"])}</g>')
    b.append(t(40, 286, "signed when it happens", 9.5, P["muted"]))
    # 三層政策閘門
    gx = 236
    b.append(t(gx + 32, 106, "POLICY GATE", 10, P["label"], anchor="middle", extra=' letter-spacing="1"'))
    for i, s in enumerate(["consent", "purpose", "minimise"]):
        y = 128 + i * 50
        b.append(f'<rect x="{gx}" y="{y}" width="64" height="34" rx="2" fill="{P["panel"]}" stroke="{P["line"]}" stroke-width="1.2">'
                 + tl("stroke", [(.3 + i * .03, P["line"]), (.31 + i * .03, P["accent"]), (.62, P["accent"]), (.63, P["line"]),
                                 (.74, P["line"]), (.75, P["refuse"]), (.84, P["refuse"]), (.85, P["line"])], D) + '</rect>')
        b.append(t(gx + 32, y + 21, f"L{i+1} {s}", 9.5, P["text2"], anchor="middle"))
    # 銀行代理 + vLEI 鏈
    ax = 330
    b.append(box(ax, 88, 246, 206))
    b.append(t(ax + 12, 106, "BANK'S AI AGENT", 10, P["label"], extra=' letter-spacing="1"'))
    for i, s in enumerate(["GLEIF", "bank (LE)", "agent"]):
        cx = ax + 40 + i * 82
        b.append(f'<circle cx="{cx}" cy="140" r="6" fill="{P["panel"]}" stroke="{P["accent"]}" stroke-width="1.4">'
                 + tl("fill", [(.18 + i * .03, P["panel"]), (.19 + i * .03, P["accent"]), (.25 + i * .03, P["panel"])], D) + '</circle>')
        b.append(t(cx, 160, s, 10, P["text2"], anchor="middle"))
        if i < 2:
            b.append(f'<line x1="{cx+8}" y1="140" x2="{cx+74}" y2="140" stroke="{P["rule"]}" stroke-dasharray="3 3"/>')
    b.append(t(ax + 12, 182, "vLEI chain re-verified on every query", 9.5, P["muted"]))
    b.append(t(ax + 12, 212, "asks:", 10.5, P["muted"]))
    b.append(t(ax + 50, 212, "“were wages paid on time?”", 10.5, P["text"]))
    b.append(t(ax + 12, 236, "gets:", 10.5, P["muted"]))
    b.append(f'<g opacity="0">{vis(.6, .95, D)}{t(ax+50, 236, "true · reason R-01", 10.5, P["pass"], weight="700")}</g>')
    b.append(f'<g opacity="0">{vis(.88, .99, D)}{t(ax+12, 272, "→ a named human reviewer decides", 9.5, P["accent"])}</g>')
    # 查詢與回覆在兩邊之間移動
    b.append(f'<g opacity="0">{move("M370 212L268 180L150 180", .26, .42, D)}{vis(.26, .42, D, .005)}{chip(0, 0, "query", P["accent"], P["soft"])}</g>')
    b.append(f'<g opacity="0">{move("M150 180L268 180L370 236", .46, .6, D)}{vis(.46, .6, D, .005)}{chip(0, 0, "true · R-01", P["pass"])}</g>')
    # 原始資料想離開 → 被擋下
    b.append(f'<g opacity="0">{move("M150 160L236 160L222 160", .66, .78, D)}{vis(.66, .84, D)}{chip(0, 0, "full record", P["refuse"])}</g>')
    b.append(f'<g opacity="0">{vis(.76, .86, D)}{t(268, 290, "record never leaves", 9.5, P["refuse"], anchor="middle")}</g>')
    return frame("GLEIF APPRECIATION AWARD", "Evidence at Source", "vLEI · VC · AI agents",
                 "agents get a boolean and a reason code — never the record · humans decide", "\n".join(b))


# ── 3. MedSSI ──────────────────────────────────────────────────────────────
def medssi():
    D = 12
    fields = ["patient name", "national ID", "medication", "dosage", "diagnosis", "lab results"]
    # 每個情境允許的欄位（FHIR path 選擇性揭露）
    scen = [("pharmacy", [0, 2, 3], .16, .42), ("researcher", [4, 5], .45, .69), ("insurer", [0, 1, 4], .72, .95)]
    b = []
    # 醫院發證
    b.append(box(28, 120, 96, 66))
    b.append(f'<g fill="{P["accent"]}"><rect x="69" y="134" width="14" height="36"/><rect x="58" y="145" width="36" height="14"/></g>')
    b.append(t(76, 204, "hospital", 10.5, P["text2"], anchor="middle"))
    b.append(t(76, 218, "issues once", 9.5, P["muted"], anchor="middle"))
    b.append(f'<g opacity="0">{move("M124 152L170 152", .02, .1, D)}{vis(.02, .12, D, .005)}{chip(0, 0, "VC", P["accent"], P["soft"])}</g>')
    # 政府數位皮夾
    wx = 164
    b.append(box(wx, 86, 160, 210, P["rule"], P["panel"], rx=10))
    b.append(t(wx + 80, 106, "TW DIGITAL WALLET", 9.5, P["label"], anchor="middle", extra=' letter-spacing="1"'))
    for i, f in enumerate(fields):
        y = 118 + i * 28
        on = []
        for _, idx, a, z in scen:
            if i in idx:
                on += [(a, 1), (z, 1)]
        pts_stroke, pts_op = [(0, P["line"])], [(0, 1), (.14, 1), (.15, .35)]
        for name, idx, a, z in scen:
            if i in idx:
                pts_stroke += [(a - .005, P["line"]), (a, P["pass"]), (z, P["pass"]), (z + .005, P["line"])]
                pts_op += [(a - .005, .35), (a, 1), (z, 1), (z + .005, .35)]
        pts_op += [(.96, .35), (.97, 1)]
        b.append(f'<g>{tl("opacity", pts_op, D)}<rect x="{wx+12}" y="{y}" width="136" height="22" rx="2" fill="{P["bg"]}" stroke="{P["line"]}" stroke-width="1.2">'
                 f'{tl("stroke", pts_stroke, D)}</rect>{t(wx+20, y+15, f, 10.5, P["text2"])}</g>')
    # 驗證方
    vx = 360
    for k, (name, idx, a, z) in enumerate(scen):
        y = 92 + k * 70
        b.append(f'<rect x="{vx}" y="{y}" width="216" height="56" rx="2" fill="{P["panel"]}" stroke="{P["line"]}" stroke-width="1.2">'
                 + tl("stroke", [(a - .005, P["line"]), (a, P["accent"]), (z, P["accent"]), (z + .005, P["line"])], D) + '</rect>')
        b.append(t(vx + 12, y + 20, name, 12, P["text"], SANS))
        b.append(t(vx + 12, y + 40, " · ".join(fields[i].split()[0] for i in idx), 10, P["pass"]))
        b.append(f'<g opacity="0">{vis(a, z, D)}{t(vx+204, y+20, "LoA ≥ substantial ✓", 9.5, P["pass"], anchor="end")}</g>')
        b.append(f'<path d="M{wx+160} {191} C {wx+190} {191}, {vx-30} {y+28}, {vx} {y+28}" fill="none" stroke="{P["accent"]}" stroke-dasharray="4 4" opacity="0">{vis(a, z, D)}</path>')
    # 藥局多要一個欄位 → 被拒
    b.append(f'<g opacity="0">{vis(.34, .42, D)}{chip(468, 160, "diagnosis ✗ outside scenario", P["refuse"])}</g>')
    return frame("MODA DIGITAL CREDENTIAL CHALLENGE 2025 — MERIT", "MedSSI", "SSI · VC/DID · FHIR",
                 "one credential, held by the patient · each verifier sees only its scenario's fields", "\n".join(b))


# ── 4. ChainTrust ──────────────────────────────────────────────────────────
def chaintrust():
    D = 11
    b = []
    # 上半：一次 KYC，到處重用（SD-JWT 最小揭露）
    b.append(box(28, 92, 112, 52))
    b.append(t(84, 114, "Bank A", 12, P["text"], SANS, anchor="middle"))
    b.append(t(84, 132, "KYC once", 10, P["muted"], anchor="middle"))
    b.append(box(214, 88, 150, 64, P["accent"], P["soft"]))
    b.append(t(289, 110, "SSI wallet", 12, P["text"], SANS, anchor="middle"))
    b.append(t(289, 128, "SD-JWT credential", 10, P["accent"], anchor="middle"))
    b.append(t(289, 142, "id_no · name · age · KYC lvl", 8.5, P["muted"], anchor="middle"))
    b.append(f'<g opacity="0">{move("M140 118L214 118", .03, .1, D)}{vis(.03, .11, D, .005)}{chip(0, 0, "issue", P["accent"], P["soft"])}</g>')
    for k, (name, y, a) in enumerate([("Bank B", 92, .14), ("Securities C", 128, .28)]):
        b.append(box(430, y, 146, 30))
        b.append(t(442, y + 20, name, 11, P["text"], SANS))
        b.append(f'<g opacity="0">{vis(a+.08, .48, D)}{tick(556, y+14)}</g>')
        b.append(f'<g opacity="0">{move(f"M364 {y+15}L430 {y+15}", a, a + .08, D)}{vis(a, a + .08, D, .005)}{chip(0, 0, "age≥20 · KYC 2", P["pass"])}</g>')
    b.append(f'<g opacity="0">{vis(.14, .48, D)}{t(397, 178, "id_no never disclosed", 9.5, P["muted"], anchor="middle")}</g>')
    b.append(f'<line x1="24" y1="194" x2="{W-24}" y2="194" stroke="{P["line"]}" stroke-dasharray="2 4"/>')
    # 下半：AI 防詐即時攔截
    b.append(t(28, 216, "AI ANTI-FRAUD", 10, P["label"], extra=' letter-spacing="1"'))
    b.append(f'<g opacity="0">{vis(.5, .96, D)}{t(28, 238, "transfer  NT$280,000 → new payee, 02:14", 11, P["text"])}</g>')
    mx, mw = 28, 380
    b.append(box(mx, 252, mw, 14, P["line"], P["panel"]))
    b.append(f'<rect x="{mx}" y="252" width="0" height="14" rx="2" fill="{P["warn"]}">'
             + tl("width", [(.54, 0), (.72, mw * .91), (.95, mw * .91), (.96, 0)], D)
             + tl("fill", [(.64, P["warn"]), (.66, P["refuse"])], D) + '</rect>')
    b.append(f'<line x1="{mx+mw*.7}" y1="246" x2="{mx+mw*.7}" y2="272" stroke="{P["text2"]}" stroke-dasharray="2 2"/>')
    b.append(t(mx + mw * .7, 284, "threshold 0.70", 9, P["muted"], anchor="middle"))
    b.append(f'<g opacity="0">{vis(.72, .95, D)}{t(mx+mw+10, 264, "0.91", 13, P["refuse"], weight="700")}</g>')
    b.append(f'<g opacity="0">{vis(.76, .95, D)}{box(466, 218, 110, 50, P["refuse"], P["bg"])}'
             f'{t(521, 238, "INTERCEPTED", 11, P["refuse"], anchor="middle", weight="700")}{t(521, 256, "call-back verify", 9.5, P["muted"], anchor="middle")}</g>')
    return frame("CHUNGHWA TELECOM SMART INNOVATION 2026 — FINALIST", "ChainTrust", "SSI · SD-JWT · AI",
                 "one KYC reused across institutions · high-risk transfers stopped in real time", "\n".join(b))


# ── 5. Agent Passport ──────────────────────────────────────────────────────
def agent_passport():
    D = 11
    b = []
    # Merkle 樹：授權書欄位，只揭露交易需要的兩片葉子
    root, mids = (128, 106), [(80, 160), (176, 160)]
    leaves = [(56, 214, "max/day", True), (104, 214, "assets", False), (152, 214, "payee", True), (200, 214, "expiry", False)]
    links = [(root, mids[0]), (root, mids[1]), (mids[0], leaves[0][:2]), (mids[0], leaves[1][:2]),
             (mids[1], leaves[2][:2]), (mids[1], leaves[3][:2])]
    for (a, c) in links:
        hot = c in [leaves[0][:2], leaves[2][:2], mids[0], mids[1]]
        anim = tl("stroke", [(.12, P["line"]), (.16, P["accent"]), (.66, P["accent"]), (.67, P["line"])], D) if hot else ""
        b.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{c[0]}" y2="{c[1]}" stroke="{P["line"]}" stroke-width="1.6">{anim}</line>')
    b.append(f'<rect x="{root[0]-34}" y="{root[1]-12}" width="68" height="24" rx="2" fill="{P["panel"]}" stroke="{P["accent"]}" stroke-width="1.4">'
             + tl("stroke", [(.7, P["accent"]), (.71, P["refuse"]), (.96, P["refuse"]), (.97, P["accent"])], D) + '</rect>')
    b.append(t(root[0], root[1] + 4, "root", 10.5, P["text"], anchor="middle"))
    b.append(f'<g opacity="0">{vis(.71, .96, D)}{t(root[0], 86, "mandate revoked", 9.5, P["refuse"], anchor="middle")}</g>')
    for m in mids:
        b.append(f'<circle cx="{m[0]}" cy="{m[1]}" r="6" fill="{P["panel"]}" stroke="{P["rule"]}" stroke-width="1.4"/>')
    for x, y, name, shown in leaves:
        col = P["pass"] if shown else P["rule"]
        b.append(box(x - 22, y - 10, 44, 20, col, P["bg"]))
        b.append(t(x, y + 4, name if shown else "•••", 9, col if shown else P["muted"], anchor="middle"))
    b.append(t(128, 250, "owner signs once ·", 9.5, P["muted"], anchor="middle"))
    b.append(t(128, 264, "agent reveals 2 of 4 fields", 9.5, P["muted"], anchor="middle"))
    b.append(t(128, 286, "ERC-8004 identity", 10, P["accent"], anchor="middle"))
    # PassportGate：同一筆交易內逐項檢查
    gx = 262
    b.append(box(gx, 88, 314, 206))
    b.append(t(gx + 14, 108, "PassportGate.pay()  ·  same transaction", 10, P["label"]))
    checks = ["ERC-8004 identity", "mandate status", "Merkle proofs", "agent signature", "daily limit"]
    for i, c in enumerate(checks):
        y = 134 + i * 24
        b.append(t(gx + 40, y + 4, c, 11, P["text2"]))
        b.append(box(gx + 14, y - 8, 16, 16, P["line"], P["bg"]))
        a = .22 + i * .06
        if i == 1:
            b.append(f'<g opacity="0">{vis(a, .67, D)}{tick(gx+16, y)}</g>')
            b.append(f'<g opacity="0">{vis(.8, .96, D)}{cross(gx+18, y)}</g>')
        else:
            b.append(f'<g opacity="0">{vis(a, .67, D)}{tick(gx+16, y)}</g>')
    b.append(f'<line x1="{gx+14}" y1="258" x2="{gx+300}" y2="258" stroke="{P["line"]}"/>')
    b.append(f'<g opacity="0">{vis(.54, .67, D)}{t(gx+14, 280, "paid 5 USDC → counterparty", 12, P["pass"], weight="700")}</g>')
    b.append(f'<g opacity="0">{vis(.82, .96, D)}{t(gx+14, 280, "refused on-chain · revoked mandate", 12, P["refuse"], weight="700")}</g>')
    return frame("MONAD METROPOLIS 2026 — TRACK 04", "Agent Passport", "ERC-8004 · vLEI · MCP",
                 "who authorised it, what it allows, is it still valid — checked before paying", "\n".join(b))


# ── 6. Mandate Layer ───────────────────────────────────────────────────────
def mandate_layer():
    D = 12
    b = []
    # 授權書
    b.append(box(28, 88, 196, 206))
    b.append(t(40, 106, "MANDATE · EIP-712", 10, P["label"], extra=' letter-spacing="1"'))
    rows = [("per-order margin", "≤ $150"), ("total budget", "$400"), ("leverage cap", "5x"),
            ("assets", "BTC ETH XAU"), ("expiry", "7 days")]
    for i, (k, v) in enumerate(rows):
        b.append(t(40, 132 + i * 22, k, 10.5, P["muted"]))
        b.append(t(212, 132 + i * 22, v, 10.5, P["text"], anchor="end"))
    b.append(t(40, 256, "budget used", 10, P["muted"]))
    b.append(box(40, 264, 172, 10, P["line"], P["bg"]))
    b.append(f'<rect x="40" y="264" width="0" height="10" fill="{P["accent"]}">'
             + tl("width", [(.17, 0), (.2, 172 * 100 / 400), (.77, 172 * 100 / 400), (.8, 172 * 250 / 400), (.95, 172 * 250 / 400), (.96, 0)], D) + '</rect>')
    b.append(f'<g opacity="0">{tl("opacity", [(.17, 0), (.2, 1), (.79, 1), (.8, 0)], D)}{t(212, 256, "$100", 10, P["accent"], anchor="end")}</g>')
    b.append(f'<g opacity="0">{vis(.8, .95, D)}{t(212, 256, "$250", 10, P["accent"], anchor="end")}</g>')
    b.append(t(40, 290, "signed by wallet or ERC-1271", 9, P["muted"]))
    # 合約
    cx, cy = 300, 190
    b.append(box(cx - 52, cy - 34, 104, 68, P["accent"], P["soft"]))
    b.append(t(cx, cy - 8, "AgentSession", 10.5, P["text"], anchor="middle"))
    b.append(t(cx, cy + 8, "Manager", 10.5, P["text"], anchor="middle"))
    b.append(t(cx, cy + 24, "on Base", 9, P["muted"], anchor="middle"))
    # 訂單依序送進合約
    orders = [("BTC 3x $100", True, "opened", .04), ("TSLA 2x $50", False, "asset not in mandate", .24),
              ("ETH 8x $80", False, "leverage > 5x", .44), ("XAU 2x $150", True, "opened", .64)]
    b.append(t(500, 106, "AGENT ORDERS", 10, P["label"], anchor="middle", extra=' letter-spacing="1"'))
    for i, (o, ok, why, a) in enumerate(orders):
        col = P["pass"] if ok else P["refuse"]
        b.append(f'<g opacity="0">{move(f"M500 130L{cx} {cy}", a, a + .12, D)}{vis(a, a + .13, D, .005)}{chip(0, 0, o, P["text2"], P["panel2"])}</g>')
        b.append(f'<rect x="{cx-52}" y="{cy-34}" width="104" height="68" rx="2" fill="none" stroke="{col}" stroke-width="2" opacity="0">{vis(a+.12, a+.16, D)}</rect>')
        y = 176 + i * 28
        mark = tick(392, y - 5, col) if ok else cross(392, y - 1, col)
        b.append(f'<g opacity="0">{vis(a+.13, .95, D)}{mark}{t(412, y, o, 10.5, P["text"])}{t(412, y+13, why, 9, col)}</g>')
    return frame("COLOSSEUM CRYPTO WORLD'S FAIR 2026 — BASE TRACK", "Mandate Layer", "Solidity · EIP-712 · x402",
                 "the user sets the mandate · the contract checks it on every single order", "\n".join(b))


# ── 7. PepeFi On-Chain CFD ─────────────────────────────────────────────────
def pepefi():
    D = 12
    b = []
    # keeper → 受保護的 oracle
    b.append(box(28, 88, 120, 72))
    b.append(t(40, 106, "KEEPER", 10, P["label"], extra=' letter-spacing="1"'))
    b.append(t(40, 126, "GitHub Actions", 10.5, P["text2"]))
    b.append(t(40, 146, "→ guarded oracle", 10.5, P["accent"]))
    for k in range(3):
        a = .05 + k * .3
        b.append(f'<circle r="3.5" fill="{P["accent"]}" opacity="0">{move("M148 124L172 124", a, a + .04, D)}{vis(a, a + .04, D, .005)}</circle>')
    # 三個市場（合成部位，不發行實體資產）
    mk = [("AAPL", "US equity", "M0 26L14 22L28 24L42 14L56 16L70 8"), ("XAU", "gold", "M0 18L14 20L28 14L42 16L56 10L70 12"),
          ("BTC", "crypto", "M0 24L14 10L28 18L42 6L56 14L70 4")]
    for i, (sym, kind, d) in enumerate(mk):
        x = 176 + i * 136
        b.append(f'<rect x="{x}" y="88" width="124" height="72" rx="2" fill="{P["panel"]}" stroke="{P["line"]}" stroke-width="1.2"/>')
        b.append(t(x + 12, 106, sym, 12, P["text"], weight="700") + t(x + 112, 106, kind, 9.5, P["muted"], anchor="end"))
        b.append(f'<path d="{d}" transform="translate({x+12} 112) scale(1.43 1)" fill="none" stroke="{P["accent"]}" stroke-width="1.4" stroke-dasharray="90" stroke-dashoffset="90">'
                 + tl("stroke-dashoffset", [(.05 + i * .02, 90), (.3, 0), (.95, 0), (.96, 90)], D) + '</path>')
        if sym == "AAPL":
            b.append(f'<g>{tl("opacity", [(.44,1),(.45,0),(.95,0),(.96,1)], D)}{t(x+12, 150, "market open", 9.5, P["pass"])}</g>')
            b.append(f'<g opacity="0">{vis(.45, .95, D)}{t(x+12, 150, "reduce-only", 9.5, P["warn"])}</g>')
        else:
            b.append(t(x + 12, 150, "24/7", 9.5, P["pass"]))
    # 下半：投資人憑證門檻 + 代理 session
    b.append(t(28, 190, "investor wallet", 11, P["text"], SANS))
    b.append(chip(206, 186, "qualified-investor VC", P["accent"], P["soft"]))
    b.append(t(28, 222, "agent session", 11, P["text"], SANS))
    b.append(chip(200, 218, "owner-bounded on-chain", P["accent"], P["soft"]))
    log = [(.14, "investor  open AAPL long 2x", True, "credential verified on-chain"),
           (.54, "agent     open AAPL long", False, "refused: market closed, reduce-only"),
           (.68, "agent     close AAPL", True, "allowed: reduce-only"),
           (.82, "agent     buy signal  0.01 USDC", True, "paid over x402")]
    for i, (a, s, ok, why) in enumerate(log):
        y = 180 + i * 28
        col = P["pass"] if ok else P["refuse"]
        mark = tick(316, y - 5, col) if ok else cross(318, y - 1, col)
        b.append(f'<g opacity="0">{vis(a, .95, D)}{mark}{t(336, y, s, 10, P["text"])}{t(336, y+12, why, 9, col)}</g>')
    b.append(t(28, 286, "testnet · mock USDC · synthetic exposure", 9.5, P["muted"]))
    return frame("NCCU CAPSTONE 2026 — BASE SEPOLIA", "PepeFi On-Chain CFD", "Solidity · Foundry · RWA",
                 "RWA-referenced perps · credential-gated · reduce-only when the market is closed", "\n".join(b))


# ── 8. RWA Real Estate Tokenization ────────────────────────────────────────
def rwa():
    D = 12
    b = []
    holders = [("A", P["accent"]), ("B", P["pass"]), ("C", P["warn"])]
    owner = [0] * 6 + [1] * 4 + [2] * 2          # 12 單位：A 6、B 4、C 2
    # 建築：每扇窗 = 一個代幣單位，顏色 = 持有人
    b.append(f'<path d="M32 118L92 88L152 118Z" fill="{P["panel2"]}" stroke="{P["rule"]}" stroke-width="1.2"/>')
    b.append(box(36, 118, 112, 176, P["rule"], P["panel"]))
    for i, o in enumerate(owner):
        x, y = 48 + (i % 3) * 32, 132 + (i // 3) * 38
        col = holders[o][1]
        anim = tl("fill", [(.26, col), (.27, P["warn"]), (.95, P["warn"]), (.96, col)], D) if i == 5 else ""
        b.append(f'<rect x="{x}" y="{y}" width="24" height="26" rx="1" fill="{col}" opacity=".75">{anim}</rect>')
    b.append(t(92, 302 - 4, "PropertyToken · 12 units", 9.5, P["muted"], anchor="middle"))
    # 合約：身分登記 + 租金分配
    b.append(box(176, 88, 150, 96, P["accent"], P["soft"]))
    b.append(t(188, 106, "IdentityRegistry", 10.5, P["text"]))
    b.append(t(188, 122, "on-chain KYC allowlist", 9, P["muted"]))
    for i, (h, ok) in enumerate([("A", 1), ("B", 1), ("C", 1), ("D", 0)]):
        x = 196 + i * 32
        b.append(t(x, 154, h, 12, P["text"], anchor="middle", weight="700"))
        b.append(tick(x - 6, 168) if ok else cross(x - 4, 172))
    b.append(box(176, 200, 150, 94, P["accent"], P["soft"]))
    b.append(t(188, 218, "RentalDistributor", 10.5, P["text"]))
    b.append(t(188, 234, "pro-rata, holders claim", 9, P["muted"]))
    b.append(f'<g opacity="0">{vis(.55, .95, D)}{t(188, 262, "rent in: 1,200 USDC", 10.5, P["accent"])}</g>')
    # 持有人
    rows = [("A", P["accent"], "6", "5", "500"), ("B", P["pass"], "4", "4", "400"), ("C", P["warn"], "2", "3", "300"), ("D", P["muted"], "0", "0", "—")]
    b.append(t(352, 106, "HOLDER", 10, P["label"], extra=' letter-spacing="1"'))
    b.append(t(470, 106, "UNITS", 10, P["label"], anchor="end", extra=' letter-spacing="1"'))
    b.append(t(576, 106, "CLAIM", 10, P["label"], anchor="end", extra=' letter-spacing="1"'))
    for i, (h, col, u0, u1, claim) in enumerate(rows):
        y = 134 + i * 34
        b.append(f'<rect x="352" y="{y-11}" width="10" height="14" fill="{col}" opacity=".8"/>')
        b.append(t(372, y, f"holder {h}", 11, P["text2"]))
        if u0 != u1:
            b.append(f'<g>{tl("opacity", [(.26,1),(.27,0),(.95,0),(.96,1)], D)}{t(470, y, u0, 11, P["text"], anchor="end")}</g>')
            b.append(f'<g opacity="0">{vis(.27, .95, D)}{t(470, y, u1, 11, P["text"], anchor="end", weight="700")}</g>')
        else:
            b.append(t(470, y, u0, 11, P["text"], anchor="end"))
        b.append(f'<g opacity="0">{vis(.7 + i * .03, .95, D)}{t(576, y, claim, 11, col if h != "D" else P["muted"], anchor="end")}</g>')
    # 轉讓動畫：A→C 成功；A→D 被代幣合約自己拒絕
    b.append(f'<g opacity="0">{move("M372 134L252 150L372 202", .08, .26, D)}{vis(.08, .26, D, .005)}{chip(0, 0, "1 unit", P["text2"], P["panel2"])}</g>')
    b.append(f'<g opacity="0">{move("M372 134L292 160", .32, .42, D)}{vis(.32, .5, D)}{chip(0, 0, "1 unit → D", P["refuse"])}</g>')
    b.append(f'<g opacity="0">{vis(.42, .52, D)}{t(470, 290, "rejected by the token contract", 9.5, P["refuse"], anchor="middle")}</g>')
    # 租金依比例流向持有人
    for i, y in enumerate([134, 168, 202]):
        a = .6 + i * .02
        b.append(f'<circle r="3.5" fill="{rows[i][1]}" opacity="0">{move(f"M326 262L{560} {y-4}", a, a + .1, D)}{vis(a, a + .1, D, .005)}</circle>')
    return frame("BLOCKCHAIN IMPLEMENTATION", "RWA Real Estate Tokenization", "Solidity · Hardhat · ERC-3643-style",
                 "identity is enforced inside the token · rent split pro rata, each holder claims", "\n".join(b))


# ── 9. QML Simulation ──────────────────────────────────────────────────────
def qml():
    D = 12
    b = []
    # 2×2 實驗設計：資料來源 × 模型家族
    gx, gy, cw, ch = 104, 108, 72, 56
    b.append(t(gx + cw, 98, "model", 9.5, P["muted"], anchor="middle"))
    for j, s in enumerate(["classical", "quantum"]):
        b.append(t(gx + j * cw + cw / 2, 116 + 2 * ch + 16, s, 9.5, P["text2"], anchor="middle"))
    for i, s in enumerate(["classical", "quantum"]):
        b.append(t(gx - 8, gy + i * ch + ch / 2 + 4, s, 9.5, P["text2"], anchor="end"))
    b.append(t(gx - 8, gy - 4, "data ↓", 9.5, P["muted"], anchor="end"))
    cells = [(0, 0, "LR baseline"), (0, 1, "QSVM / QNN"), (1, 0, "LR baseline"), (1, 1, "QSVM / QNN")]
    for k, (i, j, name) in enumerate(cells):
        a, z = .02 + k * .245, .02 + (k + 1) * .245
        x, y = gx + j * cw, gy + i * ch
        b.append(f'<rect x="{x+2}" y="{y+2}" width="{cw-4}" height="{ch-4}" rx="2" fill="{P["panel"]}" stroke="{P["line"]}" stroke-width="1.2">'
                 + tl("stroke", [(a, P["line"]), (a + .005, P["accent"]), (z - .01, P["accent"]), (z - .005, P["line"])], D)
                 + tl("fill", [(a, P["panel"]), (a + .005, P["soft"]), (z - .01, P["soft"]), (z - .005, P["panel"])], D) + '</rect>')
        b.append(t(x + cw / 2, y + ch / 2 + 4, name, 9, P["text2"], anchor="middle"))
    b.append(t(30, 286, "data advantage vs model advantage", 9.5, P["muted"]))
    # ZZFeatureMap（2 qubits）示意
    qx = 292
    b.append(t(qx, 98, "ZZFeatureMap → fidelity kernel", 9.5, P["label"]))
    for k, y in enumerate([116, 144]):
        b.append(f'<line x1="{qx}" y1="{y}" x2="{qx+168}" y2="{y}" stroke="{P["rule"]}" stroke-width="1.2"/>')
        b.append(box(qx + 8, y - 9, 18, 18, P["accent"], P["bg"]) + t(qx + 17, y + 4, "H", 9.5, P["text"], anchor="middle"))
        b.append(box(qx + 34, y - 9, 30, 18, P["accent"], P["bg"]) + t(qx + 49, y + 4, "P(x)", 8.5, P["text"], anchor="middle"))
    for x in (qx + 78, qx + 134):
        b.append(f'<line x1="{x}" y1="116" x2="{x}" y2="150" stroke="{P["accent"]}" stroke-width="1.4"/><circle cx="{x}" cy="116" r="3.5" fill="{P["accent"]}"/>'
                 f'<circle cx="{x}" cy="144" r="7" fill="none" stroke="{P["accent"]}" stroke-width="1.4"/>')
    b.append(box(qx + 92, 135, 30, 18, P["accent"], P["bg"]) + t(qx + 107, 148, "P(φ)", 8.5, P["text"], anchor="middle"))
    # 核矩陣熱圖
    kx = 486
    vals = [[1, .8, .3, .1, .2, .1], [.8, 1, .4, .2, .1, .2], [.3, .4, 1, .7, .2, .1],
            [.1, .2, .7, 1, .3, .2], [.2, .1, .2, .3, 1, .8], [.1, .2, .1, .2, .8, 1]]
    for i in range(6):
        for j in range(6):
            b.append(f'<rect x="{kx+j*13}" y="{92+i*11}" width="12" height="10" fill="{P["accent"]}" opacity="0">'
                     + tl("opacity", [(.27 + (i + j) * .008, 0), (.3 + (i + j) * .008, vals[i][j] * .9), (.95, vals[i][j] * .9), (.96, 0)], D) + '</rect>')
    b.append(t(kx + 39, 172, "K(xᵢ, xⱼ)", 9, P["muted"], anchor="middle"))
    # 散點 + 決策邊界（線性 ↔ 曲線依格子切換）
    sx, sy, sw, sh = 292, 180, 284, 112
    b.append(box(sx, sy, sw, sh, P["line"], P["panel"]))
    for k in range(22):
        ang = k / 22 * 2 * math.pi
        r_in, r_out = 18 + (k * 7 % 9), 44 + (k * 5 % 8)
        b.append(f'<circle cx="{sx+142+r_in*math.cos(ang)*1.4:.1f}" cy="{sy+56+r_in*math.sin(ang)*.85:.1f}" r="3" fill="{P["accent"]}"/>')
        ox, oy = sx + 142 + r_out * math.cos(ang + .14) * 2.4, sy + 56 + r_out * math.sin(ang + .14) * .95
        if sx + 6 < ox < sx + sw - 6 and sy + 6 < oy < sy + sh - 6:
            b.append(f'<path d="M{ox-3:.1f} {oy-3:.1f}l6 6M{ox+3:.1f} {oy-3:.1f}l-6 6" stroke="{P["warn"]}" stroke-width="1.4"/>')
    lin = f"M{sx+40} {sy+sh-6} C {sx+100} {sy+sh-40}, {sx+180} {sy+46}, {sx+250} {sy+6}"
    cur = f"M{sx+60} {sy+56} C {sx+60} {sy-12}, {sx+224} {sy-12}, {sx+224} {sy+56}"
    cur2 = f"M{sx+60} {sy+56} C {sx+60} {sy+124}, {sx+224} {sy+124}, {sx+224} {sy+56}"
    b.append(f'<path d="{lin}" fill="none" stroke="{P["text2"]}" stroke-width="1.6" stroke-dasharray="5 4">'
             + tl("d", [(.02, lin), (.26, lin), (.28, cur), (.5, cur), (.52, lin), (.75, lin), (.77, cur), (.98, cur)], D) + '</path>')
    b.append(f'<path d="{cur2}" fill="none" stroke="{P["text2"]}" stroke-width="1.6" stroke-dasharray="5 4" opacity="0">'
             + tl("opacity", [(.27, 0), (.28, 1), (.5, 1), (.51, 0), (.76, 0), (.77, 1), (.98, 1)], D) + '</path>')
    return frame("QUANTUM ML STUDY", "QML Simulation", "Qiskit · QSVM · QNN",
                 "2×2 design: data source × model family · single-seed sim, method not advantage", "\n".join(b))


PROJECTS = {
    "chainlens": chainlens, "evidence-at-source": evidence, "medssi": medssi, "chaintrust": chaintrust,
    "pepefi": pepefi,
    "rwa-tokenization": rwa, "qml-simulation": qml,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for slug, fn in PROJECTS.items():
        with open(os.path.join(OUT, f"{slug}.svg"), "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", slug)
