# -*- coding: utf-8 -*-
"""公共构建器：2027 法硕（非法学）主观题·复核修订版 PDF 两本。
字体：PyMuPDF 内置 Droid Sans Fallback（Simplified CJK），已提取到 assets/DroidSansFallback.otc。
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether, HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_PATH = os.path.join(ROOT, 'assets', 'DroidSansFallback.otc')
pdfmetrics.registerFont(TTFont('DroidFB', FONT_PATH))
pdfmetrics.registerFont(TTFont('DroidFB-Bold', FONT_PATH))   # 单一字重：粗体以颜色/字号区分
pdfmetrics.registerFontFamily('DroidFB', normal='DroidFB', bold='DroidFB-Bold',
                              italic='DroidFB', boldItalic='DroidFB-Bold')

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 15*mm, 15*mm, 15*mm, 15*mm
CONTENT_W = PAGE_W - ML - MR

class DocTheme:
    def __init__(self, accent, accent_dark, soft, gold='#B8860B'):
        self.accent = colors.HexColor(accent)
        self.accent_dark = colors.HexColor(accent_dark)
        self.soft = colors.HexColor(soft)
        self.gold = colors.HexColor(gold)
        self.ink = colors.HexColor('#212529')
        self.sub = colors.HexColor('#6B7280')
        self.line = colors.HexColor('#D8D2C4')
        self.card = colors.HexColor('#FBF8EF')
        self.grey = colors.HexColor('#F2F0EA')

def make_styles(th):
    S = {}
    S['body'] = ParagraphStyle('body', fontName='DroidFB', fontSize=9, leading=13.2,
                               textColor=th.ink, spaceAfter=3.2, alignment=TA_LEFT)
    S['bodyL'] = ParagraphStyle('bodyL', fontName='DroidFB', fontSize=9, leading=13.2,
                                textColor=th.ink, spaceAfter=3.2, alignment=TA_LEFT)
    S['small'] = ParagraphStyle('small', fontName='DroidFB', fontSize=7.6, leading=10.5,
                                textColor=th.sub, spaceAfter=2)
    S['h1'] = ParagraphStyle('h1', fontName='DroidFB-Bold', fontSize=16.5, leading=21,
                             textColor=th.accent_dark, spaceBefore=10, spaceAfter=6)
    S['h2'] = ParagraphStyle('h2', fontName='DroidFB-Bold', fontSize=12.5, leading=16.5,
                             textColor=th.accent, spaceBefore=9, spaceAfter=4.5)
    S['h3'] = ParagraphStyle('h3', fontName='DroidFB-Bold', fontSize=10, leading=14.5,
                             textColor=th.accent_dark, spaceBefore=6, spaceAfter=3)
    S['bullet'] = ParagraphStyle('bullet', fontName='DroidFB', fontSize=8.8, leading=12.6,
                                 textColor=th.ink, leftIndent=11, bulletIndent=2, spaceAfter=2.2)
    S['cell'] = ParagraphStyle('cell', fontName='DroidFB', fontSize=7.6, leading=10.4, textColor=th.ink)
    S['cellB'] = ParagraphStyle('cellB', fontName='DroidFB-Bold', fontSize=7.6, leading=10.4, textColor=th.accent_dark)
    S['cellH'] = ParagraphStyle('cellH', fontName='DroidFB-Bold', fontSize=7.9, leading=10.6, textColor=colors.white)
    S['quote'] = ParagraphStyle('quote', fontName='DroidFB', fontSize=8.6, leading=12.2,
                                textColor=th.accent_dark, backColor=th.soft, borderColor=th.accent,
                                borderWidth=0.7, borderPadding=5, leftIndent=2, rightIndent=2, spaceAfter=5)
    S['card'] = ParagraphStyle('card', fontName='DroidFB', fontSize=8.6, leading=12.4,
                               textColor=th.ink, backColor=th.card, borderColor=th.line,
                               borderWidth=0.7, borderPadding=6, leftIndent=2, rightIndent=2, spaceAfter=5)
    S['title'] = ParagraphStyle('title', fontName='DroidFB-Bold', fontSize=25, leading=33,
                                textColor=colors.white, alignment=TA_CENTER)
    S['subtitle'] = ParagraphStyle('subtitle', fontName='DroidFB', fontSize=11.5, leading=17,
                                   textColor=colors.HexColor('#F3E9DD'), alignment=TA_CENTER)
    S['covermeta'] = ParagraphStyle('covermeta', fontName='DroidFB', fontSize=9, leading=13,
                                    textColor=colors.HexColor('#D9CFC1'), alignment=TA_CENTER)
    return S

def _on_page(canvas, doc, th, short_title):
    canvas.saveState()
    canvas.setStrokeColor(th.accent)
    canvas.setLineWidth(0.9)
    canvas.line(ML, PAGE_H - 11.5*mm, PAGE_W - MR, PAGE_H - 11.5*mm)
    canvas.setFont('DroidFB', 7.5)
    canvas.setFillColor(th.sub)
    canvas.drawString(ML, PAGE_H - 9.2*mm, short_title)
    canvas.drawRightString(PAGE_W - MR, PAGE_H - 9.2*mm, 'Flypig1225 · 2027 复核修订版')
    canvas.setStrokeColor(th.line)
    canvas.setLineWidth(0.5)
    canvas.line(ML, 10.5*mm, PAGE_W - MR, 10.5*mm)
    canvas.drawString(ML, 6.8*mm, '数据：2005–2026 真题逐题结构化校验（data/tagged.json）')
    canvas.drawRightString(PAGE_W - MR, 6.8*mm, f'第 {canvas.getPageNumber()} 页')
    canvas.restoreState()

def _on_cover(canvas, doc, th):
    canvas.saveState()
    canvas.setFillColor(th.accent_dark)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(th.accent)
    canvas.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas.rect(0, 0, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#F3E9DD'))
    canvas.setFont('DroidFB-Bold', 10)
    canvas.drawCentredString(PAGE_W/2, PAGE_H - 5.4*mm, '2 0 2 7   考 研   ·   复 核 修 订 版')
    canvas.setFont('DroidFB', 9)
    canvas.drawCentredString(PAGE_W/2, 3.2*mm, 'Flypig1225 · 2027 复核修订版 · 与原押题 PDF 对照使用')
    canvas.restoreState()

def build_doc(filename, theme, short_title, story):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = BaseDocTemplate(filename, pagesize=A4, leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB,
                          title=short_title, author='Flypig1225',
                          creator='study repo · tools/predict_build')
    frame = Frame(ML, MB, CONTENT_W, PAGE_H - MT - MB, id='main',
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    cover_frame = Frame(ML, MB, CONTENT_W, PAGE_H - MT - MB, id='cover',
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    cover_tpl = PageTemplate(id='cover', frames=[cover_frame],
                             onPage=lambda d, c: _on_cover(d, c, theme))
    body_tpl = PageTemplate(id='body', frames=[frame],
                            onPage=lambda d, c: _on_page(d, c, theme, short_title))
    doc.addPageTemplates([cover_tpl, body_tpl])
    doc.build(story)
    return filename

# ---------- 小工具 ----------
def P(text, style): return Paragraph(text, style)
def B(items, style, mark='◆', mark_color='#8B0000'):
    return [Paragraph(f'<bullet><font color="{mark_color}">{mark}</font></bullet>{t}', style) for t in items]

def table(headers, rows, widths, style_header_fill, S, repeatRows=1):
    data = [[Paragraph(h, S['cellH']) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), S['cell']) for c in r])
    t = Table(data, colWidths=widths, repeatRows=repeatRows, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), style_header_fill),
        ('GRID', (0,0), (-1,-1), 0.5, S['line'] if 'line' in S else colors.HexColor('#D8D2C4')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.6), ('BOTTOMPADDING', (0,0), (-1,-1), 2.6),
        ('LEFTPADDING', (0,0), (-1,-1), 3.4), ('RIGHTPADDING', (0,0), (-1,-1), 3.4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FAF8F2')]),
    ]))
    return t

def hr(th): return HRFlowable(width='100%', thickness=0.7, color=th.line, spaceBefore=2, spaceAfter=6)
