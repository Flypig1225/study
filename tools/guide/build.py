# -*- coding: utf-8 -*-
"""构建《立法位阶 · 批准 · 备案 · 审查》图解讲义 PDF。

    python3 tools/guide/build.py --font-dir /tmp/fonts -o 立法位阶-图解讲义.pdf
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.pdfgen import canvas  # noqa: E402
import guide_base as G  # noqa: E402
import pages_a as P  # noqa: E402

PAGES = [
    P.page_cover,            # 01 封面
    P.page_two_lineages,     # 02 两种上下级
    P.page_pyramid,          # 03 位阶金字塔
    P.page_same_name,        # 04 同名不同命
    P.page_approval,         # 05 批准
    P.page_filing,           # 06 备案
    P.page_filing_traps,     # 07 备案反直觉
    P.page_review_rules,     # 08 22/11/21
    P.page_exceptions,       # 09 三个例外
    P.page_master_table,     # 10 整表拆解
    P.page_matrix,           # 11 关系×位阶矩阵
    P.page_overview_map,     # 12 总思维导图
]


def build(out_path, font_dir):
    G.setup_fonts(font_dir)
    c = canvas.Canvas(out_path, pagesize=G.A4)
    c.setTitle("立法位阶 · 批准 · 备案 · 审查｜法硕宪法学图解讲义")
    c.setAuthor("study · 宪法学背诵讲义")
    c.setSubject("立法法：位阶金字塔、批准、备案、事后审查（第 98–109 条）")
    c.setKeywords("法硕,宪法,立法法,位阶,备案,审查,批准,22,11,21")
    P.TOTAL = len(PAGES)
    bottoms = []
    for i, fn in enumerate(PAGES, start=1):
        bottom = fn(c)
        bottoms.append((fn.__name__, round(bottom, 1)))
        c.showPage()
    c.save()
    return bottoms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font-dir", default="/tmp/fonts")
    ap.add_argument("-o", "--out", default="立法位阶-图解讲义.pdf")
    a = ap.parse_args()
    print(build(a.out, a.font_dir))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
