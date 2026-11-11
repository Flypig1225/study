#!/usr/bin/env python3
"""把真题纯文本切成结构化题目：年份 / 科目 / 题型 / 题号 / 分值 / 题干 / 选项。

按年份使用真实的卷面结构表（2005-2017 旧版、2018 起新版），
不依赖标题顺序，避免 OCR 阅读顺序错乱导致的串题。

输出：data/questions.json
"""

import os
import re
import json
import glob

# (题型, 起始题号, 结束题号, 每题分值)
OLD_CRIMINAL = [("单项选择", 1, 20, 1), ("多项选择", 21, 25, 2), ("简答", 26, 27, 6),
                ("辨析", 28, 28, 8), ("法条分析", 29, 29, 10), ("案例分析", 30, 30, 15)]
OLD_CIVIL = [("单项选择", 31, 50, 1), ("多项选择", 51, 55, 2), ("简答", 56, 57, 6),
             ("辨析", 58, 58, 8), ("法条分析", 59, 59, 10), ("案例分析", 60, 60, 15)]
MID_CRIMINAL = [("单项选择", 1, 20, 1), ("多项选择", 41, 45, 2), ("简答", 51, 52, 6),
                ("辨析", 55, 55, 8), ("法条分析", 57, 57, 10), ("案例分析", 59, 59, 15)]
MID_CIVIL = [("单项选择", 21, 40, 1), ("多项选择", 46, 50, 2), ("简答", 53, 54, 6),
             ("辨析", 56, 56, 8), ("法条分析", 58, 58, 10), ("案例分析", 60, 60, 15)]
NEW_CRIMINAL = [("单项选择", 1, 20, 1), ("多项选择", 41, 45, 2), ("简答", 51, 52, 10),
                ("法条分析", 55, 55, 10), ("案例分析", 57, 57, 15)]
NEW_CIVIL = [("单项选择", 21, 40, 1), ("多项选择", 46, 50, 2), ("简答", 53, 54, 10),
             ("法条分析", 56, 56, 10), ("案例分析", 58, 58, 15)]


def structure(year):
    """返回 {题号: (科目, 题型, 分值)}"""
    table = {}
    if year <= 2010:            # 早期：60 题，六种题型各两套
        spec_c, spec_m = OLD_CRIMINAL, OLD_CIVIL
    elif year <= 2017:          # 中期：40 单选 + 多选 + 简答/辨析/法条/案例
        spec_c, spec_m = MID_CRIMINAL, MID_CIVIL
    else:                       # 2018 起：取消辨析，简答每题 10 分
        spec_c, spec_m = NEW_CRIMINAL, NEW_CIVIL
    for subject, spec in (("刑法", spec_c), ("民法", spec_m)):
        for t, a, b, score in spec:
            for n in range(a, b + 1):
                table[n] = (subject, t, score)
    return table


QNUM_PAT = re.compile(r'^\s*[·•.、]?\s*([0-9lIiOo\$SBb]{1,3})\s*[.、．。:、]\s*(.*)$')
OCR_DIGIT = str.maketrans({'l': '1', 'I': '1', 'i': '1', 'O': '0', 'o': '0', 'S': '5',
                           'B': '8', 'b': '6', '$': '5', '｜': '1', '|': '1'})


def read_num(tok):
    """把 OCR 常见的数字混淆还原成题号，失败返回 None。"""
    t = tok.translate(OCR_DIGIT)
    return int(t) if t.isdigit() else None
OPT_PAT = re.compile(r'^\s*([ABCD])\s*[.、．:：]?\s*(.*)$')
NOISE = [
    re.compile(r'更多考研精品资料'), re.compile(r'光速考研'), re.compile(r'文运法硕'),
    re.compile(r'^[\s\-—]*\d{1,2}[\s\-—]*$'), re.compile(r'共\s*\d+\s*页'),
    re.compile(r'第\s*\d+\s*页'), re.compile(r'^\s*绝密\s*[★*·]?'), re.compile(r'^\s*[◎oO]\s*考生注意事项'),
    re.compile(r'^\s*(专业基础课|专业综合课)\s*$'), re.compile(r'^\s*[讲频解]\s*$'),
]


def clean_lines(txt):
    out = []
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or any(p.search(line) for p in NOISE):
            continue
        out.append(line)
    return out


def parse_file(path, year):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    lines = clean_lines(txt)
    # 跳过封面"考生注意事项"等前置内容（其中也用 1.2.3. 编号，会与题号冲突）
    head = re.compile(r'^[一二三四五六七八九十]+\s*[、.．]\s*(单项选择题|多项选择题)')
    for i, line in enumerate(lines):
        if head.match(line):
            lines = lines[i:]
            break
    table = structure(year)
    qs = {}
    cur = None
    seen_num = set()

    for line in lines:
        m = QNUM_PAT.match(line)
        num = read_num(m.group(1)) if m else None
        if m and num in table and num not in seen_num:
            seen_num.add(num)
            subject, qtype, score = table[num]
            cur = {"year": year, "num": num, "subject": subject, "type": qtype,
                   "score": score, "stem": m.group(2).strip(), "options": {}}
            qs[num] = cur
            continue
        if cur is None:
            continue
        mo = OPT_PAT.match(line)
        if mo and cur["type"] in ("单项选择", "多项选择") and mo.group(1) not in cur["options"]:
            cur["options"][mo.group(1)] = mo.group(2).strip()
            cur["_last_opt"] = mo.group(1)
            continue
        last = cur.get("_last_opt")
        if last and cur["type"] in ("单项选择", "多项选择"):
            cur["options"][last] = (cur["options"][last] + " " + line).strip()
        else:
            cur["stem"] = (cur["stem"] + " " + line).strip()

    # 合并人工补齐的题目（OCR 丢行的少数题）
    fixt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "manual_questions.json")
    if os.path.exists(fixt):
        for q in json.load(open(fixt, encoding="utf-8")):
            if q["year"] == year:
                qs.setdefault(q["num"], q)

    out = []
    for n in sorted(qs):
        q = qs[n]
        q.pop("_last_opt", None)
        q["options"] = {k: q["options"][k] for k in sorted(q["options"])}
        out.append(q)
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base = os.path.join(root, "materials", "text")
    all_q, missing = [], {}
    for p in sorted(glob.glob(os.path.join(base, "*.txt"))):
        if "综合课" in os.path.basename(p):
            continue  # 综合课另存，暂不纳入基础课统计
        year = int(os.path.basename(p)[:4])
        qs = parse_file(p, year)
        all_q.extend(qs)
        got = {q["num"] for q in qs}
        want = set(structure(year))
        miss = sorted(want - got)
        if miss:
            missing[year] = miss
        print(f"{year}: {len(qs):3}/{len(want)} 题   缺: {miss if miss else '-'}")
    out = os.path.join(root, "data", "questions.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_q, f, ensure_ascii=False, indent=1)
    print("共", len(all_q), "题 ->", out)
    if missing:
        print("缺题年份:", {k: len(v) for k, v in missing.items()})


if __name__ == "__main__":
    main()
