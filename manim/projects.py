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
    CAPTION = "rules trace the money upstream · the model may only escalate · a person decides"
    DISCLOSURE = "synthetic scenario 07 · model trained and tested on synthetic data"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 情境 07：一筆出金申請，地址本身看起來乾淨 ──
        L = self.x_left
        src = [np.array([L + 0.35, cy + d, 0]) for d in (1.4, 0, -1.4)]
        hub = np.array([L + 2.35, cy, 0])
        hop = [np.array([L + 4.1, cy + d, 0]) for d in (0.9, -0.9)]
        dst = np.array([L + 5.9, cy, 0])
        edges = [Line(s, hub) for s in src] + [Line(hub, h) for h in hop] + [Line(h, dst) for h in hop]
        for e in edges:
            e.set_stroke(LINE, 3)
        nodes = VGroup(*[node().move_to(p) for p in src + hop])
        hub_n = node(0.24, WARN).move_to(hub)
        dst_n = Square(0.5, stroke_color=TEXT2, stroke_width=2.6, fill_color=PANEL, fill_opacity=1).move_to(dst)
        tags = VGroup(mono("sources", 16, MUTED).next_to(src[2], DOWN, 0.3),
                      mono("fast in-out relay", 16, WARN).next_to(hub, DOWN, 0.45),
                      mono("TRelay03", 16, TEXT2).next_to(dst, DOWN, 0.35))
        px = 3.35
        panel = card(6.1, 4.5).move_to([px, cy, 0])
        pl = panel.get_left()[0] + 0.3
        head = mono("WITHDRAWAL REQUEST", 16, LABEL).move_to([pl, panel.get_top()[1] - 0.35, 0], aligned_edge=LEFT)
        req = mono("200,000 USDT → TRelay03", 20).next_to(head, DOWN, 0.15, aligned_edge=LEFT)
        self.play(*[Create(e) for e in edges], FadeIn(nodes), FadeIn(hub_n), FadeIn(dst_n), FadeIn(tags),
                  FadeIn(panel), FadeIn(head), FadeIn(req), run_time=1.2)
        self.hold(1.0)

        # ── 規則引擎：沿路徑往上游回溯 → 0.19，規則說 release ──
        r1 = mono("rule engine", 18, TEXT2).next_to(req, DOWN, 0.45, aligned_edge=LEFT)
        r2 = mono("graph model", 18, TEXT2).next_to(r1, DOWN, 0.3, aligned_edge=LEFT)
        nx = panel.get_right()[0] - 0.3
        self.play(FadeIn(r1), FadeIn(r2), run_time=0.3)
        back = [e.copy().set_stroke(ACCENT, 3.5) for e in reversed(edges)]
        self.play(LaggedStart(*[Create(b.reverse_points()) for b in back], lag_ratio=0.1), run_time=1.3)
        s1 = mono("0.19 · release", 18, PASS).move_to([nx, r1.get_y(), 0], aligned_edge=RIGHT)
        self.play(FadeIn(s1, shift=LEFT * 0.15), run_time=0.4)
        self.hold(1.4)

        # ── 圖模型：從目的地往外聚合鄰居 → 0.98 ──
        rings = [Circle(0.3, stroke_color=ACCENT, stroke_width=2).move_to(dst) for _ in range(2)]
        self.play(LaggedStart(*[r.animate.scale(6).set_stroke(opacity=0) for r in rings], lag_ratio=0.35), run_time=1.1)
        sv = ValueTracker(0)
        score = live_num(sv, "{:.2f}", 18, WARN, place=lambda m: m.move_to([nx, r2.get_y(), 0], aligned_edge=RIGHT))
        self.add(score)
        self.play(sv.animate.set_value(0.98), run_time=0.7)
        sep = Line([pl, 0, 0], [nx, 0, 0], stroke_color=LINE).next_to(r2, DOWN, 0.3).set_x((pl + nx) / 2)
        verdict = mono("ENHANCED REVIEW", 24, WARN, BOLD).next_to(sep, DOWN, 0.3).align_to(r1, LEFT)
        self.play(Create(sep), FadeIn(verdict), dst_n.animate.set_stroke(WARN), run_time=0.6)
        self.hold(1.4)

        # ── 模型能做與不能做的（UI 原句：≥0.70 只能把 release 升級） ──
        rules = VGroup(
            VGroup(tick().scale(0.7), mono("may raise release → review", 16, TEXT)),
            VGroup(cross().scale(0.7), mono("cannot hold a withdrawal on its own", 16, TEXT2)),
            VGroup(cross().scale(0.7), mono("cannot downgrade the rules", 16, TEXT2)))
        for r in rules:
            r.arrange(RIGHT, buff=0.2)
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(verdict, DOWN, 0.3, aligned_edge=LEFT)
        for r in rules:
            self.play(FadeIn(r, shift=RIGHT * 0.1), run_time=0.35)
            self.hold(0.7)

        # ── 證據交給人 ──
        self.play(FadeOut(rules), run_time=0.3)
        c1 = chip("evidence chain", PASS, BG, 16)
        c2 = chip("STR draft → compliance officer", ACCENT, BG, 16)
        cc = VGroup(c1, c2).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(verdict, DOWN, 0.3, aligned_edge=LEFT)
        who = mono("a person makes the final call", 18, ACCENT).next_to(cc, DOWN, 0.25, aligned_edge=LEFT)
        self.play(FadeIn(c1, shift=UP * 0.1), FadeIn(c2, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(who), run_time=0.4)
        self.outro()


# ═══ 2. Evidence at Source ═══════════════════════════════════════════════════
class EvidenceAtSource(ProjectScene):
    AWARD = "GLEIF Appreciation Award"
    TITLE = "Evidence at Source"
    TAGS = "vLEI · VC · AI agents"
    CAPTION = "agents get yes/no answers, never the record · gates run L0 → L1 → L2"
    DISCLOSURE = "fictional worker · vLEI chain simulated · bank name fictional"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 左：Siti 的錢包，四張卡 ──
        wal = card(4.1, 4.5).move_to([self.x_left + 2.1, cy, 0])
        wl = mono("SITI'S WALLET", 16, LABEL).move_to(wal.get_corner(UL) + [0.25, -0.35, 0], aligned_edge=LEFT)
        rows = VGroup(*[mono(s, 18, TEXT2) for s in ("recruitment fee", "passport custody", "contract consent", "working hours")])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(wl, DOWN, 0.4, aligned_edge=LEFT)
        self.play(FadeIn(wal), FadeIn(wl), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.2), run_time=1.0)
        self.hold(0.8)
        # 工時卡在發薪日由工廠簽、Siti 會簽
        s1 = chip("FACTORY ✓ signs on payday", PASS, BG, 16).next_to(rows, DOWN, 0.4, aligned_edge=LEFT)
        s2 = chip("SITI ✓ countersigns", PASS, BG, 16).next_to(s1, DOWN, 0.15, aligned_edge=LEFT)
        self.play(Indicate(rows[3], color=PASS), FadeIn(s1, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(s2, shift=UP * 0.1), run_time=0.4)
        self.hold(0.9)

        # ── 右：銀行的 agent，vLEI 授權鏈 ──
        ag = card(4.4, 4.5).move_to([self.x_right - 2.2, cy, 0])
        al = mono("BANK'S AGENT", 16, LABEL).move_to(ag.get_corner(UL) + [0.25, -0.35, 0], aligned_edge=LEFT)
        pts = [ag.get_left() + [0.6 + i * 1.6, 1.15, 0] for i in range(3)]
        chain = VGroup(*[node(0.13, ACCENT).move_to(p) for p in pts])
        links = VGroup(*[DashedLine(pts[i] + RIGHT * 0.15, pts[i + 1] - RIGHT * 0.15, stroke_color=RULE) for i in range(2)])
        names = VGroup(*[mono(s, 16, TEXT2).next_to(p, DOWN, 0.18) for s, p in zip(("GLEIF", "bank", "agent"), pts)])
        sim = mono("vLEI chain · simulated", 16, WARN).next_to(names, DOWN, 0.2).align_to(al, LEFT)
        q1 = VGroup(mono("asks:", 16, MUTED), mono("zeroRecruitmentFeePaid?", 18)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        q1.next_to(sim, DOWN, 0.35).align_to(al, LEFT)
        self.play(FadeIn(ag), FadeIn(al), FadeIn(chain), Create(links), FadeIn(names), FadeIn(sim), run_time=0.8)
        self.play(FadeIn(q1), run_time=0.4)
        self.hold(0.9)

        # ── 中：三道閘門，依序 L0 → L1 → L2 ──
        gx = (wal.get_right()[0] + ag.get_left()[0]) / 2
        gates = VGroup()
        for i, s in enumerate(("L0  who is asking?", "L1  is it genuine?", "L2  may this be asked?")):
            g = card(3.0, 0.8).move_to([gx, cy + 1.35 - i * 1.15, 0])
            gates.add(VGroup(g, mono(s, 16, TEXT2).move_to(g)))
        order = mono("nothing is read before L0 passes", 16, MUTED).next_to(gates, DOWN, 0.3)
        self.play(FadeIn(gates), run_time=0.4)
        qc = chip("query", ACCENT, SOFT, 16).move_to(q1.get_left() + LEFT * 0.1)
        self.add(qc)
        for g in gates:
            self.play(qc.animate.move_to(g[0].get_right() + RIGHT * 0.05), run_time=0.35)
            self.play(g[0].animate.set_stroke(PASS), g[1].animate.set_color(PASS), run_time=0.3)
            self.hold(0.3)
        self.play(FadeIn(order), qc.animate.move_to(rows[0].get_right() + RIGHT * 0.5), run_time=0.5)
        self.play(Indicate(rows[0], color=PASS), FadeOut(qc), run_time=0.4)
        ans = mono("gets: true", 20, PASS, BOLD).next_to(q1, DOWN, 0.25, aligned_edge=LEFT)
        self.play(FadeIn(ans, shift=RIGHT * 0.1), run_time=0.4)
        self.hold(1.2)

        # ── 第二個問題：手續費金額 → L2 擋下（只放行是非題與匿名匯總） ──
        self.play(*[g[0].animate.set_stroke(LINE) for g in gates], *[g[1].animate.set_color(TEXT2) for g in gates],
                  FadeOut(order), run_time=0.3)
        q2 = VGroup(mono("asks:", 16, MUTED), mono("feeAmount?", 18)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        q2.next_to(ans, DOWN, 0.3, aligned_edge=LEFT)
        self.play(FadeIn(q2), run_time=0.4)
        qc2 = chip("query", REFUSE, SOFT, 16).move_to(q2.get_left() + LEFT * 0.1)
        self.add(qc2)
        for g in gates[:2]:
            self.play(qc2.animate.move_to(g[0].get_right() + RIGHT * 0.05), g[0].animate.set_stroke(PASS), run_time=0.35)
        self.play(qc2.animate.move_to(gates[2][0].get_right() + RIGHT * 0.05), run_time=0.35)
        why = VGroup(mono("L2: yes/no or k-anonymous", 16, REFUSE),
                     mono("aggregates only", 16, REFUSE)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).next_to(gates, DOWN, 0.3)
        self.play(gates[2][0].animate.set_stroke(REFUSE), gates[2][1].animate.set_color(REFUSE), Wiggle(qc2),
                  FadeIn(why), run_time=0.7)
        self.play(FadeOut(qc2), Indicate(rows[0], color=REFUSE), run_time=0.4)
        self.hold(1.4)
        rev = mono("→ a named human reviewer decides", 18, ACCENT).next_to(q2, DOWN, 0.3).align_to(al, LEFT)
        self.play(FadeIn(rev), run_time=0.4)
        self.outro()


# ═══ 3. MedSSI ═══════════════════════════════════════════════════════════════
class MedSSI(ProjectScene):
    AWARD = "Digital Credential Challenge 2025 — Merit Award"
    TITLE = "MedSSI"
    TAGS = "SSI · VC/DID · FHIR"
    CAPTION = "the patient holds the cards · each verifier sees only its scenario's fields"
    DISCLOSURE = "fictional patient · issuing and verifying ran in the 2025 MODA wallet sandbox"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 左：醫院 → 數位部沙盒（發卡與驗章）──
        lx = self.x_left + 1.2
        hosp = card(2.3, 1.1).move_to([lx, cy + 1.4, 0])
        plus = VGroup(Rectangle(width=0.14, height=0.5), Rectangle(width=0.5, height=0.14)).set_fill(ACCENT, 1).set_stroke(width=0)
        ht = VGroup(plus, sans("hospital", 20, TEXT2)).arrange(RIGHT, buff=0.2).move_to(hosp)
        box = card(2.3, 1.3, WARN, BG).move_to([lx, cy - 0.3, 0])
        bt = VGroup(mono("MODA sandbox", 16, WARN), mono("issues &", 16, TEXT2), mono("verifies", 16, TEXT2)).arrange(DOWN, buff=0.06).move_to(box)
        ar = Arrow(hosp.get_bottom(), box.get_top(), buff=0.05, stroke_width=2.4, color=RULE, max_tip_length_to_length_ratio=0.3)

        # ── 中：政府數位皮夾，欄位 · 卡別 ──
        data = [("medicine & dose", "prescription"), ("days' supply", "prescription"), ("allergies", "allergy card"),
                ("diagnosis", "condition card"), ("research consent", "consent card"), ("ID details", "identity card")]
        wal = card(4.6, 4.5, RULE, PANEL).move_to([self.x_left + 5.15, cy, 0])
        wl = mono("TW DIGITAL WALLET", 16, LABEL).next_to(wal.get_top(), DOWN, 0.22)
        rows = VGroup()
        for f, c in data:
            r = card(4.2, 0.52, LINE, BG)
            rows.add(VGroup(r, mono(f, 16, TEXT).move_to(r.get_left() + RIGHT * 0.18, aligned_edge=LEFT),
                            mono(c, 16, MUTED).move_to(r.get_right() + LEFT * 0.18, aligned_edge=RIGHT)))
        rows.arrange(DOWN, buff=0.1).next_to(wl, DOWN, 0.22)
        self.play(FadeIn(hosp), FadeIn(ht), run_time=0.4)
        self.play(GrowArrow(ar), FadeIn(box), FadeIn(bt), run_time=0.5)
        self.hold(0.8)
        self.play(FadeIn(wal), FadeIn(wl), run_time=0.3)
        vc = chip("VC", ACCENT, SOFT, 16).move_to(box.get_right() + RIGHT * 0.3)
        self.play(vc.animate.move_to(wal.get_left()), run_time=0.5)
        self.play(FadeOut(vc), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.12), run_time=1.0)
        self.hold(1.0)

        # ── 右：驗證方，每個情境只開放特定卡 ──
        rx = self.x_right - 1.95
        scen = [("PHARMACY · pickup", "prescription + allergy cards", [0, 1, 2]),
                ("RESEARCH · authorization", "condition + consent cards", [3, 4])]
        boxes = VGroup()
        for i, (nm, sub, _) in enumerate(scen):
            b = card(3.9, 1.25).move_to([rx, cy + 1.3 - i * 2.2, 0])
            t1 = mono(nm, 16, TEXT).move_to(b.get_corner(UL) + [0.2, -0.3, 0], aligned_edge=LEFT)
            t2 = mono(sub, 16, ACCENT).next_to(t1, DOWN, 0.12, aligned_edge=LEFT)
            boxes.add(VGroup(b, t1, t2))
        self.play(FadeIn(boxes), *[r.animate.set_opacity(0.35) for r in rows], run_time=0.5)

        for i, (_, _, idx) in enumerate(scen):
            b = boxes[i][0]
            on = [rows[k] for k in idx]
            arrow = Arrow(wal.get_right(), b.get_left(), buff=0.08, stroke_width=2.4, color=ACCENT, max_tip_length_to_length_ratio=0.15)
            ial = mono("min. assurance level ✓", 16, PASS).next_to(b, DOWN, 0.1, aligned_edge=LEFT)
            self.play(b.animate.set_stroke(ACCENT), *[r.animate.set_opacity(1) for r in on],
                      *[r[0].animate.set_stroke(PASS) for r in on], GrowArrow(arrow), FadeIn(ial), run_time=0.7)
            self.hold(1.2)
            if i == 0:
                # 藥局多要「診斷」→ 不在這次的範圍，伺服器拒絕
                ask = VGroup(mono("+ asks for diagnosis", 16, REFUSE),
                             mono("✗ unrequested field → rejected", 16, REFUSE, BOLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
                ask.next_to(ial, DOWN, 0.15, aligned_edge=LEFT)
                self.play(FadeIn(ask, shift=UP * 0.1), Indicate(rows[3], color=REFUSE), run_time=0.6)
                self.hold(1.6)
                self.play(FadeOut(ask), run_time=0.3)
            self.play(b.animate.set_stroke(LINE), *[r.animate.set_opacity(0.35) for r in on],
                      *[r[0].animate.set_stroke(LINE) for r in on], FadeOut(arrow), FadeOut(ial), run_time=0.35)
        self.play(*[r.animate.set_opacity(1) for r in rows], run_time=0.3)
        self.outro()


# ═══ 4. ChainTrust ═══════════════════════════════════════════════════════════
class ChainTrust(ProjectScene):
    AWARD = "Chunghwa Telecom Smart Innovation 2026 — Finalist"
    TITLE = "ChainTrust"
    TAGS = "SSI · SD-JWT · AI"
    CAPTION = "one KYC reused across institutions · risky transfers scored and blocked in real time"
    DISCLOSURE = "proof of concept · fraud model trained on synthetic data"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        L = self.x_left
        # ── 第一幕：發卡方（中華電信門號電子卡、銀行 KYC）→ 錢包 ──
        root = mono("trust root: CHT PublicCA", 16, LABEL).move_to([L, self.y_top - 0.2, 0], aligned_edge=LEFT)
        iss = VGroup()
        for i, (a, b) in enumerate((("CHT mobile eID", "issuer"), ("Bank A", "KYC once"))):
            c = card(2.7, 1.0).move_to([L + 1.35, cy + 0.75 - i * 1.3, 0])
            iss.add(VGroup(c, VGroup(sans(a, 19), mono(b, 16, MUTED)).arrange(DOWN, buff=0.06).move_to(c)))
        w = card(3.9, 3.7, ACCENT, SOFT).move_to([L + 5.55, cy - 0.1, 0])
        wt = VGroup(sans("SSI wallet", 20), mono("SD-JWT KYC credential", 16, ACCENT)).arrange(DOWN, buff=0.06)
        wt.move_to(w.get_top() + DOWN * 0.5)
        claims = VGroup(*[mono(s, 18, TEXT2) for s in ("fullName", "birthDate", "country", "over18", "kycLevel")])
        claims.arrange(DOWN, aligned_edge=LEFT, buff=0.16).next_to(wt, DOWN, 0.3).align_to(w.get_left() + RIGHT * 0.4, LEFT)
        self.play(FadeIn(root), FadeIn(iss), FadeIn(w), FadeIn(wt), run_time=0.7)
        ic = chip("issue", ACCENT, SOFT, 16).move_to(iss[1][0].get_right() + RIGHT * 0.3)
        self.play(ic.animate.move_to(w.get_left()), run_time=0.5)
        self.remove(ic)
        self.play(LaggedStart(*[FadeIn(c) for c in claims], lag_ratio=0.15), run_time=0.8)
        self.hold(1.0)

        # ── Bank B 要 kycLevel ≥ 2 → 只揭露 kycLevel，其他四項留在錢包 ──
        rps = VGroup()
        for i, nm in enumerate(("Bank B", "Securities C")):
            b = card(3.4, 1.0).move_to([self.x_right - 1.7, cy + 0.9 - i * 1.6, 0])
            rps.add(VGroup(b, VGroup(sans(nm, 19), mono("needs kycLevel ≥ 2", 16, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
                           .move_to(b.get_left() + RIGHT * 0.2, aligned_edge=LEFT)))
        self.play(FadeIn(rps), run_time=0.4)
        hidden = VGroup(*[mono("hidden", 16, MUTED).next_to(c, RIGHT, 0.3) for c in claims[:4]])
        self.play(*[c.animate.set_opacity(0.3) for c in claims[:4]], FadeIn(hidden), claims[4].animate.set_color(PASS), run_time=0.5)
        for r in rps:
            p = chip("kycLevel", PASS, BG, 16).move_to(claims[4].get_right() + RIGHT * 0.6)
            self.play(p.animate.move_to(r[0].get_left() + LEFT * 0.1), run_time=0.5)
            self.remove(p)
            tk = tick().move_to(r[0].get_right() + LEFT * 0.35)
            self.play(Create(tk), r[0].animate.set_stroke(PASS), run_time=0.3)
        kb = mono("✓ bound to the holder's key", 16, PASS).next_to(rps, DOWN, 0.25, aligned_edge=LEFT)
        self.play(FadeIn(kb), run_time=0.3)
        self.hold(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not self.chrome], run_time=0.5)

        # ── 第二幕：AI 防詐，風險 0–100，三段決策 ──
        lab = mono("AI ANTI-FRAUD · risk score 0–100", 16, LABEL).move_to([L, self.y_top - 0.2, 0], aligned_edge=LEFT)
        bw, by = 11.5, cy + 0.6
        x0 = L + 0.4
        segs = VGroup(*[Rectangle(width=bw * (b - a) / 100, height=0.4, stroke_width=0, fill_color=c, fill_opacity=0.35)
                        .move_to([x0 + bw * a / 100, by, 0], aligned_edge=LEFT)
                        for a, b, c in ((0, 40, PASS), (40, 70, WARN), (70, 100, REFUSE))])
        segl = VGroup(*[mono(t, 18, c).next_to(segs[i], DOWN, 0.18)
                        for i, (t, c) in enumerate((("pass  < 40", PASS), ("review  40–69", WARN), ("block  ≥ 70", REFUSE)))])
        self.play(FadeIn(lab), FadeIn(segs), FadeIn(segl), run_time=0.7)
        self.hold(1.2)
        examples = [("an everyday payment", 18, PASS, "pass"), ("an unusual pattern", 55, WARN, "review"),
                    ("account drained to a mule", 90, REFUSE, "block")]
        ptr = Triangle(fill_color=TEXT, fill_opacity=1, stroke_width=0).scale(0.13).rotate(PI).move_to([x0, by + 0.42, 0])
        self.add(ptr)
        tx = mono("", 18)
        res = mono("", 18)
        for name, v, col, dec in examples:
            ntx = mono("transfer: " + name, 20, TEXT).move_to([x0, by + 1.15, 0], aligned_edge=LEFT)
            nres = mono("→ " + dec, 22, col, BOLD).move_to([x0, by - 1.15, 0], aligned_edge=LEFT)
            self.play(FadeOut(tx), FadeOut(res), FadeIn(ntx), ptr.animate.move_to([x0 + bw * v / 100, by + 0.42, 0]), run_time=0.7)
            self.play(FadeIn(nres), run_time=0.3)
            self.hold(1.0)
            tx, res = ntx, nres
        stop = mono("block → the verifier rejects the transfer", 20, REFUSE).next_to(res, DOWN, 0.3, aligned_edge=LEFT)
        self.play(FadeIn(stop), run_time=0.4)
        self.outro()


# ═══ 5. PepeFi On-Chain CFD ═══════════════════════════════════════════════════
class PepeFi(ProjectScene):
    AWARD = "NCCU Capstone 2026 — Base Sepolia Testnet"
    TITLE = "PepeFi On-Chain CFD"
    TAGS = "Solidity · Foundry · RWA · x402"
    CAPTION = "RWA-referenced perps · credential-gated · reduce-only while the market is closed"
    DISCLOSURE = "Base Sepolia testnet · synthetic exposure · credential self-issued by the team"

    def construct(self):
        top = self.y_top - 0.75
        L = self.x_left
        # ── keeper 把公開市價推進受保護的 oracle；三個合成市場 ──
        kp = card(2.9, 1.45).move_to([L + 1.45, top, 0])
        kt = VGroup(mono("KEEPER · team bot", 16, LABEL), mono("GitHub Actions", 16, TEXT2), mono("→ guarded oracle", 16, ACCENT)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to(kp)
        mk = []
        ys = [[0, .2, .1, .5, .45, .8], [.3, .25, .45, .4, .6, .55], [.2, .7, .4, .9, .55, 1.0]]
        info = (("sETH", "crypto", "no pass needed", PASS), ("sGOLD", "RWA", "pass needed", WARN), ("sAAPL", "US equity", "market hours", PASS))
        for i, (sym, kind, st, col) in enumerate(info):
            b = card(3.05, 1.45).move_to([L + 4.6 + i * 3.2, top, 0])
            s = mono(sym, 20, TEXT, BOLD).move_to(b.get_corner(UL) + [0.2, -0.27, 0], aligned_edge=LEFT)
            k = mono(kind, 16, MUTED).move_to(b.get_corner(UR) + [-0.2, -0.27, 0], aligned_edge=RIGHT)
            pts = [b.get_left() + [0.25 + j * 0.5, -0.22 + ys[i][j] * 0.4, 0] for j in range(6)]
            ln = VMobject(stroke_color=ACCENT, stroke_width=2.6).set_points_as_corners(pts)
            stt = mono(st, 16, col).move_to(b.get_corner(DL) + [0.2, 0.22, 0], aligned_edge=LEFT)
            mk.append(VGroup(b, s, k, ln, stt))
        self.play(FadeIn(kp), FadeIn(kt), *[FadeIn(VGroup(m[0], m[1], m[2], m[4])) for m in mk], run_time=0.7)
        dot = Dot(kp.get_right(), 0.07, color=ACCENT)
        self.play(dot.animate.move_to(mk[0][0].get_left()), run_time=0.35)
        self.remove(dot)
        self.play(*[Create(m[3]) for m in mk], run_time=0.9)
        self.hold(1.0)

        # ── 下半：事件紀錄，一行一行停住 ──
        y0 = top - 1.35
        def entry(i, txt, why, ok):
            mark = (tick() if ok else cross()).move_to([L + 0.25, y0 - i * 0.68, 0])
            col = PASS if ok else REFUSE
            t1 = mono(txt, 18, TEXT).next_to(mark, RIGHT, 0.3).shift(UP * 0.12)
            t2 = mono(why, 16, col).next_to(t1, DOWN, 0.06, aligned_edge=LEFT)
            return VGroup(mark, t1, t2)

        log = [
            ("wallet without a pass · open sGOLD", "NotKycVerified — reverted on-chain", False, 1),
            ("with a qualified-investor VC · open sGOLD", "allowed (VC self-issued by the team)", True, 1),
            ("sAAPL · US market closed · open long", "refused: reduce-only until the market opens", False, 2),
            ("agent · inside its session limits", "margin/trade · budget · max leverage · expiry", True, None),
        ]
        shown = []
        for i, (a, b, ok, m) in enumerate(log):
            if m == 2:
                closed = mono("closed → reduce-only", 16, WARN).move_to(mk[2][4], aligned_edge=LEFT)
                self.play(Transform(mk[2][4], closed), mk[2][3].animate.set_stroke(MUTED), run_time=0.4)
            e = entry(i, a, b, ok)
            anim = [FadeIn(e, shift=RIGHT * 0.15)]
            if m is not None:
                anim.append(Indicate(mk[m][0], color=PASS if ok else REFUSE))
            self.play(*anim, run_time=0.5)
            self.hold(1.3)
            shown.append(e)
        # 超出 session 上限 → 擋下；付 0.01 USDC 買訊號
        self.play(*[FadeOut(e) for e in shown], run_time=0.3)
        e5 = entry(0, "agent · leverage above the session cap", "LeverageExceedsSessionCap — reverted", False)
        e6 = entry(1, "agent · GET /signals/:trader", "0.01 USDC (testnet) paid over x402", True)
        self.play(FadeIn(e5, shift=RIGHT * 0.15), run_time=0.5)
        self.hold(1.2)
        self.play(FadeIn(e6, shift=RIGHT * 0.15), run_time=0.5)
        self.outro()


# ═══ 6. RWA Real Estate Tokenization ═════════════════════════════════════════
class RWATokenization(ProjectScene):
    AWARD = "Blockchain Implementation"
    TITLE = "RWA Real Estate Tokenization"
    TAGS = "Solidity · Hardhat · ERC-3643-style"
    CAPTION = "identity is checked inside the token · rent split pro rata · each holder claims"
    DISCLOSURE = "local Hardhat network · sample data · mock USDC"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        cols = {"A": ACCENT, "B": PASS, "C": WARN, "D": MUTED}
        owner = ["A"] * 6 + ["B"] * 4 + ["C"] * 2

        # ── 建築：12 扇窗 = 12 個代幣單位，顏色代表持有人 ──
        body = card(2.5, 3.2, RULE, PANEL).move_to([self.x_left + 1.4, cy - 0.2, 0])
        roof = Polygon(body.get_corner(UL) + RIGHT * 0.05, body.get_top() + UP * 0.6, body.get_corner(UR) + LEFT * 0.05,
                       stroke_color=RULE, stroke_width=2, fill_color=PANEL2, fill_opacity=1)
        wins = VGroup(*[Rectangle(width=0.5, height=0.5, stroke_width=0, fill_color=cols[o], fill_opacity=0.8) for o in owner])
        wins.arrange_in_grid(4, 3, buff=0.2).move_to(body)
        cap = mono("PropertyToken (ERC-20) · 12 units", 16, TEXT2).next_to(body, DOWN, 0.2).align_to(body, LEFT)
        self.play(FadeIn(body), FadeIn(roof), LaggedStart(*[FadeIn(w) for w in wins], lag_ratio=0.05), FadeIn(cap), run_time=1.0)
        self.hold(0.8)

        # ── IdentityRegistry：owner 登記 A、B、C；D 沒登記 ──
        cx = -1.05
        reg = card(4.0, 2.0, ACCENT, SOFT).move_to([cx, cy + 1.05, 0])
        rt = mono("IdentityRegistry", 18).move_to(reg.get_corner(UL) + [0.2, -0.3, 0], aligned_edge=LEFT)
        call = mono("owner · registerIdentity(A, B, C)", 16, TEXT2).next_to(rt, DOWN, 0.12, aligned_edge=LEFT)
        letters = VGroup(*[mono(h, 20, TEXT, BOLD) for h in "ABCD"]).arrange(RIGHT, buff=0.75).move_to(reg.get_bottom() + UP * 0.65)
        self.play(FadeIn(reg), FadeIn(rt), FadeIn(call), FadeIn(letters), run_time=0.6)
        marks = {}
        for i, h in enumerate("ABC"):
            marks[h] = tick().scale(0.8).next_to(letters[i], DOWN, 0.12)
            self.play(Create(marks[h]), run_time=0.25)
        marks["D"] = mono("not registered", 16, MUTED).next_to(letters[3], DOWN, 0.12)
        self.play(FadeIn(marks["D"]), run_time=0.3)
        self.hold(0.8)

        # ── 右：持有人表 ──
        hx = 1.55
        hdr = VGroup(mono("HOLDER", 16, LABEL).move_to([hx, cy + 1.85, 0], aligned_edge=LEFT),
                     mono("UNITS", 16, LABEL).move_to([hx + 3.0, cy + 1.85, 0], aligned_edge=RIGHT),
                     mono("CLAIM", 16, LABEL).move_to([hx + 4.85, cy + 1.85, 0], aligned_edge=RIGHT))
        units = {"A": 6, "B": 4, "C": 2, "D": 0}
        rows, unum = {}, {}
        for i, h in enumerate("ABCD"):
            y = cy + 1.2 - i * 0.62
            sw = Square(0.22, stroke_width=0, fill_color=cols[h], fill_opacity=0.85).move_to([hx + 0.11, y, 0])
            rows[h] = VGroup(sw, mono(f"holder {h}", 18, TEXT2).next_to(sw, RIGHT, 0.2))
            unum[h] = mono(str(units[h]), 20).move_to([hx + 3.0, y, 0], aligned_edge=RIGHT)
        self.play(FadeIn(hdr), *[FadeIn(r) for r in rows.values()], *[FadeIn(u) for u in unum.values()], run_time=0.5)
        self.hold(0.6)

        # ── 轉讓 A→C：代幣合約在轉帳時查雙方身分 → 成功 ──
        above = reg.get_top() + UP * 0.28
        tok = chip("A → C · 1 unit", TEXT2, PANEL2).move_to(rows["A"][1].get_center())
        self.play(tok.animate.move_to(above), run_time=0.6)
        ok = mono("sender ✓  receiver ✓", 16, PASS).next_to(tok, LEFT, 0.25)
        self.play(FadeIn(ok), Indicate(letters[0], color=PASS), Indicate(letters[2], color=PASS), run_time=0.6)
        self.play(tok.animate.move_to(rows["C"][1].get_center()), FadeOut(ok), run_time=0.6)
        self.remove(tok)
        self.play(wins[5].animate.set_fill(WARN),
                  Transform(unum["A"], mono("5", 20, TEXT, BOLD).move_to(unum["A"], aligned_edge=RIGHT)),
                  Transform(unum["C"], mono("3", 20, TEXT, BOLD).move_to(unum["C"], aligned_edge=RIGHT)), run_time=0.5)
        self.hold(0.6)

        # ── 轉讓 A→D：D 沒登記 → 代幣合約自己 revert（合約原字） ──
        tok2 = chip("A → D · 1 unit", REFUSE).move_to(rows["A"][1].get_center())
        self.play(tok2.animate.move_to(above), run_time=0.6)
        rev = VGroup(mono("revert", 16, LABEL),
                     mono('"Receiver failed KYC/AML check"', 18, REFUSE, BOLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        rev.move_to([hx, cy - 1.45, 0], aligned_edge=LEFT)
        self.play(Wiggle(tok2), letters[3].animate.set_color(REFUSE), marks["D"].animate.set_color(REFUSE), FadeIn(rev), run_time=0.8)
        self.hold(2.0)
        self.play(FadeOut(tok2), FadeOut(rev), letters[3].animate.set_color(TEXT), marks["D"].animate.set_color(MUTED), run_time=0.4)

        # ── 租金：owner 存入 → 每單位 100 → 持有人各自 claimRent() ──
        dist = card(4.0, 1.75, ACCENT, SOFT).move_to([cx, cy - 1.25, 0])
        dt = mono("RentalDistributor", 18).move_to(dist.get_corner(UL) + [0.2, -0.3, 0], aligned_edge=LEFT)
        d1 = mono("owner · distributeRent(1,200)", 16, TEXT2).next_to(dt, DOWN, 0.14, aligned_edge=LEFT)
        d2 = mono("12 units → 100 per unit", 16, ACCENT).next_to(d1, DOWN, 0.12, aligned_edge=LEFT)
        self.play(FadeIn(dist), FadeIn(dt), FadeIn(d1), run_time=0.5)
        self.play(FadeIn(d2, shift=UP * 0.1), run_time=0.4)
        self.hold(0.8)
        for h, amt in (("A", 500), ("B", 400), ("C", 300)):
            c = chip("claimRent()", cols[h], BG, 16).move_to(rows[h][1].get_center())
            self.play(c.animate.move_to(dist.get_right() + LEFT * 0.9 + UP * 0.1), run_time=0.45)
            self.remove(c)
            amtm = mono(str(amt), 20, cols[h], BOLD).move_to([hx + 4.85, rows[h].get_y(), 0], aligned_edge=RIGHT)
            self.play(FadeIn(amtm, shift=LEFT * 0.15), run_time=0.3)
        self.play(FadeIn(mono("—", 20, MUTED).move_to([hx + 4.85, rows["D"].get_y(), 0], aligned_edge=RIGHT)), run_time=0.3)
        st = mono("rent settles before each transfer", 16, MUTED).move_to([hx, cy - 1.45, 0], aligned_edge=LEFT)
        self.play(FadeIn(st), run_time=0.4)
        self.outro()


# ═══ 7. QML Simulation ═══════════════════════════════════════════════════════
class QMLSimulation(ProjectScene):
    AWARD = "Quantum ML Study"
    TITLE = "QML Simulation"
    TAGS = "Qiskit · QSVM · QNN"
    CAPTION = "2×2 design: data source × model family → a data or a model advantage?"
    DISCLOSURE = "single-seed simulation · no saved results — shows the method, not an advantage"

    def construct(self):
        cy = (self.y_top + self.y_bot) / 2
        # ── 左：2×2 實驗設計 ──
        g0 = np.array([self.x_left + 2.45, cy + 0.55, 0])
        cells = VGroup()
        for i in range(2):
            for j in range(2):
                c = card(2.05, 1.15).move_to(g0 + [j * 2.15, -i * 1.25, 0])
                cells.add(VGroup(c, mono("LR" if j == 0 else "QSVM · QNN", 16, TEXT2).move_to(c)))
        colh = VGroup(*[mono(s, 16, TEXT2).next_to(cells[j], UP, 0.15) for j, s in enumerate(("classical", "quantum"))])
        rowh = VGroup(*[mono(s, 16, TEXT2).next_to(cells[i * 2], LEFT, 0.15) for i, s in enumerate(("classical", "quantum"))])
        axm = mono("model →", 16, MUTED).next_to(colh, UP, 0.12)
        axd = mono("data ↓", 16, MUTED).next_to(rowh, UP, 0.45).align_to(rowh, RIGHT)
        q = mono("data advantage or model advantage?", 16, ACCENT).next_to(cells, DOWN, 0.35).align_to(rowh, LEFT)
        self.play(FadeIn(cells), FadeIn(colh), FadeIn(rowh), FadeIn(axm), FadeIn(axd), run_time=0.7)
        self.play(FadeIn(q), run_time=0.4)
        self.hold(1.4)

        # 右側面板：依序說明「資料」與「模型」
        px = 2.95
        panel = card(6.9, 4.3, LINE, PANEL).move_to([px, cy + 0.05, 0])
        self.play(FadeIn(panel), run_time=0.3)

        def light(idx, on=True):
            return [cells[k][0].animate.set_stroke(ACCENT if on else LINE).set_fill(SOFT if on else PANEL) for k in idx]

        # ── 資料列 1：古典資料 make_moons ──
        h1 = label("classical data", 16).move_to(panel.get_corner(UL) + [0.3, -0.35, 0], aligned_edge=LEFT)
        rng = np.random.default_rng(42)
        c0 = panel.get_center() + DOWN * 0.15
        moons = VGroup()
        for k in range(70):
            t = rng.uniform(0, PI)
            if k % 2 == 0:
                x, y, col = np.cos(t), np.sin(t), ACCENT
            else:
                x, y, col = 1 - np.cos(t), 0.5 - np.sin(t), WARN
            x, y = x + rng.normal(0, 0.12), y + rng.normal(0, 0.12)
            moons.add(Dot(c0 + [(x - 0.5) * 1.9, (y - 0.25) * 1.7, 0], 0.05, color=col))
        mn = mono("make_moons · n = 320 · noise 0.18", 16, TEXT2).move_to(panel.get_corner(DL) + [0.3, 0.35, 0], aligned_edge=LEFT)
        self.play(*light([0, 1]), FadeIn(h1), LaggedStart(*[FadeIn(d) for d in moons], lag_ratio=0.01), FadeIn(mn), run_time=1.0)
        self.hold(1.6)

        # ── 資料列 2：量子資料：(α, β) → 雙量子位元電路 → 512 shots 的量測機率 ──
        h2 = label("quantum data", 16).move_to(h1, aligned_edge=LEFT)
        steps = VGroup(*[chip(s, ACCENT if k < 3 else TEXT2, BG, 16) for k, s in enumerate(
            ("random (α, β)", "2-qubit circuit · Aer", "4 measured probs · 512 shots", "label = f(α, β)"))])
        steps.arrange(DOWN, buff=0.38).move_to(panel.get_center() + DOWN * 0.1)
        arrows = VGroup(*[Arrow(steps[k].get_bottom(), steps[k + 1].get_top(), buff=0.05, stroke_width=2.4,
                                color=RULE, max_tip_length_to_length_ratio=0.35) for k in range(3)])
        self.play(*light([0, 1], False), *light([2, 3]), FadeOut(h1), FadeOut(moons), FadeOut(mn), FadeIn(h2), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.1) for s in steps], *[GrowArrow(a) for a in arrows], lag_ratio=0.25), run_time=1.3)
        self.hold(1.6)

        # ── 模型欄：ZZFeatureMap（reps=2）→ 保真度量子核 → QSVM；另有變分 QNN、QSVT-like ──
        h3 = label("quantum models", 16).move_to(h1, aligned_edge=LEFT)
        x0, y0 = panel.get_left()[0] + 0.5, panel.get_top()[1] - 1.05
        wires = VGroup(*[Line([x0, y0 - k * 0.6, 0], [x0 + 3.9, y0 - k * 0.6, 0], stroke_color=RULE) for k in range(2)])

        def gate(x, y, s, w=0.5):
            r = card(w, 0.4, ACCENT, BG).move_to([x, y, 0])
            return VGroup(r, mono(s, 14).move_to(r))
        ys = [y0, y0 - 0.6]
        circ = VGroup(*[gate(x0 + 0.4, y, "H") for y in ys], *[gate(x0 + 1.1, y, "P(x)", 0.7) for y in ys])
        for x in (x0 + 1.9, x0 + 2.9):
            circ.add(Line([x, ys[0], 0], [x, ys[1], 0], stroke_color=ACCENT, stroke_width=2.4),
                     Dot([x, ys[0], 0], 0.07, color=ACCENT),
                     Circle(0.12, stroke_color=ACCENT, stroke_width=2.4).move_to([x, ys[1], 0]))
        circ.add(gate(x0 + 2.4, ys[1], "P(φ)", 0.7))
        reps = mono("ZZFeatureMap · reps = 2", 16, TEXT2).next_to(wires, RIGHT, 0.25).shift(UP * 0.3)
        kern = mono("K(x, x′) = |⟨φ(x)|φ(x′)⟩|²", 18, ACCENT).next_to(wires, DOWN, 0.35, aligned_edge=LEFT)
        models = VGroup(mono("→ QSVM  (fidelity quantum kernel)", 16, TEXT),
                        mono("→ variational QNN  (RealAmplitudes)", 16, TEXT),
                        mono("→ QSVT-like approximation", 16, TEXT)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        models.next_to(kern, DOWN, 0.3, aligned_edge=LEFT)
        self.play(*light([2, 3], False), *light([1, 3]), FadeOut(h2), FadeOut(steps), FadeOut(arrows), FadeIn(h3), run_time=0.5)
        self.play(Create(wires), LaggedStart(*[FadeIn(m) for m in circ], lag_ratio=0.04), FadeIn(reps), run_time=0.9)
        self.play(FadeIn(kern), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in models], lag_ratio=0.3), run_time=0.9)
        self.hold(1.6)

        # ── 四格都跑同一套流程，但沒有存下結果 → 不畫誰贏 ──
        self.play(*light([1, 3], False), FadeOut(VGroup(h3, wires, circ, reps, kern, models)), run_time=0.4)
        h4 = label("all four cells", 16).move_to(h1, aligned_edge=LEFT)
        res = VGroup(mono("same split · seed 42", 18, TEXT2),
                     mono("accuracy printed when run", 18, TEXT2),
                     mono("no outputs saved in the notebook", 18, WARN)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        res.move_to(panel.get_center(), aligned_edge=None)
        self.play(FadeIn(h4), run_time=0.3)
        for k in range(4):
            acc = mono("acc —", 16, MUTED).next_to(cells[k][1], DOWN, 0.08)
            self.play(*light([k]), FadeIn(acc), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(r) for r in res], lag_ratio=0.35), run_time=0.9)
        self.outro()


SCENES = {
    "chainlens": ChainLens, "evidence-at-source": EvidenceAtSource, "medssi": MedSSI,
    "chaintrust": ChainTrust, "pepefi": PepeFi, "rwa-tokenization": RWATokenization,
    "qml-simulation": QMLSimulation,
}
