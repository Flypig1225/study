# -*- coding: utf-8 -*-
"""把生成的 PDF 切成按页 JPG，用于 legislation.html 的懒加载展示。

    python3 tools/guide/make_html.py legislation-guide.pdf --outdir legislation

为什么不用「单文件 base64 内嵌」：整份 12 页 base64 后接近 3 MB，
在手机、微信内置浏览器、以及部分预览器里会长时间白屏，看起来就像「打不开」。
改成独立 JPG + loading="lazy"，首屏只加载 1 张（约 95 KB）。
"""
import argparse
import os

import pymupdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--outdir", default="legislation")
    ap.add_argument("--zoom", type=float, default=1.55, help="渲染倍率，1.55 约 150 dpi")
    ap.add_argument("--quality", type=int, default=80)
    a = ap.parse_args()

    doc = pymupdf.open(a.pdf)
    os.makedirs(a.outdir, exist_ok=True)
    total = 0
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(a.zoom, a.zoom))
        path = os.path.join(a.outdir, "p%02d.jpg" % i)
        pix.save(path, jpg_quality=a.quality)
        total += os.path.getsize(path)
    print("%d pages -> %s/ (%.2f MB)" % (len(doc), a.outdir, total / 1e6))


if __name__ == "__main__":
    main()
