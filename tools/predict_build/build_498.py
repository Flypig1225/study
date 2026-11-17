#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建《2027 法硕（非法学）专业综合课（498）主观大题·规律分析与押题预测·复核修订版》"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DocTheme, make_styles, build_doc
import common498_a as A
import common498_b as B
import common498_c as C
import common498_d as D
import common498_e as E
import common498_f as F
import common498_g as G
import common498_h as H

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, '法综分析副本.pdf')
TAGGED = os.path.join(ROOT, 'data', 'zonghe', 'tagged.json')

th = DocTheme(accent='#0F4C3A', accent_dark='#06231B', soft='#E9F2EC')   # 黛绿 · 宪法绿
S = make_styles(th)

story = []
story += A.cover_story(th, S)
story += A.revision_notes(th, S)
story += A.part1(th, S)
story += B.part2(th, S)
story += C.part3_jurisprudence_pre(th, S)
story += C.part3_jurisprudence(th, S)
story += D.part3_juris_a(th, S)
story += E.part3_constitution_pre(th, S)
story += E.part3_constitution(th, S)
story += E.part3_constitution_a(th, S)
story += F.part3_history_pre(th, S)
story += F.part3_history(th, S)
story += G.part3_history_a(th, S)
story += H.part5(th, S)
story += H.appendix_a(TAGGED, th, S)
story += H.appendix_b(th, S)

t0 = time.time()
build_doc(OUT, th, '2027 法硕（非法学）专业综合课（498）· 主观大题 · 复核修订版', story)
print(f'OK -> {OUT}  ({time.time()-t0:.1f}s)')
