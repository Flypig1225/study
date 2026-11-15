#!/usr/bin/env python3
"""把 2005-2026 法硕（非法学）专业综合课（498）纯文本切成结构化题目。

科目：法理学 / 中国宪法学 / 中国法制史
题型：单项选择 / 多项选择 / 简答 / 分析 / 论述
输出：data/zonghe/questions.json
"""

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_DIR = os.path.join(ROOT, "materials", "text")
OUT = os.path.join(ROOT, "data", "zonghe", "questions.json")

# 每套真题的精确分科界线：(单选法理末, 单选宪法末, 单选法制史末, 多选法理末, 多选宪法末, 多选法制史末)
SPLITS = {
    2005: (15, 33, 47, 53, 60, 64),
    2006: (15, 31, 45, 51, 59, 63),
    2007: (15, 31, 45, 50, 59, 63),
    2008: (15, 31, 45, 51, 59, 63),
    2009: (15, 31, 45, 51, 59, 63),
    2010: (15, 31, 45, 51, 59, 63),
    2011: (15, 31, 45, 51, 59, 63),
    2012: (15, 31, 45, 51, 59, 63),
    2013: (14, 29, 45, 51, 58, 63),
    2014: (15, 31, 45, 51, 59, 63),
    2015: (14, 29, 45, 51, 58, 63),
    2016: (14, 29, 45, 51, 58, 63),
    2017: (15, 30, 45, 51, 58, 63),
    2018: (12, 27, 40, 44, 47, 50),
    2019: (12, 27, 40, 44, 47, 50),
    2020: (12, 27, 40, 44, 47, 50),
    2021: (12, 27, 40, 44, 47, 50),
    2022: (12, 27, 40, 44, 47, 50),
    2023: (13, 27, 40, 44, 47, 50),
    2024: (12, 27, 40, 44, 47, 50),
    2025: (12, 27, 40, 44, 47, 50),
    2026: (12, 27, 40, 44, 47, 50),
}

# 58 题制年份第 58 题的归属（法理/宪法融合题按主考点归入宪法学或法制史）
SUBJ_58 = {2018: "中国法制史", 2023: "中国法制史"}


def structure(year):
    """返回 {题号: (科目, 题型, 分值)}"""
    s1, s2, s3, m1, m2, m3 = SPLITS[year]
    table = {}
    for n in range(1, s1 + 1):
        table[n] = ("法理学", "单项选择", 1)
    for n in range(s1 + 1, s2 + 1):
        table[n] = ("中国宪法学", "单项选择", 1)
    for n in range(s2 + 1, s3 + 1):
        table[n] = ("中国法制史", "单项选择", 1)
    for n in range(s3 + 1, m1 + 1):
        table[n] = ("法理学", "多项选择", 2)
    for n in range(m1 + 1, m2 + 1):
        table[n] = ("中国宪法学", "多项选择", 2)
    for n in range(m2 + 1, m3 + 1):
        table[n] = ("中国法制史", "多项选择", 2)

    if year == 2005:
        subj_map = {
            65: ("法理学", "简答", 8),
            66: ("中国宪法学", "简答", 8),
            67: ("中国法制史", "简答", 8),
            68: ("法理学", "分析", 10),
            69: ("中国宪法学", "分析", 10),
            70: ("中国法制史", "分析", 10),
            71: ("法理学", "论述", 15),
        }
    elif year == 2009:
        # 2009 卷将 15 分论述放在 68 题位置，69/70 为宪法/法制史分析
        subj_map = {
            64: ("法理学", "简答", 8),
            65: ("中国宪法学", "简答", 8),
            66: ("中国法制史", "简答", 8),
            67: ("法理学", "分析", 10),
            68: ("法理学", "论述", 15),
            69: ("中国宪法学", "分析", 10),
            70: ("中国法制史", "分析", 10),
        }
    elif year <= 2017:
        subj_map = {
            64: ("法理学", "简答", 8),
            65: ("中国宪法学", "简答", 8),
            66: ("中国法制史", "简答", 8),
            67: ("法理学", "分析", 10),
            68: ("中国宪法学", "分析", 10),
            69: ("中国法制史", "分析", 10),
            70: ("法理学", "论述", 15),
        }
    else:
        subj_map = {
            51: ("法理学", "简答", 10),
            52: ("中国宪法学", "简答", 10),
            53: ("中国法制史", "简答", 10),
            54: ("法理学", "分析", 10),
            55: ("中国宪法学", "分析", 10),
            56: ("中国法制史", "分析", 10),
            57: ("法理学", "论述", 15),
            58: (SUBJ_58.get(year, "中国宪法学"), "论述", 15),
        }
    table.update(subj_map)
    return table


OCR_DIGIT = str.maketrans({
    "l": "1", "I": "1", "i": "1", "O": "0", "o": "0",
    "S": "5", "B": "8", "b": "6", "$": "5", "｜": "1", "|": "1",
})
QNUM_PAT = re.compile(r"^\s*[·•.、]?\s*([0-9lIiOo\$S]{1,3})\s*[.、．。:]\s*(.*)$")
OPT_PAT = re.compile(r"^\s*([A-Da-d])\s*[.、．:：]?\s*(.*)$")
NOISE = [
    re.compile(r"更多考研精品资料"),
    re.compile(r"光速考研"),
    re.compile(r"文运法硕"),
    re.compile(r"淘宝店铺"),
    re.compile(r"^[\s\-—]*\d{1,2}[\s\-—]*$"),
    re.compile(r"共\s*\d+\s*页"),
    re.compile(r"第\s*\d+\s*页"),
    re.compile(r"^\s*绝密\s*[★*·]?"),
    re.compile(r"^\s*[◎oO]\s*考生注意事项"),
    re.compile(r"^\s*专业综合课\s*$"),
    re.compile(r"^\s*20\d{2}年全国法律硕士"),
]
SECTION_PAT = re.compile(r"^[一二三四五六七八九十]+\s*[、.．]\s*(?:单项选择题|多项选择题|简答题|分析题|论述题)")
SECTION_TAIL = re.compile(r"\s*[一二三四五六七八九十]{1,3}\s*[、.．]\s*(?:单|多)项选择题.*$")
OPT_DOTTED = re.compile(r"(?<![A-Za-z0-9])[.、]?\s*([A-Da-d])\s*[.、．]\s*")
OPT_PLAIN = re.compile(r"(?<![A-Za-z0-9])\s+([A-Da-d])\s+(?=[\u4e00-\u9fff])")
OPT_LOOSE = re.compile(r"(?<![A-Za-z0-9])[.、]?\s*([A-Da-d])\s*[.、．]?\s*(?=[\u4e00-\u9fff(（《“])")


def read_num(tok):
    t = tok.translate(OCR_DIGIT)
    return int(t) if t.isdigit() else None


def clean_lines(txt):
    out = []
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or any(p.search(line) for p in NOISE):
            continue
        out.append(line)
    return out


def _markers(blk, pat):
    first = {}
    for m in pat.finditer(blk):
        L = m.group(1).upper()
        if L not in first:
            first[L] = (m.start(1), m.end())
    return first if len(first) == 4 else {}


def _locate(q, full_text):
    num = q["num"]
    for m in re.finditer(rf"(?m)^\s*{num}\s*[.、．。:]", full_text):
        blk = full_text[m.start(): m.start() + 900]
        probe = re.sub(r"\s+", "", q["stem"])[:10]
        if not probe or sum(1 for ch in probe if ch in blk) >= min(5, len(probe)):
            return blk
    probe = re.sub(r"\s+", "", q["stem"])[:12]
    if len(probe) >= 6:
        pat = r"\s*".join(re.escape(c) for c in probe)
        m = re.search(pat, full_text)
        if m:
            return full_text[max(0, m.start() - 6): m.start() + 900]
    return None


def repair_options(q, full_text):
    if q["type"] not in ("单项选择", "多项选择"):
        return q
    opts0 = q.get("options", {})
    # 若 A 项被粘到题干尾巴
    if "A" not in opts0 and len(opts0) >= 2:
        m = re.search(r"(?<![A-Za-z0-9])\s*1?\s*A\s*[.、．]?\s*", q["stem"])
        if m:
            tail = q["stem"][m.end():]
            cut = re.search(r"(?<![A-Za-z0-9])[B-D]\s*[.、．]", tail)
            if cut:
                tail = tail[:cut.start()]
            tail = re.sub(r"\s+", " ", tail).strip(" ,，。;；")
            if tail:
                q["stem"] = q["stem"][: m.start()].strip()
                q["options"] = {"A": tail, **opts0}
                opts0 = q["options"]

    merged = any(re.search(r"(?<![A-Za-z0-9])[B-Db-d]\s*[.、．]", t) for t in opts0.values())
    if len(opts0) >= 4 and not merged:
        return q

    blk = _locate(q, full_text)
    if not blk:
        return q
    nxt = re.search(rf"(?m)^\s*(?:{q['num'] + 1}\s*[.、．。:]|[二三四五][、.．])", blk[3:])
    if nxt:
        blk = blk[: nxt.start() + 3]

    ma = re.search(r"(?m)(?:^|\s)[A-Da-d]\s*[.、．]?\s*(?=[\u4e00-\u9fff0-9(（《“])", blk)
    if ma:
        blk_opt = blk[ma.start():]
    else:
        blk_opt = blk

    for pat in (OPT_DOTTED, OPT_PLAIN, OPT_LOOSE):
        marks = _markers(blk_opt, pat)
        if not marks:
            continue
        order = sorted(marks.items(), key=lambda kv: kv[1][0])
        opts = {}
        for i, (L, (_s, e)) in enumerate(order):
            end = order[i + 1][1][0] if i + 1 < len(order) else len(blk_opt)
            txt = re.sub(r"\s+", " ", blk_opt[e:end]).strip(" ,，。;；")
            txt = SECTION_TAIL.sub("", txt).strip(" ,，。;；")
            if txt:
                opts[L] = txt
        if len(opts) == 4:
            q["options"] = {k: opts[k] for k in "ABCD"}
            return q
    return q


def clean_option_text(txt):
    txt = SECTION_TAIL.sub("", txt)
    txt = re.sub(r"\s*[二三四五][、.．]\s*(?:多项选择|简答|分析|论述).*$", "", txt)
    return txt.strip(" ,，;；、")


def parse_file(path, year):
    txt = open(path, encoding="utf-8").read()
    lines = clean_lines(txt)
    head = re.compile(r"^[一二三四五六七八九十]+\s*[、.．]\s*单项选择题")
    for i, line in enumerate(lines):
        if head.match(line):
            lines = lines[i:]
            break

    table = structure(year)
    qs = {}
    cur = None
    seen_num = set()

    for line in lines:
        if SECTION_PAT.match(line):
            # 跳过大题标题行，不拼接进上一题末尾选项/题干
            if cur is not None:
                cur.pop("_last_opt", None)
            continue
        m = QNUM_PAT.match(line)
        num = read_num(m.group(1)) if m else None
        if m and num in table and num not in seen_num:
            # 防止年号 2011 等误判
            if num == max(seen_num, default=0) + 1 or (num > max(seen_num, default=0) and num <= len(table)):
                seen_num.add(num)
                subject, qtype, score = table[num]
                cur = {
                    "year": year,
                    "num": num,
                    "subject": subject,
                    "type": qtype,
                    "score": score,
                    "stem": m.group(2).strip(),
                    "options": {},
                }
                qs[num] = cur
                continue
        if cur is None:
            continue
        mo = OPT_PAT.match(line)
        if mo and cur["type"] in ("单项选择", "多项选择"):
            L = mo.group(1).upper()
            # 只当字母是有效选项前缀（有 .、: 或 换行独立行首字母后接非标点/数字）才切新选项
            if L not in cur["options"] and (re.match(r"^\s*[A-Da-d]\s*[.、．:：]", line) or re.match(r"^\s*[A-Da-d]\s+[\u4e00-\u9fff0-9(（《“]", line)):
                cur["options"][L] = mo.group(2).strip()
                cur["_last_opt"] = L
                continue
        last = cur.get("_last_opt")
        if last and cur["type"] in ("单项选择", "多项选择"):
            cur["options"][last] = (cur["options"][last] + " " + line).strip()
        else:
            cur["stem"] = (cur["stem"] + " " + line).strip()

    full_text = "\n".join(lines)
    for q in qs.values():
        repair_options(q, full_text)
        if q["type"] in ("单项选择", "多项选择"):
            q["options"] = {k: clean_option_text(v) for k, v in q["options"].items()}
            q["options"] = {k: v for k, v in sorted(q["options"].items()) if v}

    out = []
    for n in sorted(qs):
        q = qs[n]
        q.pop("_last_opt", None)
        out.append(q)
    return out


def main():
    all_q = []
    bad_opts = []
    for y in range(2005, 2027):
        p = os.path.join(TXT_DIR, f"{y}_法硕（非法学）_专业综合课真题.txt")
        qs = parse_file(p, y)
        all_q.extend(qs)
        want = set(structure(y))
        got = {q["num"] for q in qs}
        miss = sorted(want - got)
        incomplete = [q["num"] for q in qs if q["type"] in ("单项选择", "多项选择") and sorted(q["options"]) != ["A", "B", "C", "D"]]
        if incomplete:
            bad_opts.extend((y, n, sorted(next(x for x in qs if x["num"] == n)["options"])) for n in incomplete)
        print(f"{y}: {len(qs):2}/{len(want)} 题  缺题:{miss or '-'}  残缺选项:{incomplete or '-'}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(all_q, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"合计 {len(all_q)} 题 -> {os.path.relpath(OUT, ROOT)}")
    if bad_opts:
        print("残缺选项详情:", bad_opts)


if __name__ == "__main__":
    main()
