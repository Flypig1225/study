#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 2027押题总报告.md 渲染为 PDF（fpdf2 + Noto Sans SC 静态字体）。"""
import re, sys
from fpdf import FPDF

SRC = '押题回测/2027押题总报告.md'
DST = '2027法硕非法学大题押题报告.pdf'
# NOTE: 标题在 MD 首行

pdf = FPDF(format='A4')
pdf.set_margins(16, 16, 16)
pdf.set_auto_page_break(True, margin=18)
pdf.add_font('Noto', '', '/tmp/NotoSansSC-Regular.ttf')
pdf.add_font('Noto', 'B', '/tmp/NotoSansSC-Bold.ttf')
pdf.add_page()
W = pdf.w - pdf.l_margin - pdf.r_margin

def inline_text(x):
    """按 ** 加粗分段。返回 [(text, bold)]"""
    parts = re.split(r'\*\*(.+?)\*\*', x)
    out = []
    for i, p in enumerate(parts):
        if p == '': continue
        out.append((p, i % 2 == 1))
    return out or [('', False)]

def write_para(x, size=10.5, lh=5.6):
    pdf.set_font('Noto', '', size)
    for t, b in inline_text(x):
        pdf.set_font('Noto', 'B' if b else '', size)
        pdf.write(lh, t)
    pdf.ln(lh + 1)

from fpdf import FontFace

def write_table(rows):
    ncol = len(rows[0])
    # 列宽：按各列最长行内容估计，clamp 到 [0.6, 3.2] 相对比
    raw = []
    for col in zip(*rows):
        L = max(len(c) for c in col)
        raw.append(min(3.2, max(0.6, L / 14.0)))
    tot = sum(raw)
    widths = tuple(x / tot for x in raw)
    head = FontFace(family='Noto', size_pt=8.2, emphasis='BOLD', fill_color=(238, 238, 238))
    body = FontFace(family='Noto', size_pt=8.2)
    with pdf.table(col_widths=widths, text_align='LEFT', line_height=4.6,
                   borders_layout='ALL', padding=1.2,
                   headings_style=head) as table:
        for ri, row in enumerate(rows):
            r = table.row()
            for c in row:
                r.cell(c, style=body)

md = open(SRC).read()
lines = md.split('\n')
i = 0
first_h1 = True
while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if not s:
        i += 1; continue
    if s.startswith('|'):
        tbl = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            row = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-{3,}:?', c) for c in row):
                tbl.append(row)
            i += 1
        write_table(tbl); continue
    if s.startswith('# '):
        pdf.set_font('Noto', 'B', 17)
        pdf.multi_cell(W, 9, s[2:], align='C'); pdf.ln(4)
    elif s.startswith('## '):
        if pdf.get_y() > pdf.h - 60: pdf.add_page()
        pdf.set_draw_color(30, 30, 30)
        pdf.set_font('Noto', 'B', 13.5)
        pdf.set_text_color(0, 0, 0)
        y0 = pdf.get_y()
        pdf.multi_cell(W, 7.5, ' ' + s[3:])
        pdf.set_line_width(0.5); pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + W, pdf.get_y())
        pdf.ln(3.5)
    elif s.startswith('### '):
        if pdf.get_y() > pdf.h - 50: pdf.add_page()
        pdf.set_font('Noto', 'B', 11.5); pdf.set_text_color(20, 40, 90)
        pdf.multi_cell(W, 6.5, s[4:]); pdf.set_text_color(0, 0, 0); pdf.ln(1)
    elif s.startswith('> '):
        pdf.set_font('Noto', '', 8.8); pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(W, 4.6, s[2:]); pdf.set_text_color(0, 0, 0); pdf.ln(2)
    elif s == '---':
        pdf.ln(2)
    elif s.startswith('- '):
        x = pdf.l_margin + 4
        pdf.set_x(x); write_para('• ' + s[2:], 10.2, 5.4)
        pdf.set_x(pdf.l_margin)
    elif re.match(r'^\d+\.\s', s):
        m = re.match(r'^(\d+)\.\s(.*)$', s)
        x = pdf.l_margin + 3
        pdf.set_x(x); write_para(f"{m.group(1)}. {m.group(2)}", 10.2, 5.4)
        pdf.set_x(pdf.l_margin)
    else:
        if pdf.get_y() > pdf.h - 30: pdf.add_page()
        write_para(s)
    i += 1

# 页脚页码
pdf.output(DST)
print('PDF 已生成:', DST)
