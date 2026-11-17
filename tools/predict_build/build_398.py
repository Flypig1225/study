#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建《2027 法硕（非法学）专业基础课（398）主观大题·规律分析与押题预测·复核修订版》"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DocTheme, make_styles, build_doc
import content398_a as A
import content398_b as B
import content398_c as C
import content398_d as D
import content398_e as E
import content398_f as F

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, '法基分析副本.pdf')
TAGGED = os.path.join(ROOT, 'data', 'tagged.json')

th = DocTheme(accent='#8B0000', accent_dark='#4A0000', soft='#F7ECE2')   # 暗红 · 司法红
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
build_doc(OUT, th, '2027 法硕（非法学）专业基础课（398）· 主观大题 · 复核修订版', story)
print(f'OK -> {OUT}  ({time.time()-t0:.1f}s)')
