#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建《法基分析副本-合并版》（复核修订版＋吸收 (1) 顺位版四项增量）"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common_m import DocTheme, make_styles, build_doc
import content398m_a as A
import content398m_b as B
import content398m_c as C
import content398m_d as D
import content398m_e as E
import content398m_f as F

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, '法基分析副本-合并版.pdf')
TAGGED = os.path.join(ROOT, 'data', 'tagged.json')

th = DocTheme(accent='#8B0000', accent_dark='#4A0000', soft='#F7ECE2')
S = make_styles(th)

story = []
story += A.cover_story(th, S)
story += A.revision_notes(th, S)
story += A.part1(th, S)
story += B.part1b(th, S)
story += C.part2(th, S)
story += D.part3_criminal(th, S)
story += D.part3_criminal_a(th, S)
story += E.part3_civil_pre(th, S)
story += E.part3_civil(th, S)
story += E.part3_civil_a(th, S)
story += F.part4(th, S)
story += F.appendix_a(TAGGED, th, S)
story += F.appendix_b(th, S)

t0 = time.time()
build_doc(OUT, th, '2027 法硕（非法学）专业基础课（398）· 主观大题 · 合并版', story)
print(f'OK -> {OUT}  ({time.time()-t0:.1f}s)')
