# -*- coding: utf-8 -*-
"""把生成的 PDF 转成手机友好的单文件 HTML（图片内嵌 base64）。

    python3 tools/guide/make_html.py 立法位阶-批准-备案-审查-图解讲义.pdf -o 图解讲义.html
"""
import argparse
import base64
import os

import pymupdf

TITLES = [
    "封面：从「部门规章最大」这个误解说起",
    "① 先分清两种「上下级」：人大线 vs 政府线",
    "② 位阶金字塔：宪法 → 法律 → 行政法规 → 地方性法规 → 规章",
    "②-b 同名不同命：省级／市级、部门规章／政府规章",
    "③ 批准：批准当自己",
    "④ 备案：备案找上级",
    "④-b 备案的三个「反直觉」",
    "⑤ 事后审查：三个数字 22 / 11 / 21",
    "⑤-b 书上「三个例外」逐条翻译",
    "⑥ 整表拆解：书上那张表一行不落",
    "⑦ 关系 × 位阶 对照矩阵",
    "⑧ 总思维导图 ＋ 考前 5 分钟速查",
]

HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>立法位阶 · 批准 · 备案 · 审查｜法硕宪法学图解讲义</title>
<style>
  :root{--paper:#FBF8F2;--ink2:#4A5568;--navy:#1F3A5F;--line:#D9D2C3;}
  *{box-sizing:border-box}
  body{margin:0;background:#EDE7DB;color:#1B2430;
       font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei","Hiragino Sans GB",system-ui,sans-serif;
       -webkit-text-size-adjust:100%}
  header{max-width:920px;margin:0 auto;padding:22px 16px 6px}
  h1{font-size:20px;margin:0 0 6px;color:var(--navy);letter-spacing:.02em}
  .sub{font-size:13px;color:var(--ink2);line-height:1.65}
  .bar{max-width:920px;margin:12px auto 0;padding:0 16px;display:flex;gap:10px;flex-wrap:wrap}
  .bar a{font-size:13.5px;text-decoration:none;color:#fff;background:var(--navy);
         padding:9px 15px;border-radius:999px}
  .bar a.alt{background:#fff;color:var(--navy);border:1px solid var(--line)}
  main{max-width:920px;margin:18px auto 56px;padding:0 16px}
  figure{margin:0 0 20px;background:var(--paper);border:1px solid var(--line);border-radius:10px;
         overflow:hidden;box-shadow:0 1px 3px rgba(27,36,48,.07)}
  figure img{display:block;width:100%;height:auto}
  figcaption{font-size:12.5px;color:#7C8798;padding:9px 13px;border-top:1px solid var(--line);
             display:flex;justify-content:space-between;gap:10px}
  footer{text-align:center;font-size:12px;color:#7C8798;padding:0 16px 44px;line-height:1.9}
  @media print{
    body{background:#fff}
    .bar,header,footer{display:none}
    figure{break-inside:avoid;page-break-inside:avoid;border:none;box-shadow:none;margin:0}
    main{max-width:none;margin:0;padding:0}
  }
</style>
</head>
<body>
<header>
  <h1>立法位阶 · 批准 · 备案 · 审查</h1>
  <div class="sub">法硕（非法学）宪法学 · 立法法 ｜ 12 页图解讲义<br>
  从「部门规章是不是最大的」讲到位阶金字塔，再到批准、备案、事后审查</div>
</header>
<div class="bar">
  <a href="__PDF__" download>↓ 下载 PDF（适合打印、做笔记）</a>
  <a class="alt" href="javascript:window.print()">打印本页</a>
</div>
<main>
"""

FOOT = """</main>
<footer>配套：2005–2026 法硕（非法学）真题 · 宪法学「立法法 / 国家机构」部分<br>
法条依据：《立法法》（2023 修正）第 82、85、98–101、107–109 条</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="图解讲义.html")
    ap.add_argument("--zoom", type=float, default=1.7)
    ap.add_argument("--quality", type=int, default=82)
    a = ap.parse_args()

    doc = pymupdf.open(a.pdf)
    parts = [HEAD.replace("__PDF__", os.path.basename(a.pdf))]
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(a.zoom, a.zoom))
        b64 = base64.b64encode(pix.tobytes("jpeg", jpg_quality=a.quality)).decode()
        title = TITLES[i] if i < len(TITLES) else "第 %d 页" % (i + 1)
        parts.append(
            '<figure><img src="data:image/jpeg;base64,%s" alt="%s">'
            '<figcaption><span>%s</span><span>%02d / %d</span></figcaption></figure>'
            % (b64, title, title, i + 1, len(doc)))
    parts.append(FOOT)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote %s (%.1f MB)" % (a.out, os.path.getsize(a.out) / 1e6))


if __name__ == "__main__":
    main()
