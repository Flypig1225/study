#!/usr/bin/env python3
"""真题 PDF -> 纯文本提取器

策略：
1. 页面有干净的文字层（中文字符占比高、坏字符少）→ 直接抽取文本层
2. 文字层残缺（字体子集缺 ToUnicode）或整页为扫描图 → 渲染成图后 OCR
3. OCR 结果按"分栏感知"的阅读顺序重组（两栏试卷不会串行）
"""

import os
import re
import sys
import glob
import unicodedata

import pymupdf

CJK = re.compile(r'[\u4e00-\u9fff]')
DPI = 200


def text_quality(txt):
    """返回 (中文字数, 坏字符数)。坏字符 = 控制符/私用区字符。"""
    cjk = bad = 0
    for ch in txt:
        if '\u4e00' <= ch <= '\u9fff':
            cjk += 1
        elif (ord(ch) < 32 and ch not in '\n\r\t') or 0xe000 <= ord(ch) <= 0xf8ff:
            bad += 1
    return cjk, bad


def page_text_layer(page):
    t = page.get_text("text")
    cjk, bad = text_quality(t)
    return t, cjk, bad


def ocr_page(page, ocr):
    pix = page.get_pixmap(dpi=DPI)
    img = pix.tobytes("png")
    res, _ = ocr(img)
    if not res:
        return ""
    lines = []
    for box, txt, score in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        lines.append({
            "x0": min(xs), "x1": max(xs),
            "y": sum(ys) / len(ys),
            "h": max(ys) - min(ys),
            "t": txt.strip(),
        })
    return order_lines(lines, pix.width)


def order_lines(lines, page_width):
    """分栏感知排序：先判断左右分栏，再按栏内 y 排序。"""
    if not lines:
        return ""
    mid = page_width / 2
    left = [l for l in lines if (l["x0"] + l["x1"]) / 2 < mid * 0.92]
    right = [l for l in lines if (l["x0"] + l["x1"]) / 2 >= mid * 0.92]
    # 判据：两侧都占一定比例、且中线附近基本没有"跨栏长行"
    spanning = [l for l in lines if l["x0"] < mid * 0.75 and l["x1"] > mid * 1.25]
    two_col = (len(left) >= 6 and len(right) >= 6
               and len(spanning) <= max(2, 0.06 * len(lines)))
    if two_col:
        out = []
        for col in (left, right):
            col.sort(key=lambda l: l["y"])
            out.append("\n".join(l["t"] for l in col))
        return "\n".join(out)
    lines.sort(key=lambda l: (round(l["y"] / max(l["h"], 1)), l["x0"]))
    # 同一视觉行的多段合并
    rows, cur, cur_y = [], [], None
    for l in sorted(lines, key=lambda l: l["y"]):
        if cur_y is None or abs(l["y"] - cur_y) < max(l["h"], 10) * 0.6:
            cur.append(l)
            cur_y = l["y"] if cur_y is None else (cur_y + l["y"]) / 2
        else:
            rows.append(sorted(cur, key=lambda l: l["x0"]))
            cur, cur_y = [l], l["y"]
    if cur:
        rows.append(sorted(cur, key=lambda l: l["x0"]))
    return "\n".join(" ".join(l["t"] for l in r) for r in rows)


def extract(path, ocr=None):
    doc = pymupdf.open(path)
    parts = []
    stats = {"text_pages": 0, "ocr_pages": 0}
    for page in doc:
        t, cjk, bad = page_text_layer(page)
        if cjk >= 80 and bad <= cjk * 0.05:
            parts.append(t)
            stats["text_pages"] += 1
        else:
            if ocr is None:            # 按需加载 OCR 模型
                from rapidocr_onnxruntime import RapidOCR
                ocr = RapidOCR()
            parts.append(ocr_page(page, ocr))
            stats["ocr_pages"] += 1
    return "\n".join(parts), stats


def main():
    src_dir = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src_dir, "*.pdf")))
    need_ocr = len(sys.argv) > 3 and sys.argv[3] == "ocr"
    ocr = None
    if need_ocr:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        out = os.path.join(out_dir, base + ".txt")
        if os.path.exists(out) and os.path.getsize(out) > 500:
            print("skip", base)
            continue
        txt, st = extract(p, ocr)
        txt = unicodedata.normalize("NFKC", txt)
        with open(out, "w", encoding="utf-8") as f:
            f.write(txt)
        cjk, bad = text_quality(txt)
        print(f"{base[:40]:42} cjk={cjk:6} bad={bad:5} text_pages={st['text_pages']} ocr_pages={st['ocr_pages']}")


if __name__ == "__main__":
    main()
