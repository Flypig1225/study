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


QNUM_PAT = re.compile(r'^\s*[·•.、]?\s*([0-9lIiOo\$S]{1,3})\s*[.、．。:、]\s*(.*)$')
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



OPT_INLINE = re.compile(r'(?<![A-Za-z0-9])([ABCD])\s*[.、．]\s*')



SECTION_TAIL = re.compile(r"\s*[一二三四五六七八九十]{1,3}\s*[、.．]\s*[单多]项选择题.*$")
TAIL_JUNK = re.compile(r"\s*(根据以下案情|共\s*\d+\s*分|答案|解析).*$")


def clean_option_text(txt):
    txt = SECTION_TAIL.sub("", txt)
    txt = TAIL_JUNK.sub("", txt)
    return txt.strip(" ,，。;；、")


def clean_options(qs):
    for q in qs.values():
        if q["type"] in ("单项选择", "多项选择"):
            q["options"] = {k: clean_option_text(v) for k, v in q["options"].items()}
            q["options"] = {k: v for k, v in q["options"].items() if v}


OPT_DOTTED = re.compile(r"(?<![A-Za-z0-9])[.、]?\s*([A-Da-d])\s*[.、．]\s*")
OPT_PLAIN = re.compile(r"(?<![A-Za-z0-9])\s+([A-Da-d])\s+(?=[\u4e00-\u9fff])")
OPT_LOOSE = re.compile(r"(?<![A-Za-z0-9])[.、]?\s*([A-Da-d])\s*[.、．]?\s*(?=[\u4e00-\u9fff(（])")


def _markers(blk, pat):
    """每个字母取首次出现位置；必须 A/B/C/D 各一次才认。"""
    first = {}
    for m in pat.finditer(blk):
        L = m.group(1).upper()
        if L not in first:
            first[L] = (m.start(1), m.end())
    return first if len(first) == 4 else {}


def _locate(q, full_text):
    """定位题干原文块：优先按题号行首匹配，失败则按题干前若干字做容错检索。"""
    num = q["num"]
    for m in re.finditer(rf"(?m)^\s*{num}\s*[.、．。:]", full_text):
        blk = full_text[m.start(): m.start() + 600]
        if sum(1 for ch in re.sub(r"\s+", "", q["stem"])[:10] if ch in blk) >= 5:
            return blk
    probe = re.sub(r"\s+", "", q["stem"])[:12]
    if len(probe) >= 6:
        pat = r"\s*".join(re.escape(c) for c in probe)
        m = re.search(pat, full_text)
        if m:
            return full_text[max(0, m.start() - 6): m.start() + 600]
    return None


def repair_options(q, full_text):
    """按原文 A/B/C/D 标记重切选项，修正换行合并、分隔点丢失、选项乱序等缺陷。"""
    if q["type"] not in ("单项选择", "多项选择"):
        return q
    opts0 = q.get("options", {})
    # A 项被 OCR 粘进题干（如「对甲的行为()。 1A.应以教唆罪定罪处罚」）时拆回来
    if "A" not in opts0 and len(opts0) >= 2:
        m = re.search(r"(?<![A-Za-z0-9])\s*1?\s*A\s*[.、．]\s*", q["stem"])
        if m:
            tail = q["stem"][m.end():]
            cut = re.search(r"(?<![A-Za-z0-9])[B-D]\s*[.、．]", tail)
            if cut:
                tail = tail[:cut.start()]
            tail = re.sub(r"\s+", " ", tail).strip(" ,，。;；")
            if tail:
                q["stem"] = q["stem"][: m.start()].strip()
                q["options"] = {"A": tail, **opts0}
                return q
    merged = any(re.search(r"(?<![A-Za-z0-9])[ABCDabcd]\s*[.、．]", t) for t in opts0.values())
    if len(opts0) >= 4 and not merged:
        return q
    blk = _locate(q, full_text)
    if not blk:
        return q
    nxt = re.search(rf"(?m)^\s*{q['num'] + 1}\s*[.、．。:]", blk[3:])
    if nxt:
        blk = blk[: nxt.start() + 3]
    for pat in (OPT_DOTTED, OPT_PLAIN, OPT_LOOSE):
        marks = _markers(blk, pat)
        if not marks:
            continue
        order = sorted(marks.items(), key=lambda kv: kv[1][0])
        opts = {}
        for i, (L, (_s, e)) in enumerate(order):
            end = order[i + 1][1][0] if i + 1 < len(order) else len(blk)
            txt = re.sub(r"\s+", " ", blk[e:end]).strip(" ,，。;；")
            if txt:
                opts[L] = txt
        if len(opts) == 4:
            q["options"] = {k: opts[k] for k in "ABCD"}
            return q
    return q


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

    full_text = "\n".join(lines)
    for q in qs.values():
        repair_options(q, full_text)

    # 人工补录：OCR 物理丢行的选项
    fixes_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "data", "option_fixes.json")
    if os.path.exists(fixes_path):
        with open(fixes_path, encoding="utf-8") as f:
            fixes = json.load(f)
        for k, add in fixes.items():
            if k.startswith("_"):
                continue
            y, n = k.split("-")
            if int(y) == year and int(n) in qs:
                qs[int(n)]["options"].update(add)
                qs[int(n)]["options"] = {k2: qs[int(n)]["options"][k2]
                                         for k2 in sorted(qs[int(n)]["options"])}

    clean_options(qs)

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
