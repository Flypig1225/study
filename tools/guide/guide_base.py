# -*- coding: utf-8 -*-
"""
生成《立法位阶 · 批准 · 备案 · 审查》图解讲义 PDF。

依赖：
    pip install reportlab
字体：
    Noto Sans SC（思源黑体），来源 google/fonts: ofl/notosanssc/NotoSansSC[wght].ttf
    用 fontTools 的 instancer 拆成 400 / 500 / 700 三个静态字重，放在 --font-dir 目录下，
    命名为 NotoSansSC-Regular.ttf / NotoSansSC-Medium.ttf / NotoSansSC-Bold.ttf。

用法：
    python3 tools/build_legislation_guide.py --font-dir /tmp/fonts -o 立法位阶-图解讲义.pdf
"""

import argparse
import os

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PW, PH = A4
M = 42.0
CW = PW - 2 * M

# ---------------------------------------------------------------- 配色
INK = HexColor("#1B2430")
INK2 = HexColor("#4A5568")
INK3 = HexColor("#7C8798")
NAVY = HexColor("#1F3A5F")
RED = HexColor("#A63D40")
GOLD = HexColor("#B8873B")
PAPER = HexColor("#FBF8F2")
PAPER2 = HexColor("#F3EEE3")
LINE = HexColor("#D9D2C3")
GREEN = HexColor("#3E6B5A")
WHITE = HexColor("#FFFFFF")

T_CONST = HexColor("#7B2D26")
T_LAW = HexColor("#A6462F")
T_ADMIN = HexColor("#C08333")
T_LOCAL = HexColor("#4E7A6C")
T_RULE = HexColor("#6E7A86")

F_REG = "SC"
F_MED = "SCM"
F_BOLD = "SCB"

NO_HEAD = "，。、；：？！）】》」』’”%·"
NO_TAIL = "（【《「『‘“"

_TOTAL_PAGES = [0]


# ---------------------------------------------------------------- 基础工具
def setup_fonts(font_dir):
    for name, fn in ((F_REG, "NotoSansSC-Regular.ttf"),
                     (F_MED, "NotoSansSC-Medium.ttf"),
                     (F_BOLD, "NotoSansSC-Bold.ttf")):
        pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, fn)))


def sw(s, font, size):
    return pdfmetrics.stringWidth(s, font, size)


def _tokens(s, font=F_REG, bfont=F_BOLD):
    """把 "**加粗**普通" 拆成 [(字符, 字体), ...]，\\n 用 (None,None) 标记换行。"""
    toks = []
    bold = False
    i = 0
    while i < len(s):
        if s.startswith("**", i):
            bold = not bold
            i += 2
            continue
        ch = s[i]
        if ch == "\n" or s[i:i+2] == "\\n":
            if s[i:i+2] == "\\n":
                i += 2
            else:
                i += 1
            toks.append((None, None))
            continue
        else:
            toks.append((ch, bfont if bold else font))
        i += 1
    return toks


def _hang_width(runs, size):
    """末尾悬挂标点不计入行宽（中文排版惯例）。"""
    tail = 0
    for txt, fnt in reversed(runs):
        if txt and txt[-1] in NO_HEAD:
            tail += sw(txt[-1], fnt, size)
            txt2 = txt[:-1]
            while txt2 and txt2[-1] in NO_HEAD:
                tail += sw(txt2[-1], fnt, size)
                txt2 = txt2[:-1]
            break
        break
    return tail


def wrap_rich(s, size, width, font=F_REG, bfont=F_BOLD, hang=True):
    """折行，返回 [ [(text, font), ...], ... ]。"""
    lines, cur, curw = [], [], 0.0
    for ch, fnt in _tokens(s, font, bfont):
        if ch is None:
            lines.append(cur)
            cur, curw = [], 0.0
            continue
        w = sw(ch, fnt, size)
        if curw + w <= width or not cur:
            cur.append((ch, fnt))
            curw += w
        elif ch in NO_HEAD:
            # 行首禁则：全角标点跟随本行（允许略微超出）
            cur.append((ch, fnt))
            curw += w
            lines.append(cur)
            cur, curw = [], 0.0
        else:
            if cur and cur[-1][0] in NO_TAIL and len(cur) > 1:
                moved = cur.pop()
                lines.append(cur)
                cur = [moved, (ch, fnt)]
                curw = sw(moved[0], moved[1], size) + w
            else:
                lines.append(cur)
                cur, curw = [(ch, fnt)], w
    lines.append(cur)

    # 后处理：若某行以全角标点开头，把它移到上一行末尾（行首禁则）
    for i in range(1, len(lines)):
        while lines[i] and lines[i][0][0] in NO_HEAD:
            moved = lines[i].pop(0)
            lines[i - 1].append(moved)

    out = []
    for ln in lines:
        # 合并同字体连续片段
        merged = []
        for ch, fnt in ln:
            if merged and merged[-1][1] == fnt:
                merged[-1] = (merged[-1][0] + ch, fnt)
            else:
                merged.append((ch, fnt))
        out.append(merged)
    return out


def wrap(s, font, size, width):
    return ["".join(t for t, _ in ln) for ln in wrap_rich(s, size, width, font, font)]


def text(c, x, y, s, size=9, color=INK, font=F_REG, align="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "l":
        c.drawString(x, y, s)
    elif align == "c":
        c.drawCentredString(x, y, s)
    else:
        c.drawRightString(x, y, s)
    return sw(s, font, size)


def draw_runs(c, x, y, runs, size, color, align="l"):
    total = sum(sw(t, f, size) for t, f in runs)
    if align == "c":
        x -= total / 2.0
    elif align == "r":
        x -= total
    c.setFillColor(color)
    for t, f in runs:
        c.setFont(f, size)
        c.drawString(x, y, t)
        x += sw(t, f, size)


def para(c, x, y, width, s, size=9, leading=None, color=INK, font=F_REG,
         align="l", check=True, bcolor=None):
    """从 y 开始向下排段落，返回下一行的基线 y。支持 **加粗** 与悬挂标点。"""
    leading = leading or size * 1.62
    lines = wrap_rich(s, size, width, font, F_BOLD)
    if check:
        for ln in lines:
            over = sum(sw(t, f, size) for t, f in ln) - _hang_width(ln, size)
            assert over <= width + 0.8, (
                "溢出 %.1f>%.1f: %s" % (over, width, "".join(t for t, _ in ln)))
    for k, ln in enumerate(lines):
        if bcolor:
            # 加粗部分换色
            for idx, (t, f) in enumerate(ln):
                if f == F_BOLD:
                    ln[idx] = (t, f)
        draw_runs(c, x + (width / 2.0 if align == "c" else 0), y - k * leading,
                  ln, size, color, "c" if align == "c" else "l")
    return y - (len(lines) - 1) * leading - leading


def rrect(c, x, y, w, h, fill=None, stroke=None, r=5, lw=0.8, dash=None):
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    if dash:
        c.setDash(dash, 0)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke is not None else 0,
                fill=1 if fill is not None else 0)
    if dash:
        c.setDash([], 0)


def poly(c, pts, fill=None, stroke=None, lw=0.8):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.drawPath(p, stroke=1 if stroke is not None else 0,
               fill=1 if fill is not None else 0)


def line(c, x1, y1, x2, y2, color=LINE, lw=0.8, dash=None):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    if dash:
        c.setDash(dash, 0)
    c.line(x1, y1, x2, y2)
    if dash:
        c.setDash([], 0)


def hline(c, x1, x2, y, color=LINE, lw=0.8, dash=None):
    line(c, x1, y, x2, y, color, lw, dash)


def arrow_head(c, x, y, dx, dy, color, size=4.2):
    """在 (x,y) 处画一个指向 (dx,dy) 方向的箭头。"""
    import math
    ang = math.atan2(dy, dx)
    a1 = ang + math.radians(150)
    a2 = ang - math.radians(150)
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + size * math.cos(a1), y + size * math.sin(a1))
    p.lineTo(x + size * math.cos(a2), y + size * math.sin(a2))
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1)


def badge(c, x, y, s, size=7.5, bg=NAVY, fg=WHITE, padx=5, h=13, font=F_MED):
    w = sw(s, font, size) + 2 * padx
    rrect(c, x, y, w, h, fill=bg, r=h / 2.0)
    text(c, x + w / 2.0, y + (h - size) / 2.0 + 1.0, s, size, fg, font, "c")
    return w


def tag_row(c, x, y, items, size=7.6, gap=4, bg=PAPER2, fg=INK2):
    """一行内联标签，返回结束 x。"""
    cx = x
    for it in items:
        w = sw(it, F_REG, size) + 10
        rrect(c, cx, y, w, 13.5, fill=bg, r=2.2)
        text(c, cx + 5, y + 4.2, it, size, fg, F_REG)
        cx += w + gap
    return cx


def header(c, title, kicker=None):
    y = PH - 44
    text(c, M, y, title, 11.5, NAVY, F_BOLD)
    if kicker:
        text(c, PW - M, y, kicker, 8, INK3, F_REG, "r")
    hline(c, M, PW - M, y - 8, GOLD, 1.1)


def footer(c, page, total):
    text(c, M, 26, "立法位阶 · 批准 · 备案 · 审查　｜　法硕（非法学）背诵讲义", 7.2, INK3)
    text(c, PW - M, 26, "%02d / %02d" % (page, total), 7.6, INK3, F_MED, "r")


def page_bg(c, tint=PAPER):
    c.setFillColor(tint)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)


def sec_title(c, x, y, num, title, sub=""):
    c.setFillColor(NAVY)
    c.circle(x + 8, y + 4, 8.2, stroke=0, fill=1)
    text(c, x + 8, y + 1.4, str(num), 8.6, WHITE, F_BOLD, "c")
    text(c, x + 23, y, title, 14, NAVY, F_BOLD)
    if sub:
        text(c, x + 23 + sw(title, F_BOLD, 14) + 8, y + 1.5, sub, 8.4, INK3)
    return y - 18


def mix(c1, c2, t):
    return Color(c1.red + (c2.red - c1.red) * t,
                 c1.green + (c2.green - c1.green) * t,
                 c1.blue + (c2.blue - c1.blue) * t)


def table(c, x, y_top, cols, header, rows, fs=7.4, pad=5.2, lh=1.5,
          header_bg=NAVY, header_fg=WHITE, header_fs=None, row_tints=None,
          first_col_font=F_MED, first_col_color=INK, grid=LINE, zebra=True,
          align=None, row_colors=None, line_color=INK2):
    """通用表格：富文本折行、按内容算行高。返回表格底部 y。"""
    header_fs = header_fs or fs
    ncol = len(cols)
    total_w = sum(cols)
    heights, cell_lines = [], []
    for r in rows:
        ls = [wrap_rich(str(v), fs, cols[i] - 2 * pad,
                        first_col_font if i == 0 else F_REG, F_BOLD)
              for i, v in enumerate(r)]
        cell_lines.append(ls)
        heights.append(max(len(l) for l in ls) * fs * lh + 2 * pad)
    hh = max(len(wrap_rich(h, header_fs, cols[i] - 2 * pad, F_MED, F_BOLD))
             for i, h in enumerate(header)) * header_fs * lh + 2 * pad + 2

    y = y_top
    c.setFillColor(header_bg)
    c.rect(x, y - hh, total_w, hh, stroke=0, fill=1)
    cx = x
    for i, h in enumerate(header):
        lines = wrap_rich(h, header_fs, cols[i] - 2 * pad, F_MED, F_BOLD)
        ty = y - hh / 2.0 + (len(lines) - 1) * header_fs * lh / 2.0 - header_fs * 0.35
        for k, ln in enumerate(lines):
            draw_runs(c, cx + cols[i] / 2.0, ty - k * header_fs * lh, ln,
                      header_fs, header_fg, "c")
        cx += cols[i]
    y -= hh

    for ri, r in enumerate(rows):
        rh = heights[ri]
        if row_tints and row_tints[ri] is not None:
            c.setFillColor(row_tints[ri])
            c.rect(x, y - rh, total_w, rh, stroke=0, fill=1)
        elif zebra and ri % 2 == 1:
            c.setFillColor(mix(PAPER, PAPER2, 0.55))
            c.rect(x, y - rh, total_w, rh, stroke=0, fill=1)
        cx = x
        for i, v in enumerate(r):
            lines = cell_lines[ri][i]
            block_h = len(lines) * fs * lh
            ty = y - (rh - block_h) / 2.0 - fs * 0.72
            al = align[i] if align and i < len(align) else "l"
            col = first_col_color if i == 0 else INK2
            if row_colors and row_colors[ri] is not None:
                col = row_colors[ri]
            for k, ln in enumerate(lines):
                if al == "c":
                    draw_runs(c, cx + cols[i] / 2.0, ty - k * fs * lh, ln, fs, col, "c")
                else:
                    draw_runs(c, cx + pad, ty - k * fs * lh, ln, fs, col, "l")
            cx += cols[i]
        y -= rh
        hline(c, x, x + total_w, y, grid, 0.5)

    bottom = y
    cx = x
    for i in range(ncol + 1):
        line(c, cx, bottom, cx, y_top, grid, 0.6)
        if i < ncol:
            cx += cols[i]
    line(c, x, y_top, x + total_w, y_top, grid, 0.6)
    return bottom



# ================================================================ 通用局部元件
def numbox(c, x, y, s, size=9, bg=NAVY, fg=WHITE, d=17):
    c.setFillColor(bg)
    c.circle(x, y + size * 0.34, d / 2.0, stroke=0, fill=1)
    text(c, x, y + size * 0.34 - size * 0.36, s, size, fg, F_BOLD, "c")


def stage(c, x, y, num, title, sub="", color=NAVY, width=None):
    """步骤标题：圆形数字 + 标题 + 小注。"""
    numbox(c, x + 9, y, str(num), 9.4, color, WHITE, 18)
    text(c, x + 24, y, title, 13.4, NAVY, F_BOLD)
    if sub:
        text(c, x + 24 + sw(title, F_BOLD, 13.4) + 9, y + 1.4, sub, 8.4, INK3)
    return y - 19


def callout(c, x, y, w, s, color=GOLD, size=8.7, title=None, bg=None,
            leading=None, pad=12):
    leading = leading or size * 1.62
    inner = max(40.0, w - 2 * pad - 4)
    lines = wrap_rich(s, size, inner)
    h = len(lines) * leading + (14 if title else 0) + 14
    rrect(c, x, y - h, w, h, fill=bg or mix(PAPER2, WHITE, 0.45), stroke=None, r=4)
    rrect(c, x, y - h, 2.8, h, fill=color, r=1.4)
    yy = y - 15
    if title:
        text(c, x + pad, yy, title, 8.5, color, F_BOLD)
        yy -= 13
    para(c, x + pad, yy, inner, s, size, leading, INK2)
    return y - h


def pill(c, x, y, s, bg, fg=WHITE, size=7.4, h=14, padx=6, font=F_MED):
    w = sw(s, font, size) + 2 * padx
    rrect(c, x, y, w, h, fill=bg, r=h / 2.0)
    text(c, x + w / 2.0, y + (h - size) / 2.0 + 1.2, s, size, fg, font, "c")
    return w


def dotted(c, x1, y1, x2, y2, color=INK3, lw=0.9):
    line(c, x1, y1, x2, y2, color, lw, [1.6, 2.2])




# ---------------------------------------------------------------- 复合元件
def bottom_note(c, s, color=NAVY):
    """页底「记住这一句」条，压到页脚上方。"""
    y = 44
    lines = wrap_rich(s, 8.4, CW - 96)
    h = len(lines) * 13 + 12
    rrect(c, M, y, CW, h, fill=mix(color, WHITE, 0.9), stroke=None, r=3)
    text(c, M + 10, y + h - 14, "记住这一句", 7.5, color, F_BOLD)
    para(c, M + 76, y + h - 14, CW - 90, s, 8.4, 13, INK2)
    return y + h


def quiz_box(c, y, items, title="自测 · 判断题", hint="先自己想，再看虚线下"):
    """页底自测：判断题 + 答案，按内容自适应高度。返回底部 y。"""
    text(c, M, y, title, 9.4, NAVY, F_BOLD)
    text(c, PW - M, y, hint, 7.3, INK3, F_REG, "r")
    y -= 13
    n = len(items)
    gap = 8
    bw = (CW - (n - 1) * gap) / n
    boxes = []
    for q, a in items:
        ql = wrap_rich(q, 8.1, bw - 40, F_MED)
        al = wrap_rich(a, 7.3, bw - 24)
        h = 15 + len(ql) * 12.2 + 9 + len(al) * 10.8 + 11
        boxes.append((ql, al, h))
    maxh = max(b[2] for b in boxes)
    for i, (ql, al, h) in enumerate(boxes):
        bx = M + i * (bw + gap)
        rrect(c, bx, y - maxh, bw, maxh, fill=WHITE, stroke=LINE, r=4)
        c.setFillColor(NAVY)
        c.circle(bx + 13, y - 13.4, 7.4, stroke=0, fill=1)
        text(c, bx + 13, y - 16.2, str(i + 1), 7.2, WHITE, F_BOLD, "c")
        for k, ln in enumerate(ql):
            draw_runs(c, bx + 25, y - 11 - k * 12.2, ln, 8.1, INK)
        sep_y = y - 15 - len(ql) * 12.2 - 3
        line(c, bx + 12, sep_y, bx + bw - 12, sep_y, LINE, 0.5, [1.4, 2])
        for k, ln in enumerate(al):
            draw_runs(c, bx + 12, sep_y - 13 - k * 10.8, ln, 7.3, INK2)
    return y - maxh - 9


def card(c, x, y, w, body, title=None, sub=None, color=NAVY, size=8,
         title_size=9.4, pad=12, leading=None):
    """标题＋可选副标题＋正文的自适应卡片，返回卡片底部 y。"""
    leading = leading or size * 1.65
    inner = w - 2 * pad
    ty = 0
    if title:
        ty += title_size * 1.5
    if sub:
        ty += sum(len(l) for l in wrap_rich(sub, 7.2, inner)) * 10.8 + 2
    bl = wrap_rich(body, size, inner)
    h = ty + len(bl) * leading + pad
    rrect(c, x, y - h, w, h, fill=WHITE, stroke=LINE, r=5)
    c.setFillColor(color)
    c.rect(x, y - h, w, 2.8, stroke=0, fill=1)
    yy = y - pad - title_size * 0.9
    if title:
        text(c, x + pad, yy, title, title_size, color, F_BOLD)
        yy -= title_size * 1.35
    if sub:
        for ln in wrap_rich(sub, 7.2, inner):
            draw_runs(c, x + pad, yy, ln, 7.2, INK3)
            yy -= 10.8
        yy -= 2
    for ln in bl:
        draw_runs(c, x + pad, yy, ln, size, INK2)
        yy -= leading
    return y - h
