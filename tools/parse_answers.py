#!/usr/bin/env python3
"""解析 PDF -> data/answers.json（年份-题号 -> 答案 + 解析）

输入：materials/answer_text/<year>.txt（由 tools/extract_text.py 从解析 PDF 提取）
输出：data/answers.json + 控制台覆盖率报告
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_DIR = os.environ.get("ANS_TXT", os.path.join(ROOT, "materials", "answer_text"))
OUT = os.path.join(ROOT, "data", "answers.json")

LETTERS = "ABCD"


def norm(t):
    t = t.replace("\u00a0", " ")
    t = re.sub(r'[【〔\[\(（]\s*答\s*案\s*[】〕\]\)）l1!]?', "[答案]", t)
    t = re.sub(r'\[解析[l1!]?', "[解析]", t)
    t = t.replace("【", "[").replace("】", "]")
    t = t.replace("『", "[").replace("』", "]")
    t = t.replace("“", '"').replace("”", '"')
    t = re.sub(r"[ \t\u3000]+", " ", t)
    return t


def answer_section(t):
    """2005-2010 卷：前半是题目，后半才是答案解析。"""
    occ = [m.start() for m in re.finditer(r"答\s*案?\s*解\s*析", t)]
    if not occ:
        # 2010 卷标题写「真题答案详解」；只在文首出现才算标题，避免正文里的「详解」把小标题当成答案区
        occ = [m.start() for m in re.finditer(r"答\s*案?\s*详\s*解", t) if m.start() < 200]
    if len(occ) >= 2:
        return t[occ[-1]:]
    if occ:
        return t[occ[0]:]
    return t


def split_blocks(seg):
    """按行首题号切块；同一题号只保留第一次出现。"""
    seg = re.sub(r"(?m)^(\s*)(\d{1,2})\s+[lI](\s*[.、．,，:：])", r"\g<1>\g<2>1\g<3>", seg)  # "5 I." = 51
    seg = re.sub(r"(?m)^(\s*)[lI](\s*[.、．,，:：])", r"\g<1>1\g<2>", seg)  # OCR 的 "l." / "I." = 第 1 题
    ms = list(re.finditer(r"(?m)^\s*(\d(?:\s?\d)?)\s*[.、．,，:：]\s*", seg))
    blocks, seen = {}, set()
    for i, m in enumerate(ms):
        raw = re.sub(r"\s", "", m.group(1)).replace("l", "1").replace("I", "1")
        if not raw.isdigit():
            continue
        num = int(raw)
        if num in seen:
            continue
        seen.add(num)
        end = ms[i + 1].start() if i + 1 < len(ms) else len(seg)
        blocks[num] = seg[m.end():end]
    return blocks


HEAD_JUNK = re.compile(
    r"^\s*(?:[\[\(]?(?:答案|解析|考点|详解|命题思路|试题解析)[\]\)]?\s*[:：]?\s*)+")


def find_answer(body, qtype):
    """在一题的解析块里找答案字母。返回 (letters, 剩余解析文本)。"""
    head = body[:120]
    L = r"([A-D](?:\s*[、,，/和及]?\s*[A-D]){0,3})"
    pats = [
        r"\[答案\]\s*[:：]?[^A-Da-z\n]{0,4}" + L,
        r"^\s*" + L + r"\s*[\[\(【〔]",
        r"^\s*" + L + r"\s*(?:\n|$)",
        r"答\s*案\s*[:：]\s*" + L,
        r"(?:本题|该题|此题|此题中)?\s*(?:正确)?答案\s*(?:为|是|应选|选)\s*[:：]?\s*" + L,
        r"(?:故|因此|所以|综上)[^。；\n]{0,12}?(?:选|应选)\s*[:：]?\s*" + L,
        r"(?:应选|故选|选择|选)\s*" + L + r"(?![A-Za-z])",
    ]
    for scope in (head, body[:600], body):
        for p in pats:
            m = re.search(p, scope, re.M)
            if m:
                got = "".join(sorted(set(re.sub(r"[^A-D]", "", m.group(1)))))
                if qtype == "单项选择" and len(got) > 1:
                    continue
                if qtype == "多项选择" and len(got) < 2:
                    continue
                return got, m
    return None, None


def strip_marks(body, m):
    """把『1.【答案】B。[解析]』这类抬头去掉，只留解析正文。"""
    if m is None:
        return body.strip()
    if m.start() <= 40:                 # 答案在开头：从答案后开始
        t = body[m.end():]
        t = re.sub(r"^[\s。．.、,，:：\[\]【】()（）]*", "", t)
    else:                               # 答案在文末（"因此本题答案为C"）：整段都保留
        t = body
    t = re.sub(r"[\[\(【〔]\s*(?:解析|考点|详解|命题思路|评析)\s*[\]\)】〕]\s*[:：]?\s*", "", t)
    t = re.sub(r"(?m)^[\s。．.、,，:：\[\]【】()（）]*(?:解析|考点|详解)\s*[:：]?\s*", "", t)
    t = re.sub(r"^[\]\)】〕\s]+", "", t)
    lines = t.split("\n")
    if len(lines) > 1 and len(lines[0].strip()) <= 12 and lines[1].strip().startswith(lines[0].strip()):
        lines = lines[1:]                       # 去掉重复的「考点」小标题
    t = "\n".join(lines)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()



def parse_speed_table(t):
    """2023 卷：『选择题答案速查』是「题号行 + 答案行」的表格，题号 OCR 常错位，按位置对齐。"""
    i = t.find("答案速查")
    if i < 0:
        return {}
    seg = t[i:t.find("简答题", i) if t.find("简答题", i) > 0 else i + 1500]
    lines = [x.strip() for x in seg.split("\n") if x.strip()]
    out, pending = {}, None
    for ln in lines:
        toks = ln.split()
        if all(x.isdigit() for x in toks) and len(toks) >= 5:
            pending = toks
            continue
        if pending and all(re.fullmatch(r"[A-D]{1,4}", x) for x in toks) and len(toks) == len(pending):
            nums = [int(x) for x in pending]
            base = (min(nums) - 1) // 10 * 10 + 1
            clean = list(range(base, base + len(nums)))       # 以位置为准，抗 OCR 题号错位
            for n, a in zip(clean, toks):
                out[n] = "".join(sorted(set(a)))
            pending = None
    return out

def main():
    tagged_path = os.path.join(ROOT, "data", "tagged.json")
    tagged = json.load(open(tagged_path, encoding="utf-8"))
    expect = {}
    for q in tagged:
        if q["type"] in ("单项选择", "多项选择"):
            expect.setdefault(q["year"], {})[q["num"]] = q["type"]

    out, report = {}, {}
    for path in sorted(glob.glob(os.path.join(TXT_DIR, "*.txt"))):
        year = int(os.path.basename(path)[:-4])
        if year not in expect:
            continue
        raw = norm(open(path, encoding="utf-8").read())
        speed = parse_speed_table(raw)
        seg = answer_section(raw)
        blocks = split_blocks(seg)
        ok = miss = bad = 0
        for num, qtype in expect[year].items():
            body = blocks.get(num)
            if not body:
                if num in speed:
                    out[f"{year}-{num}"] = {"a": speed[num], "e": ""}
                    continue
                miss += 1
                continue
            letters, m = find_answer(body, qtype)
            if not letters:
                if num in speed:
                    out[f"{year}-{num}"] = {"a": speed[num], "e": strip_marks(body, None)[:1200]}
                    continue
                miss += 1
                continue
            ok += 1
            key = f"{year}-{num}"
            expl = strip_marks(body, m)
            out[key] = {"a": letters, "e": expl[:1200]}
        report[year] = (ok, len(expect[year]), miss)

    # 人工补录（OCR 表格/粘连行）优先
    manual_path = os.path.join(ROOT, "data", "answers_manual.json")
    if os.path.exists(manual_path):
        manual = json.load(open(manual_path, encoding="utf-8"))
        for k, v in manual.items():
            if k.startswith("_"):
                continue
            cur = out.setdefault(k, {})
            for kk, vv in v.items():
                if vv or kk not in cur:      # 人工值只在非空时覆盖，避免清掉已抽到的解析
                    cur[kk] = vv
        print(f"人工补录 {len(manual)} 条")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for y in sorted(expect):
        tot = len(expect[y])
        ok = sum(1 for n in expect[y] if f"{y}-{n}" in out)
        print(f"{'OK ' if ok == tot else '缺 '}{y}: {ok}/{tot}")
    print(f"合计 {len(out)} 条 -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
