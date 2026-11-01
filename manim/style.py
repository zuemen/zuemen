"""
共用風格：與 zuemen.net（src/app/globals.css）同一套色票與字體

所有專案場景都繼承 ProjectScene：
  - 上方：獎項小標（字距拉開）＋ 襯線標題 ＋ 右上技術標籤
  - 下方：一句「機制說明」
  - 中間：各場景自己畫
"""
from manim import *

# ── 網站 design tokens ──────────────────────────────────────────────────────
BG = "#0a0a0b"
PANEL = "#111114"
PANEL2 = "#17171c"
LINE = "#222228"
RULE = "#34343b"
TEXT = "#ecebe6"
TEXT2 = "#a6a59f"
MUTED = "#8a8a93"
LABEL = "#8f8e88"
ACCENT = "#9bb6d8"
SOFT = "#141b24"
PASS = "#8cc9a1"
REFUSE = "#f0907a"
WARN = "#e3c07a"

SERIF = "Newsreader"
SANS = "IBM Plex Sans"
MONO = "JetBrains Mono"

config.background_color = BG


# ── 文字 ───────────────────────────────────────────────────────────────────
def mono(s, size=20, color=TEXT, weight=NORMAL):
    """等寬字：標籤、數值、程式相關"""
    return Text(s, font=MONO, font_size=size, color=color, weight=weight)


def sans(s, size=24, color=TEXT, weight=NORMAL):
    """內文無襯線字"""
    return Text(s, font=SANS, font_size=size, color=color, weight=weight)


def serif(s, size=48, color=TEXT):
    """標題襯線字"""
    return Text(s, font=SERIF, font_size=size, color=color)


def live_num(tracker, fmt="{:.2f}", size=26, color=TEXT, color_fn=None, place=None):
    """隨 ValueTracker 變動的等寬數字（取代 DecimalNumber，避免 LaTeX 字體跟網站不一致）
    place(m) 負責每一幀把數字擺回正確位置"""
    def make():
        v = tracker.get_value()
        m = mono(fmt.format(v), size, color_fn(v) if color_fn else color)
        if place:
            place(m)
        return m
    return always_redraw(make)


def label(s, size=16, color=LABEL):
    """全大寫小標（網站的 label 樣式）"""
    return Text(s.upper(), font=MONO, font_size=size, color=color)


# ── 形狀 ───────────────────────────────────────────────────────────────────
def card(w, h, stroke=LINE, fill=PANEL, sw=1.6):
    """網站的面板：近乎直角、細邊框"""
    return RoundedRectangle(width=w, height=h, corner_radius=0.04,
                            stroke_color=stroke, stroke_width=sw,
                            fill_color=fill, fill_opacity=1)


def chip(s, color=ACCENT, fill=BG, size=17):
    """小標籤：細框 + 等寬字"""
    t = mono(s, size, color)
    r = RoundedRectangle(width=t.width + 0.36, height=t.height + 0.26, corner_radius=0.04,
                         stroke_color=color, stroke_width=1.6, fill_color=fill, fill_opacity=1)
    return VGroup(r, t.move_to(r))


def tick(color=PASS, s=0.22):
    """打勾"""
    return VMobject(stroke_color=color, stroke_width=4).set_points_as_corners(
        [[-s, 0, 0], [-s * 0.3, -s * 0.7, 0], [s, s * 0.8, 0]])


def cross(color=REFUSE, s=0.18):
    """打叉"""
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 4)


def node(r=0.16, stroke=RULE, fill=PANEL):
    return Circle(radius=r, stroke_color=stroke, stroke_width=2.4, fill_color=fill, fill_opacity=1)


# ── 場景基底 ───────────────────────────────────────────────────────────────
class ProjectScene(Scene):
    """所有專案動畫共用的版型"""
    AWARD = ""
    TITLE = ""
    TAGS = ""
    CAPTION = ""

    def setup(self):
        top = config.frame_height / 2
        left = -config.frame_width / 2 + 0.55
        right = config.frame_width / 2 - 0.55

        aw = mono(self.AWARD.upper(), 17, LABEL).to_corner(UL, buff=0.55)
        tg = mono(self.TAGS, 17, MUTED).to_corner(UR, buff=0.55)
        tt = serif(self.TITLE, 54).next_to(aw, DOWN, buff=0.22, aligned_edge=LEFT)
        rule_top = Line([left, tt.get_bottom()[1] - 0.25, 0], [right, tt.get_bottom()[1] - 0.25, 0],
                        stroke_color=LINE, stroke_width=1.6)
        cap = mono(self.CAPTION, 18, MUTED).to_corner(DL, buff=0.5)
        rule_bot = Line([left, cap.get_top()[1] + 0.25, 0], [right, cap.get_top()[1] + 0.25, 0],
                        stroke_color=LINE, stroke_width=1.6)
        self.chrome = VGroup(aw, tg, tt, rule_top, rule_bot, cap)
        self.add(self.chrome)
        # 內容區的上下界，給子類別排版用
        self.y_top = rule_top.get_y() - 0.2
        self.y_bot = rule_bot.get_y() + 0.2

    def outro(self, *keep):
        """結尾：停一下再淡出內容（標題框留著），讓 GIF 首尾銜接"""
        self.wait(1.4)
        rest = [m for m in self.mobjects if m is not self.chrome and m not in keep]
        self.play(*[FadeOut(m) for m in rest], run_time=0.6)
        self.wait(0.2)
