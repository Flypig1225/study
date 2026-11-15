#!/usr/bin/env python3
"""解析 2005-2026 法硕（非法学）专业综合课答案解析文本 -> data/zonghe/answers.json

处理要点：
1. 2010-2021 题号 OCR 数字还原（l/I->1, O->0, 空格合并）与孤立悬浮答案字母回填。
2. 2008 行内粘连题号拆分、2009 无标点题号兼容、2020 多字间空格兼容。
3. 2023 切取「专业综合课参考答案」之后段落，速查表按位置对齐。
4. 2024 采用原图核验的答案速查表 + 51-58 主观详解。
5. 2026 支持 `1. 答案:A` 及主观题独立切块。
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_DIR = os.path.join(ROOT, "materials", "answer_text_zonghe")
Q_PATH = os.path.join(ROOT, "data", "zonghe", "questions.json")
MANUAL_PATH = os.path.join(ROOT, "data", "zonghe", "answers_manual.json")
OUT_OBJ = os.path.join(ROOT, "data", "zonghe", "answers.json")
OUT_SUBJ = os.path.join(ROOT, "data", "zonghe", "subjective_answers.json")

OCR_DIGIT = str.maketrans({"l": "1", "I": "1", "i": "1", "O": "0", "o": "0"})


def fix_qnum_prefix(line):
    # 把行首 OCR 损坏的题号还原，如 `II.【答案】` -> `11.【答案】`, `3 1.【答案】` -> `31.【答案】`, `lO.` -> `10.`
    m = re.match(r"^\s*([0-9lIiOo][0-9lIiOo\s]{0,3}?)\s*([.、．,，:：]?\s*\[答案\].*)$", line)
    if m:
        tok = re.sub(r"\s+", "", m.group(1)).translate(OCR_DIGIT)
        if tok.isdigit():
            return f"{tok}{m.group(2)}"
    return line


def norm(t, year):
    t = t.replace("\u00a0", " ")
    if year == 2023:
        idx = t.find("专业综合课参考答案")
        if idx >= 0:
            t = t[idx:]
    if year == 2024:
        t = re.sub(r"([^\n])(五、论述题)", r"\1\n\2", t)
        t = re.sub(r"(五、论述题)\s*(57\.)", r"\1\n\2", t)
    t = re.sub(r"[【〔\[\(（]\s*答\s*案\s*[】〕\]\)）l1!]?", "[答案]", t)
    t = re.sub(r"[【〔\[\(（]\s*解\s*析\s*[】〕\]\)）l1!]?", "[解析]", t)
    t = re.sub(r"[【〔\[\(（]\s*考\s*点\s*[】〕\]\)）l1!]?", "[考点]", t)
    t = re.sub(r"[【〔\[\(（]\s*详\s*解\s*[】〕\]\)）l1!]?", "[详解]", t)
    t = t.replace("『", "[").replace("』", "]")
    t = t.replace("“", '"').replace("”", '"')
    t = re.sub(r"[ \t\u3000]+", " ", t)
    # 2008 等行内粘连：`...故应选C。6.C[解析]` -> 换行
    t = re.sub(r"([。；;])\s*(\d{1,2}\s*[.、．]\s*[A-D]{1,4}\s*\[解析\])", r"\1\n\2", t)

    lines = [fix_qnum_prefix(ln) for ln in t.splitlines()]
    fixed = []
    i = 0
    while i < len(lines):
        cur = lines[i].strip()
        if i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            m_let = re.fullmatch(r"([A-Da-d\s]{1,8}(?:\s*\([^)]*\))?)", cur)
            m_q = re.match(r"^(\d{1,2}\s*[.、．,，:：]?\s*\[答案\])\s*(.*)$", nxt)
            if m_let and m_q and not re.match(r"^[A-Da-d]", m_q.group(2)):
                raw_let = m_let.group(1)
                # 处理 `AC(原答案为C)`：保留原题型信息供单选判定，并将修订说明写入后续正文
                m_orig = re.search(r"原答案为\s*([A-D]{1,4})", raw_let)
                if m_orig:
                    let = m_orig.group(1)
                    note = f"[修订提示：{raw_let.strip()}] "
                else:
                    let = re.sub(r"[^A-Da-d]", "", raw_let).upper()
                    note = ""
                fixed.append(f"{m_q.group(1)} {let} {note}{m_q.group(2)}".strip())
                i += 2
                continue
        fixed.append(lines[i])
        i += 1
    return "\n".join(fixed)


def split_obj_subj(txt, year):
    if year == 2009:
        m_sub = re.search(r"(?m)^\s*64\s+(?:答案|\[?答案)", txt)
    elif year == 2023:
        m_sub = re.search(r"(?m)^\s*(?:三\s*[、.．]\s*)?简\s*答\s*题", txt)
    else:
        m_sub = re.search(r"(?m)^\s*三\s*[、.．]\s*简\s*答\s*题", txt)
    if m_sub:
        return txt[:m_sub.start()], txt[m_sub.start():]
    return txt, ""


def split_blocks(seg, max_num):
    ms = list(
        re.finditer(
            r"(?m)^\s*(\d{1,2})(?:\s*[.、．,，:：]\s*|\s*(?=\[(?:答案|解析)\])|\s+(?=[A-D]{1,4}(?:\s|\[)|本题考查))",
            seg,
        )
    )
    blocks, seen = {}, set()
    valid = []
    for m in ms:
        num = int(m.group(1))
        if 1 <= num <= max_num and num not in seen:
            # 防止前面题目解析内部偶然出现数字开头行抢号（要求基本递增）
            if not valid or num > valid[-1][0]:
                seen.add(num)
                valid.append((num, m.start(), m.end()))
    for i, (num, _s, e) in enumerate(valid):
        end = valid[i + 1][1] if i + 1 < len(valid) else len(seg)
        blocks[num] = seg[e:end]
    return blocks


def find_answer(body, qtype):
    head = body[:140]
    # 只匹配同行空白，防止跨行把下一行 `A、B、C` 误并进答案字母
    L = r"([A-D](?:[ \t]*[、,，/和及]?[ \t]*[A-D]){0,3})"
    pats = [
        r"\[答案\]\s*[:：]?[^A-Da-z\n]{0,4}" + L,
        r"^\s*" + L + r"[ \t]*[\[\(【〔]",
        r"^\s*" + L + r"[ \t]*(?:\n|$|。)",
        r"答\s*案\s*[:：][ \t]*" + L,
        r"(?:本题|该题|此题|此题中)?\s*(?:正确)?答案\s*(?:为|是|应选|选)\s*[:：]?[ \t]*" + L,
        r"(?:故|因此|所以|综上)[^。；\n]{0,16}?(?:选|应选)\s*[:：]?[ \t]*" + L,
        r"(?:应选|故选|选择|选)[ \t]*" + L + r"(?![A-Za-z])",
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
    if m is None:
        return body.strip()
    if m.start() <= 45:
        t = body[m.end():]
        t = re.sub(r"^[\s。．.、,，:：\[\]【】()（）]*", "", t)
    else:
        t = body
    t = re.sub(r"[\[\(【〔]\s*(?:解析|考点|详解|命题思路|评析|答案)\s*[\]\)】〕]\s*[:：]?\s*", "", t)
    t = re.sub(r"(?m)^[\s。．.、,，:：\[\]【】()（）]*(?:解析|考点|详解)\s*[:：]?\s*", "", t)
    t = re.sub(r"^[\]\)】〕\s]+", "", t)
    t = re.sub(r"更多考研精品资料[^。\n]*", "", t)
    t = re.sub(r"[-—]\s*\d{1,3}\s*[-—]", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def parse_speed_table(t):
    out = {}
    for m in re.finditer(r"(?m)^(\d{1,2})\s*[-~]\s*(\d{1,2})\s*[:：]\s*([A-D\s]+)$", t):
        a, b = int(m.group(1)), int(m.group(2))
        toks = m.group(3).split()
        if len(toks) == b - a + 1:
            for n, ans in zip(range(a, b + 1), toks):
                out[n] = "".join(sorted(set(ans)))
    for m in re.finditer(r"(?m)^(\d{1,2})\.\s*([A-D]{1,4})(?:\s*\([^)]*\))?\s*$", t):
        out[int(m.group(1))] = "".join(sorted(set(m.group(2))))
    if out:
        return out

    i = t.find("答案速查")
    if i < 0:
        return {}
    seg = t[i:t.find("简答题", i) if t.find("简答题", i) > 0 else i + 1800]
    lines = [x.strip() for x in seg.split("\n") if x.strip()]
    pending = None
    for ln in lines:
        toks = ln.split()
        if all(x.isdigit() for x in toks) and len(toks) >= 5:
            pending = toks
            continue
        if pending and all(re.fullmatch(r"[A-D]{1,4}", x) for x in toks) and len(toks) == len(pending):
            nums = [int(x) for x in pending]
            base = (min(nums) - 1) // 10 * 10 + 1
            for n, ans in zip(range(base, base + len(nums)), toks):
                out[n] = "".join(sorted(set(ans)))
            pending = None
    return out


def parse_subjective_blocks(subj_txt, min_num, max_num):
    if not subj_txt:
        return {}
    ms = list(re.finditer(r"(?m)^\s*(\d{2})(?:\s*[.、．:：]\s*|\s+(?=答案|\[))", subj_txt))
    valid = []
    seen = set()
    for m in ms:
        n = int(m.group(1))
        if min_num <= n <= max_num and n not in seen:
            if not valid or n > valid[-1][0]:
                seen.add(n)
                valid.append((n, m.start(), m.end()))
    out = {}
    for i, (n, _s, e) in enumerate(valid):
        end = valid[i + 1][1] if i + 1 < len(valid) else len(subj_txt)
        body = subj_txt[e:end].strip()
        body = re.sub(r"更多考研精品资料[^。\n]*", "", body)
        body = re.sub(r"^\s*(?:\[(?:答案|答案要点|详解|参考答案|解析)\]|答案要点|参考答案|答案|详解)\s*[:：]?\s*", "", body)
        out[n] = body.strip()
    return out


def main():
    qs = json.load(open(Q_PATH, encoding="utf-8"))
    expect_obj = {}
    expect_subj = {}
    for q in qs:
        if q["type"] in ("单项选择", "多项选择"):
            expect_obj.setdefault(q["year"], {})[q["num"]] = q["type"]
        else:
            expect_subj.setdefault(q["year"], []).append(q["num"])

    out_obj, out_subj = {}, {}
    for y in sorted(expect_obj):
        path = os.path.join(TXT_DIR, f"{y}.txt")
        raw = norm(open(path, encoding="utf-8").read(), y)
        speed = parse_speed_table(raw)
        obj_txt, subj_txt = split_obj_subj(raw, y)
        max_obj = max(expect_obj[y])
        blocks = split_blocks(obj_txt, max_obj)

        for num, qtype in sorted(expect_obj[y].items()):
            key = f"{y}-{num}"
            body = blocks.get(num)
            if body and not speed:
                letters, m = find_answer(body, qtype)
                if letters:
                    out_obj[key] = {"a": letters, "e": strip_marks(body, m)[:4000]}
                    continue
            if num in speed:
                out_obj[key] = {"a": speed[num], "e": ""}
                continue
            if body:
                letters, m = find_answer(body, qtype)
                if letters:
                    out_obj[key] = {"a": letters, "e": strip_marks(body, m)[:4000]}

        subj_nums = expect_subj[y]
        s_map = parse_subjective_blocks(subj_txt, min(subj_nums), max(subj_nums))
        for n in subj_nums:
            if n in s_map and s_map[n]:
                out_subj[f"{y}-{n}"] = s_map[n]

    if os.path.exists(MANUAL_PATH):
        man = json.load(open(MANUAL_PATH, encoding="utf-8"))
        for k, v in man.items():
            if k.startswith("_"):
                continue
            out_obj[k] = v

    os.makedirs(os.path.dirname(OUT_OBJ), exist_ok=True)
    json.dump(out_obj, open(OUT_OBJ, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(out_subj, open(OUT_SUBJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    tot_obj = sum(len(v) for v in expect_obj.values())
    miss_obj = [f"{y}-{n}" for y in sorted(expect_obj) for n in sorted(expect_obj[y]) if f"{y}-{n}" not in out_obj]
    tot_subj = sum(len(v) for v in expect_subj.values())
    miss_subj = [f"{y}-{n}" for y in sorted(expect_subj) for n in sorted(expect_subj[y]) if f"{y}-{n}" not in out_subj]
    print(f"客观题答案: {len(out_obj)}/{tot_obj}  缺: {miss_obj or '-'}")
    print(f"主观题答案: {len(out_subj)}/{tot_subj}  缺: {miss_subj or '-'}")


if __name__ == "__main__":
    main()
