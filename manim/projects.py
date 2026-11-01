"""
代表專案的 Manim 動畫（Manim Community Edition 0.22）

每個 Scene 對應 zuemen.net/projects 上的一個專案，依專案描述演出系統的實際運作方式。
同一份程式輸出兩種格式（見 manim/render.sh）：
  - GitHub README：640px GIF
  - zuemen.net：1080p MP4 + WebP 封面 + 循環預覽

單獨預覽一個場景：
    cd manim && manim -ql projects.py ChainLens
"""
import numpy as np
from manim import *
from style import *


# ═══ 1. ChainLens ════════════════════════════════════════════════════════════
class ChainLens(ProjectScene):
    AWARD = "FinTech Taipei Awards 2026 — Winner"
    TITLE = "ChainLens"
    TAGS = "SNA · GNN · AML"
    CAPTION = "rule engine traces the path upstream · GNN may only escalate · a person decides"

    def construct(self):
        # ── 資金流圖：來源 → 集資點（fan-in）→ 分散（fan-out）→ 出金地址 ──
        cy = (self.y_top + self.y_bot) / 2
        src = [np.array([-6.0, cy + d, 0]) for d in (1.3, 0, -1.3)]
        hub = np.array([-3.9, cy, 0])
        fan = [np.array([-1.8, cy + d, 0]) for d in (1.3, 0, -1.3)]
        dst = np.array([0.0, cy, 0])

        edges = ([Line(s, hub) for s in src] + [Line(hub, f) for f in fan] + [Line(f, dst) for f in fan])
        for e in edges:
            e.set_stroke(LINE, 3)
        nodes = VGroup(*[node().move_to(p) for p in src + fan])
        hub_n = node(0.24, WARN).move_to(hub)
        dst_n = Square(0.5, stroke_color=TEXT2, stroke_width=2.6, fill_color=PANEL, fill_opacity=1).move_to(dst)
        tags = VGroup(mono("sources", 16, MUTED).next_to(src[2], DOWN, 0.3),
                      mono("fan-in", 16, WARN).next_to(hub, DOWN, 0.4),
                      mono("fan-out", 16, WARN).next_to(fan[2], DOWN, 0.3),
                      mono("withdrawal", 16, MUTED).next_to(dst, RIGHT, 0.5))
        self.play(*[Create(e) for e in edges], FadeIn(nodes), FadeIn(hub_n), FadeIn(dst_n), FadeIn(tags), run_time=1.2)

        # ── 資金點沿著邊流動（三段依序） ──
        for group in (edges[:3], edges[3:6], edges[6:]):
            dots = [Dot(e.get_start(), 0.07, color=TEXT2) for e in group]
            self.play(*[MoveAlongPath(d, e) for d, e in zip(dots, group)], run_time=0.55, rate_func=linear)
            self.remove(*dots)

        # ── 右側審查面板 ──
        px = 4.35
        panel = card(4.7, 4.3).move_to([px, cy, 0])
        head = mono("WITHDRAWAL #4821", 16, LABEL).move_to(panel.get_corner(UL) + [1.45, -0.35, 0])
        r1 = mono("rule engine", 19, TEXT2).next_to(head, DOWN, 0.4, aligned_edge=LEFT)
        r2 = mono("GraphSAGE", 19, TEXT2).next_to(r1, DOWN, 0.28, aligned_edge=LEFT)
        sep = Line(panel.get_left() + [0.3, 0, 0], panel.get_right() - [0.3, 0, 0], stroke_color=LINE).next_to(r2, DOWN, 0.3)
        sep.set_x(px)
        verdict = mono("release", 26, MUTED).next_to(sep, DOWN, 0.3).align_to(r1, LEFT)
        self.play(FadeIn(panel), FadeIn(head), FadeIn(r1), FadeIn(r2), Create(sep), FadeIn(verdict), run_time=0.6)

        # ── 規則引擎：沿路徑往上游回溯，比對洗錢圖樣 ──
        back = [e.copy().set_stroke(ACCENT, 3.5) for e in reversed(edges)]
        self.play(LaggedStart(*[Create(b.reverse_points()) for b in back], lag_ratio=0.08), run_time=1.2)
        hit = mono("pattern hit", 18, WARN).next_to(r1, RIGHT).align_to(panel.get_right() - [0.3, 0, 0], RIGHT)
        self.play(FadeIn(hit, shift=LEFT * 0.2), Indicate(hub_n, color=WARN), run_time=0.6)

        # ── GraphSAGE：從目的地往外聚合鄰居 ──
        rings = [Circle(0.3, stroke_color=ACCENT, stroke_width=2).move_to(dst) for _ in range(2)]
        self.play(LaggedStart(*[r.animate.scale(6).set_stroke(opacity=0) for r in rings], lag_ratio=0.35), run_time=1.1)
        sv = ValueTracker(0)
        score = live_num(sv, "{:.2f}", 20, WARN, place=lambda m: m.move_to(r2).align_to(hit, RIGHT))
        self.add(score)
        self.play(sv.animate.set_value(0.87), run_time=0.7)

        # ── 判定：模型只能升級，不能自行扣留 ──
        v2 = mono("→ enhanced review", 26, WARN, BOLD).move_to(verdict, aligned_edge=LEFT)
        note = mono("may escalate, never hold", 15, MUTED).next_to(v2, DOWN, 0.15, aligned_edge=LEFT)
        self.play(Transform(verdict, v2), dst_n.animate.set_stroke(WARN), FadeIn(note), run_time=0.6)
        c1 = chip("evidence chain", PASS).next_to(note, DOWN, 0.3, aligned_edge=LEFT)
        c2 = chip("STR draft → analyst", ACCENT).next_to(c1, DOWN, 0.15, aligned_edge=LEFT)
        self.play(FadeIn(c1, shift=UP * 0.15), FadeIn(c2, shift=UP * 0.15), run_time=0.6)
        self.outro()


# ═══ 2. Evidence at Source ═══════════════════════════════════════════════════
class EvidenceAtSource(ProjectScene):
    AWARD = "GLEIF Appreciation Award"
    TITLE = "Evidence at Source"
    TAGS = "vLEI · VC · AI agents"
    CAPTION = "agents get a boolean and a reason code — never the record · a human decides"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 左：移工持有的錢包，事實由雙方在發生時簽章 ──
        wal = card(3.7, 4.3).move_to([-4.95, cy, 0])
        wl = mono("WORKER-HELD WALLET", 16, LABEL).move_to(wal.get_corner(UL) + [1.3, -0.35, 0])
        facts = VGroup(*[mono(s, 18, TEXT2) for s in ("employment start", "wages paid on time", "housing provided")])
        facts.arrange(DOWN, aligned_edge=LEFT, buff=0.28).next_to(wl, DOWN, 0.4, aligned_edge=LEFT)
        self.play(FadeIn(wal), FadeIn(wl), LaggedStart(*[FadeIn(f) for f in facts], lag_ratio=0.2), run_time=0.9)
        s1 = chip("sig · employer", PASS).next_to(facts, DOWN, 0.4, aligned_edge=LEFT)
        s2 = chip("sig · worker", PASS).next_to(s1, DOWN, 0.15, aligned_edge=LEFT)
        self.play(FadeIn(s1, shift=UP * 0.1), run_time=0.35)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.35)

        # ── 中：三層政策閘門 ──
        gates = VGroup()
        for i, s in enumerate(("L1 consent", "L2 purpose", "L3 minimise")):
            g = card(1.7, 0.75).move_to([-1.15, cy + 1.2 - i * 1.2, 0])
            gates.add(VGroup(g, mono(s, 15, TEXT2).move_to(g)))
        gl = mono("POLICY GATE", 16, LABEL).next_to(gates, UP, 0.3)

        # ── 右：銀行的 AI 代理，vLEI 授權鏈 ──
        ag = card(4.6, 4.3).move_to([3.95, cy, 0])
        al = mono("BANK'S AI AGENT", 16, LABEL).move_to(ag.get_corner(UL) + [1.15, -0.35, 0])
        chain_pts = [ag.get_left() + [0.7 + i * 1.6, 1.2, 0] for i in range(3)]
        chain = VGroup(*[node(0.13, ACCENT).move_to(p) for p in chain_pts])
        links = VGroup(*[DashedLine(chain_pts[i] + RIGHT * 0.15, chain_pts[i + 1] - RIGHT * 0.15, stroke_color=RULE)
                         for i in range(2)])
        names = VGroup(*[mono(s, 15, TEXT2).next_to(p, DOWN, 0.2) for s, p in zip(("GLEIF", "bank (LE)", "agent"), chain_pts)])
        q = mono("asks: “wages paid on time?”", 17, TEXT).next_to(names, DOWN, 0.5).align_to(names, LEFT)
        self.play(FadeIn(gates), FadeIn(gl), FadeIn(ag), FadeIn(al), FadeIn(chain), Create(links), FadeIn(names), run_time=0.8)
        # 每次查詢都重新驗證 vLEI 鏈
        self.play(LaggedStart(*[n.animate.set_fill(ACCENT) for n in chain], lag_ratio=0.3), run_time=0.7)
        self.play(FadeIn(q), run_time=0.4)

        # ── 查詢往左穿過閘門 → 回傳 boolean ──
        qc = chip("query", ACCENT, SOFT).move_to(q.get_left() + LEFT * 0.4)
        self.add(qc)
        self.play(qc.animate.move_to(gates[1]), run_time=0.6)
        self.play(*[g[0].animate.set_stroke(ACCENT) for g in gates], run_time=0.3)
        self.play(qc.animate.move_to(facts[1].get_right() + RIGHT * 0.5), run_time=0.5)
        self.play(Indicate(facts[1], color=PASS), FadeOut(qc), run_time=0.4)
        ans = chip("true · R-01", PASS).move_to(facts[1].get_right() + RIGHT * 0.6)
        self.play(ans.animate.move_to(gates[1]), run_time=0.45)
        got = mono("gets: true · reason R-01", 17, PASS, BOLD).next_to(q, DOWN, 0.3, aligned_edge=LEFT)
        self.play(Transform(ans, got), run_time=0.5)

        # ── 原始資料想離開 → 被閘門擋下 ──
        raw = chip("record", REFUSE).move_to(facts[1].get_right() + RIGHT * 0.1)
        self.play(FadeIn(raw), run_time=0.2)
        self.play(raw.animate.next_to(gates[0], LEFT, 0.08), gates[0][0].animate.set_stroke(REFUSE), run_time=0.45)
        x = cross().move_to(raw)
        stop = mono("record never leaves", 16, REFUSE).next_to(gates, DOWN, 0.3)
        self.play(FadeIn(x), FadeIn(stop), run_time=0.4)
        rev = mono("→ a named human reviewer decides", 15, ACCENT).next_to(got, DOWN, 0.4, aligned_edge=LEFT)
        self.play(FadeIn(rev), run_time=0.4)
        self.outro()


# ═══ 3. MedSSI ═══════════════════════════════════════════════════════════════
class MedSSI(ProjectScene):
    AWARD = "MODA Digital Credential Challenge 2025 — Merit"
    TITLE = "MedSSI"
    TAGS = "SSI · VC/DID · FHIR"
    CAPTION = "one credential, held by the patient · each verifier sees only its scenario's fields"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 醫院發一次憑證 ──
        hosp = card(1.9, 1.5).move_to([-5.8, cy + 0.3, 0])
        plus = VGroup(Rectangle(width=0.22, height=0.75), Rectangle(width=0.75, height=0.22)).set_fill(ACCENT, 1).set_stroke(width=0).move_to(hosp)
        ht = VGroup(sans("hospital", 20, TEXT2), mono("issues once", 15, MUTED)).arrange(DOWN, buff=0.1).next_to(hosp, DOWN, 0.25)

        # ── 政府數位皮夾，6 個 FHIR 欄位 ──
        names = ["patient name", "national ID", "medication", "dosage", "diagnosis", "lab results"]
        wal = card(3.4, 4.5, RULE, PANEL).move_to([-2.0, cy, 0])
        wl = mono("TW DIGITAL WALLET", 15, LABEL).next_to(wal.get_top(), DOWN, 0.25)
        rows = VGroup()
        for n in names:
            r = card(2.9, 0.5, LINE, BG)
            rows.add(VGroup(r, mono(n, 16, TEXT2).move_to(r.get_left() + RIGHT * 0.2, aligned_edge=LEFT)))
        rows.arrange(DOWN, buff=0.12).next_to(wl, DOWN, 0.25)
        self.play(FadeIn(hosp), FadeIn(plus), FadeIn(ht), FadeIn(wal), FadeIn(wl), run_time=0.6)
        vc = chip("VC", ACCENT, SOFT).move_to(hosp.get_right() + RIGHT * 0.3)
        self.play(vc.animate.move_to(wal.get_left()), run_time=0.5)
        self.play(FadeOut(vc), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.1), run_time=0.8)

        # ── 三個驗證方，每個情境只開放特定欄位 ──
        scen = [("pharmacy", [0, 2, 3]), ("researcher", [4, 5]), ("insurer", [0, 1, 4])]
        boxes = VGroup()
        for i, (nm, idx) in enumerate(scen):
            b = card(4.2, 1.15).move_to([3.95, cy + 1.45 - i * 1.45, 0])
            t1 = sans(nm, 22).move_to(b.get_corner(UL) + [0.25, -0.33, 0], aligned_edge=LEFT)
            t2 = mono(" · ".join(names[k].split()[0] for k in idx), 15, PASS).next_to(t1, DOWN, 0.12, aligned_edge=LEFT)
            boxes.add(VGroup(b, t1, t2))
        self.play(FadeIn(boxes), *[r.animate.set_opacity(0.35) for r in rows], run_time=0.5)

        for i, (nm, idx) in enumerate(scen):
            b = boxes[i][0]
            arrow = CurvedArrow(wal.get_right() + RIGHT * 0.05, b.get_left(), angle=-0.3 if i == 0 else (0 if i == 1 else 0.3),
                                stroke_color=ACCENT, stroke_width=2.5, tip_length=0.15)
            loa = mono("LoA ≥ substantial ✓", 14, PASS).move_to(b.get_corner(UR) + [-1.15, -0.3, 0])
            on = [rows[k] for k in idx]
            self.play(b.animate.set_stroke(ACCENT), *[r.animate.set_opacity(1) for r in on],
                      *[r[0].animate.set_stroke(PASS) for r in on], Create(arrow), FadeIn(loa), run_time=0.6)
            if nm == "pharmacy":
                # 藥局多要「診斷」→ 不在情境內，拒絕
                ask = chip("diagnosis ✗ outside scenario", REFUSE).next_to(b, DOWN, 0.08).shift(RIGHT * 0.3)
                self.play(FadeIn(ask, shift=UP * 0.1), Indicate(rows[4], color=REFUSE), run_time=0.6)
                self.wait(0.3)
                self.play(FadeOut(ask), run_time=0.25)
            else:
                self.wait(0.7)
            self.play(b.animate.set_stroke(LINE), *[r.animate.set_opacity(0.35) for r in on],
                      *[r[0].animate.set_stroke(LINE) for r in on], FadeOut(arrow), FadeOut(loa), run_time=0.35)
        self.play(*[r.animate.set_opacity(1) for r in rows], run_time=0.3)
        self.outro()


# ═══ 4. ChainTrust ═══════════════════════════════════════════════════════════
class ChainTrust(ProjectScene):
    AWARD = "Chunghwa Telecom Smart Innovation 2026 — Finalist"
    TITLE = "ChainTrust"
    TAGS = "SSI · SD-JWT · AI"
    CAPTION = "one KYC reused across institutions · high-risk transfers stopped in real time"

    def construct(self):
        top = self.y_top - 0.95
        # ── 上半：一次 KYC、到處重用 ──
        a = card(2.6, 1.2).move_to([-5.2, top, 0])
        at = VGroup(sans("Bank A", 22), mono("KYC once", 15, MUTED)).arrange(DOWN, buff=0.08).move_to(a)
        w = card(3.6, 1.45, ACCENT, SOFT).move_to([-0.9, top, 0])
        wt = VGroup(sans("SSI wallet", 22), mono("SD-JWT credential", 15, ACCENT),
                    mono("id_no · name · age · KYC lvl", 13, MUTED)).arrange(DOWN, buff=0.07).move_to(w)
        self.play(FadeIn(a), FadeIn(at), FadeIn(w), FadeIn(wt), run_time=0.5)
        iss = chip("issue", ACCENT, SOFT).move_to(a.get_right() + RIGHT * 0.3)
        self.play(iss.animate.move_to(w.get_left()), run_time=0.5)
        self.remove(iss)

        rps = []
        for i, nm in enumerate(("Bank B", "Securities C")):
            b = card(3.0, 0.62).move_to([4.6, top + 0.42 - i * 0.84, 0])
            rps.append(VGroup(b, sans(nm, 19).move_to(b.get_left() + RIGHT * 0.25, aligned_edge=LEFT)))
        self.play(*[FadeIn(r) for r in rps], run_time=0.3)
        for r in rps:
            # 只揭露需要的聲明，身分證號不出錢包
            p = chip("age≥20 · KYC 2", PASS).move_to(w.get_right() + RIGHT * 0.2)
            self.play(p.animate.move_to(r[0].get_left() + LEFT * 0.05), run_time=0.5)
            self.remove(p)
            tk = tick().move_to(r[0].get_right() + LEFT * 0.35)
            self.play(Create(tk), r[0].animate.set_stroke(PASS), run_time=0.3)
        nd = mono("id_no never disclosed", 15, MUTED).next_to(w, DOWN, 0.2)
        self.play(FadeIn(nd), run_time=0.3)

        sep = DashedLine([-6.6, top - 1.4, 0], [6.6, top - 1.4, 0], stroke_color=LINE, dash_length=0.06)
        self.play(Create(sep), run_time=0.3)

        # ── 下半：AI 即時防詐 ──
        y = top - 2.15
        lab = mono("AI ANTI-FRAUD", 16, LABEL).move_to([-6.6, y, 0], aligned_edge=LEFT)
        tx = mono("transfer  NT$280,000 → new payee, 02:14", 19, TEXT).next_to(lab, DOWN, 0.25, aligned_edge=LEFT)
        bar_bg = card(7.0, 0.32, LINE, PANEL).next_to(tx, DOWN, 0.3, aligned_edge=LEFT)
        thr_x = bar_bg.get_left()[0] + 7.0 * 0.7
        thr = DashedLine([thr_x, bar_bg.get_top()[1] + 0.15, 0], [thr_x, bar_bg.get_bottom()[1] - 0.15, 0], stroke_color=TEXT2)
        thr_t = mono("threshold 0.70", 14, MUTED).next_to(thr, DOWN, 0.08)
        self.play(FadeIn(lab), FadeIn(tx), FadeIn(bar_bg), Create(thr), FadeIn(thr_t), run_time=0.5)

        risk = ValueTracker(0.0)
        bar = always_redraw(lambda: Rectangle(
            width=max(7.0 * risk.get_value(), 0.001), height=0.32, stroke_width=0,
            fill_color=REFUSE if risk.get_value() > 0.7 else WARN, fill_opacity=1
        ).move_to(bar_bg.get_left(), aligned_edge=LEFT))
        num = live_num(risk, "{:.2f}", 24, color_fn=lambda v: REFUSE if v > 0.7 else WARN,
                       place=lambda m: m.next_to(bar_bg, RIGHT, 0.25))
        self.add(bar, num)
        self.play(risk.animate.set_value(0.91), run_time=1.3, rate_func=rush_into)
        stop = card(2.7, 1.0, REFUSE, BG).move_to([5.2, bar_bg.get_y() + 0.3, 0])
        st = VGroup(mono("INTERCEPTED", 20, REFUSE, BOLD), mono("call-back verify", 14, MUTED)).arrange(DOWN, buff=0.08).move_to(stop)
        self.play(FadeIn(stop, scale=1.1), FadeIn(st), run_time=0.45)
        self.outro()


# ═══ 5. PepeFi On-Chain CFD ═══════════════════════════════════════════════════
class PepeFi(ProjectScene):
    AWARD = "NCCU Capstone 2026 — Base Sepolia"
    TITLE = "PepeFi On-Chain CFD"
    TAGS = "Solidity · Foundry · RWA · x402"
    CAPTION = "RWA-referenced perps · credential-gated · reduce-only while the market is closed"

    def construct(self):
        top = self.y_top - 0.8
        # ── keeper 把公開市價推進受保護的 oracle ──
        kp = card(2.7, 1.6).move_to([-5.4, top - 0.1, 0])
        kt = VGroup(mono("KEEPER", 15, LABEL), mono("GitHub Actions", 16, TEXT2), mono("→ guarded oracle", 16, ACCENT)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to(kp)
        self.play(FadeIn(kp), FadeIn(kt), run_time=0.4)

        # ── 三個市場：美股、黃金、加密（合成部位，不發行實體資產） ──
        mk = []
        ys = [[0, .2, .1, .5, .45, .8], [.3, .25, .45, .4, .6, .55], [.2, .7, .4, .9, .55, 1.0]]
        for i, (sym, kind) in enumerate((("AAPL", "US equity"), ("XAU", "gold"), ("BTC", "crypto"))):
            b = card(2.9, 1.6).move_to([-1.75 + i * 3.1, top - 0.1, 0])
            s = mono(sym, 20, TEXT, BOLD).move_to(b.get_corner(UL) + [0.2, -0.27, 0], aligned_edge=LEFT)
            k = mono(kind, 14, MUTED).move_to(b.get_corner(UR) + [-0.2, -0.27, 0], aligned_edge=RIGHT)
            pts = [b.get_left() + [0.25 + j * 0.48, -0.25 + ys[i][j] * 0.45, 0] for j in range(6)]
            ln = VMobject(stroke_color=ACCENT, stroke_width=2.6).set_points_as_corners(pts)
            st = mono("24/7" if sym != "AAPL" else "market open", 14, PASS).move_to(b.get_corner(DL) + [0.2, 0.2, 0], aligned_edge=LEFT)
            mk.append(VGroup(b, s, k, ln, st))
        self.play(*[FadeIn(VGroup(m[0], m[1], m[2], m[4])) for m in mk], run_time=0.4)
        dot = Dot(kp.get_right(), 0.07, color=ACCENT)
        self.play(dot.animate.move_to(mk[0][0].get_left()), run_time=0.35)
        self.remove(dot)
        self.play(*[Create(m[3]) for m in mk], run_time=0.9)

        # ── 下半：憑證門檻與代理 session ──
        y0 = top - 1.6
        rows = VGroup(
            VGroup(sans("investor wallet", 19), chip("qualified-investor VC", ACCENT, SOFT)).arrange(RIGHT, buff=0.3),
            VGroup(sans("agent session", 19), chip("owner-bounded on-chain", ACCENT, SOFT)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([-6.6, y0 - 0.55, 0], aligned_edge=LEFT)
        self.play(FadeIn(rows), run_time=0.4)

        log_x = 0.6
        def entry(i, txt, why, ok):
            mark = (tick() if ok else cross()).move_to([log_x, y0 - 0.1 - i * 0.55, 0])
            col = PASS if ok else REFUSE
            t1 = mono(txt, 16, TEXT).next_to(mark, RIGHT, 0.25).shift(UP * 0.09)
            t2 = mono(why, 13, col).next_to(t1, DOWN, 0.05, aligned_edge=LEFT)
            return VGroup(mark, t1, t2)

        e1 = entry(0, "investor  open AAPL long 2x", "credential verified on-chain", True)
        self.play(FadeIn(e1, shift=RIGHT * 0.15), Indicate(rows[0][1], color=PASS), run_time=0.6)
        # 美股休市 → 只能減倉
        closed = mono("closed → reduce-only", 14, WARN).move_to(mk[0][4], aligned_edge=LEFT)
        self.play(Transform(mk[0][4], closed), mk[0][3].animate.set_stroke(MUTED), run_time=0.5)
        e2 = entry(1, "agent     open AAPL long", "refused: market closed", False)
        self.play(FadeIn(e2, shift=RIGHT * 0.15), run_time=0.5)
        e3 = entry(2, "agent     close AAPL", "allowed: reduce-only", True)
        self.play(FadeIn(e3, shift=RIGHT * 0.15), run_time=0.5)
        e4 = entry(3, "agent     buy signal  0.01 USDC", "paid over x402", True)
        self.play(FadeIn(e4, shift=RIGHT * 0.15), run_time=0.5)
        note = mono("testnet · mock USDC · synthetic exposure", 14, MUTED).next_to(rows, DOWN, 0.5, aligned_edge=LEFT)
        self.play(FadeIn(note), run_time=0.3)
        self.outro()


# ═══ 6. RWA Real Estate Tokenization ═════════════════════════════════════════
class RWATokenization(ProjectScene):
    AWARD = "Blockchain Implementation"
    TITLE = "RWA Real Estate Tokenization"
    TAGS = "Solidity · Hardhat · ERC-3643-style"
    CAPTION = "identity is enforced inside the token · rent is split pro rata and each holder claims"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        cols = {"A": ACCENT, "B": PASS, "C": WARN, "D": MUTED}
        owner = ["A"] * 6 + ["B"] * 4 + ["C"] * 2

        # ── 建築：12 扇窗 = 12 個代幣單位，顏色代表持有人 ──
        body = card(2.8, 3.6, RULE, PANEL).move_to([-5.2, cy - 0.35, 0])
        roof = Polygon(body.get_corner(UL) + LEFT * 0.15, body.get_top() + UP * 0.75, body.get_corner(UR) + RIGHT * 0.15,
                       stroke_color=RULE, stroke_width=2, fill_color=PANEL2, fill_opacity=1)
        wins = VGroup(*[Rectangle(width=0.58, height=0.58, stroke_width=0, fill_color=cols[o], fill_opacity=0.8) for o in owner])
        wins.arrange_in_grid(4, 3, buff=0.22).move_to(body)
        cap = mono("PropertyToken · 12 units", 15, MUTED).next_to(body, DOWN, 0.2)
        self.play(FadeIn(body), FadeIn(roof), LaggedStart(*[FadeIn(w) for w in wins], lag_ratio=0.05), FadeIn(cap), run_time=1.0)

        # ── 合約：身分登記（白名單）＋ 租金分配 ──
        reg = card(3.4, 1.9, ACCENT, SOFT).move_to([-1.2, cy + 1.0, 0])
        rt = VGroup(mono("IdentityRegistry", 18), mono("on-chain KYC allowlist", 13, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        rt.move_to(reg.get_corner(UL) + [0.2, -0.35, 0], aligned_edge=UL)
        ids = VGroup()
        for i, h in enumerate("ABCD"):
            m = (tick() if h != "D" else cross()).scale(0.8)
            ids.add(VGroup(mono(h, 20, TEXT, BOLD), m).arrange(DOWN, buff=0.12))
        ids.arrange(RIGHT, buff=0.5).move_to(reg.get_bottom() + UP * 0.55)
        dist = card(3.4, 1.7, ACCENT, SOFT).move_to([-1.2, cy - 1.15, 0])
        dt = VGroup(mono("RentalDistributor", 18), mono("pro rata · holders claim", 13, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        dt.move_to(dist.get_corner(UL) + [0.2, -0.35, 0], aligned_edge=UL)
        self.play(FadeIn(reg), FadeIn(rt), FadeIn(ids), FadeIn(dist), FadeIn(dt), run_time=0.6)

        # ── 右：持有人表 ──
        hx = 1.85
        hdr = VGroup(mono("HOLDER", 15, LABEL).move_to([hx, cy + 1.75, 0], aligned_edge=LEFT),
                     mono("UNITS", 15, LABEL).move_to([hx + 2.9, cy + 1.75, 0], aligned_edge=RIGHT),
                     mono("CLAIM", 15, LABEL).move_to([hx + 4.5, cy + 1.75, 0], aligned_edge=RIGHT))
        units = {"A": 6, "B": 4, "C": 2, "D": 0}
        rows, unum = {}, {}
        for i, h in enumerate("ABCD"):
            y = cy + 1.1 - i * 0.7
            sw = Square(0.22, stroke_width=0, fill_color=cols[h], fill_opacity=0.85).move_to([hx + 0.11, y, 0])
            nm = mono(f"holder {h}", 18, TEXT2).next_to(sw, RIGHT, 0.2)
            un = mono(str(units[h]), 20).move_to([hx + 2.9, y, 0], aligned_edge=RIGHT)
            rows[h] = VGroup(sw, nm)
            unum[h] = un
        self.play(FadeIn(hdr), *[FadeIn(r) for r in rows.values()], *[FadeIn(u) for u in unum.values()], run_time=0.5)

        # ── 轉讓 A→C：雙方都在白名單 → 成功 ──
        tok = chip("1 unit", TEXT2, PANEL2).move_to(rows["A"][1].get_left())
        self.play(tok.animate.move_to(reg.get_right() + LEFT * 0.4), run_time=0.45)
        self.play(Indicate(ids[0], color=PASS), Indicate(ids[2], color=PASS), run_time=0.4)
        self.play(tok.animate.move_to(rows["C"][1].get_left()), run_time=0.45)
        self.remove(tok)
        self.play(wins[5].animate.set_fill(WARN),
                  Transform(unum["A"], mono("5", 20, TEXT, BOLD).move_to(unum["A"], aligned_edge=RIGHT)),
                  Transform(unum["C"], mono("3", 20, TEXT, BOLD).move_to(unum["C"], aligned_edge=RIGHT)), run_time=0.5)

        # ── 轉讓 A→D：D 未通過 KYC → 代幣合約自己拒絕 ──
        tok2 = chip("1 unit → D", REFUSE).move_to(rows["A"][1].get_left())
        self.play(tok2.animate.move_to(reg.get_right() + LEFT * 0.6), run_time=0.45)
        rej = mono("rejected by the token contract", 15, REFUSE).next_to(reg, UP, 0.12)
        self.play(Indicate(ids[3], color=REFUSE), FadeIn(rej), Wiggle(tok2), run_time=0.7)
        self.play(FadeOut(tok2), FadeOut(rej), run_time=0.3)

        # ── 租金 1,200 USDC 依持有比例 5:4:3 分配，各自領取 ──
        rent = mono("rent in: 1,200 mock USDC", 15, ACCENT).move_to(dist.get_bottom() + UP * 0.4)
        self.play(FadeIn(rent, shift=UP * 0.1), run_time=0.4)
        claims = []
        for h, amt in (("A", 500), ("B", 400), ("C", 300)):
            d = Dot(rent.get_right(), 0.08, color=cols[h])
            y = rows[h].get_y()
            c = mono(str(amt), 20, cols[h]).move_to([hx + 4.5, y, 0], aligned_edge=RIGHT)
            claims.append((d, c))
        self.play(*[d.animate.move_to(c.get_left() + LEFT * 0.2) for d, c in claims], run_time=0.7)
        self.play(*[FadeOut(d) for d, _ in claims], *[FadeIn(c) for _, c in claims],
                  FadeIn(mono("—", 22, MUTED).move_to([hx + 4.5, rows["D"].get_y(), 0], aligned_edge=RIGHT)), run_time=0.4)
        self.outro()


# ═══ 7. QML Simulation ═══════════════════════════════════════════════════════
class QMLSimulation(ProjectScene):
    AWARD = "Quantum ML Study"
    TITLE = "QML Simulation"
    TAGS = "Qiskit · QSVM · QNN"
    CAPTION = "2×2 design: data source × model family · single-seed sim — the method, not an advantage"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 左：2×2 實驗設計 ──
        g0 = np.array([-4.55, cy + 0.15, 0])
        cells = VGroup()
        for i in range(2):
            for j in range(2):
                c = card(1.75, 1.15).move_to(g0 + [j * 1.85, -i * 1.25, 0])
                cells.add(VGroup(c, mono("LR baseline" if j == 0 else "QSVM / QNN", 14, TEXT2).move_to(c)))
        colh = VGroup(*[mono(s, 15, TEXT2).next_to(cells[j], UP, 0.15) for j, s in enumerate(("classical", "quantum"))])
        rowh = VGroup(*[mono(s, 15, TEXT2).next_to(cells[i * 2], LEFT, 0.15) for i, s in enumerate(("classical", "quantum"))])
        axm = mono("model →", 14, MUTED).next_to(colh, UP, 0.12)
        axd = mono("data ↓", 14, MUTED).next_to(rowh, UP, 0.5).align_to(rowh, RIGHT)
        self.play(FadeIn(cells), FadeIn(colh), FadeIn(rowh), FadeIn(axm), FadeIn(axd), run_time=0.6)
        q = mono("data advantage vs model advantage?", 15, MUTED).next_to(cells, DOWN, 0.35).align_to(rowh, LEFT)
        self.play(FadeIn(q), run_time=0.3)

        # ── 右上：ZZFeatureMap 電路 + 量子核 ──
        cx = 0.6
        wires = VGroup(*[Line([cx, cy + 1.6 - k * 0.7, 0], [cx + 3.6, cy + 1.6 - k * 0.7, 0], stroke_color=RULE) for k in range(2)])
        def gate(x, y, s, w=0.5):
            r = card(w, 0.42, ACCENT, BG).move_to([x, y, 0])
            return VGroup(r, mono(s, 13).move_to(r))
        ys = [cy + 1.6, cy + 0.9]
        circ = VGroup(*[gate(cx + 0.4, y, "H") for y in ys], *[gate(cx + 1.1, y, "P(x)", 0.7) for y in ys])
        for x in (cx + 1.9, cx + 2.9):
            circ.add(Line([x, ys[0], 0], [x, ys[1], 0], stroke_color=ACCENT, stroke_width=2.4),
                     Dot([x, ys[0], 0], 0.07, color=ACCENT),
                     Circle(0.13, stroke_color=ACCENT, stroke_width=2.4).move_to([x, ys[1], 0]))
        circ.add(gate(cx + 2.4, ys[1], "P(φ)", 0.7))
        ft = mono("ZZFeatureMap", 15, LABEL).next_to(wires, UP, 0.42, aligned_edge=LEFT)
        self.play(Create(wires), FadeIn(ft), LaggedStart(*[FadeIn(m) for m in circ], lag_ratio=0.05), run_time=0.9)
        kern = MathTex(r"K(x,x')=\big|\langle\phi(x)\,|\,\phi(x')\rangle\big|^2", font_size=30, color=ACCENT)
        kern.next_to(wires, DOWN, 0.35, aligned_edge=LEFT)
        # 核矩陣熱圖
        vals = np.array([[1, .8, .3, .1, .2, .1], [.8, 1, .4, .2, .1, .2], [.3, .4, 1, .7, .2, .1],
                         [.1, .2, .7, 1, .3, .2], [.2, .1, .2, .3, 1, .8], [.1, .2, .1, .2, .8, 1]])
        heat = VGroup(*[Square(0.22, stroke_width=0, fill_color=ACCENT, fill_opacity=0.9 * v) for v in vals.flatten()])
        heat.arrange_in_grid(6, 6, buff=0.03).move_to([5.6, cy + 1.25, 0])
        self.play(Write(kern), LaggedStart(*[FadeIn(h) for h in heat], lag_ratio=0.01), run_time=1.0)

        # ── 右下：資料散點 + 決策邊界（線性 ↔ 量子核的曲線邊界）──
        plot = card(6.4, 2.35, LINE, PANEL).move_to([3.6, cy - 1.35, 0])
        c0 = plot.get_center()
        rng = np.random.default_rng(3)
        inner, outer = VGroup(), VGroup()
        for k in range(26):
            a = rng.uniform(0, TAU)
            r = rng.uniform(0.15, 0.55)
            inner.add(Dot(c0 + [r * 2.1 * np.cos(a), r * 1.2 * np.sin(a), 0], 0.05, color=ACCENT))
            r2 = rng.uniform(0.75, 0.98)
            p = c0 + [r2 * 2.9 * np.cos(a + .2), r2 * 1.05 * np.sin(a + .2), 0]
            outer.add(Cross(scale_factor=0.06, stroke_color=WARN, stroke_width=2.5).move_to(p))
        self.play(FadeIn(plot), LaggedStart(*[FadeIn(d) for d in inner], lag_ratio=0.02),
                  LaggedStart(*[FadeIn(d) for d in outer], lag_ratio=0.02), run_time=0.8)

        lin = DashedLine(c0 + [-2.6, -0.95, 0], c0 + [2.6, 0.95, 0], stroke_color=TEXT2, stroke_width=2.4)
        ell = DashedVMobject(Ellipse(width=2.9 * 1.45, height=1.05 * 1.45, stroke_color=TEXT2, stroke_width=2.4).move_to(c0), num_dashes=40)
        tag = mono("", 14)
        # 依序點亮 2×2 的四格，邊界跟著模型家族切換
        for k in range(4):
            j = k % 2
            hl = [cells[k][0].animate.set_stroke(ACCENT).set_fill(SOFT)]
            if k > 0:
                hl += [cells[k - 1][0].animate.set_stroke(LINE).set_fill(PANEL)]
            new_tag = mono("linear boundary" if j == 0 else "quantum-kernel boundary", 14, MUTED).next_to(plot, UP, 0.1, aligned_edge=RIGHT)
            if k == 0:
                self.play(*hl, Create(lin), FadeIn(new_tag), run_time=0.6)
                cur = lin
            else:
                tgt = ell if j == 1 else lin.copy()
                self.play(*hl, ReplacementTransform(cur, tgt), ReplacementTransform(tag, new_tag), run_time=0.7)
                cur = tgt
            tag = new_tag
            self.wait(0.35)
        self.play(cells[3][0].animate.set_stroke(LINE).set_fill(PANEL), run_time=0.3)
        self.outro()


SCENES = {
    "chainlens": ChainLens, "evidence-at-source": EvidenceAtSource, "medssi": MedSSI,
    "chaintrust": ChainTrust, "pepefi": PepeFi, "rwa-tokenization": RWATokenization,
    "qml-simulation": QMLSimulation,
}
