#!/usr/bin/env python3
"""把解析原文改写成刷题页需要的「结论 + 逐项说明 + 补充要点」结构。

输出 data/answers_shaped.json：{ "2005-1": {"a": "B", "e": "…"} }
e 的格式（与导游刷题模板一致）：
    \\x01结论句（加粗）\\x02
    A✓ 一句话说明
    B✗ 一句话说明
    ……
    补充要点（没有字母前缀的行，显示在底部“解析”框）
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "answers.json")
OUT = os.path.join(ROOT, "data", "answers_shaped.json")

OCR_FIX = {"北体": "本题", "教竣": "教唆", "教咬": "教唆", "属千": "属于", "千是": "于是", "植人": "植入"}
JUNK = [
    re.compile(r"更多考研精品资料[^。\n]*"),
    re.compile(r"[-—]\s*\d{1,3}\s*[-—]\s*\]?"),
    re.compile(r"(?m)^\s*[\]\)】〕]\s*"),
]
BARE = re.compile(r"^(?:故)?\s*(?:正确)?答案\s*(?:为|是)?\s*[:：]?\s*[A-D、,，]{1,7}\s*。?$")
CONCL = re.compile(r"(故选|答案为|答案选|本题答案|正确答案|应选|正确选项为|答案是)")
CONCL2 = re.compile(r"(因此|所以|故|可见|综上)[^。]{0,40}(正确|错误|适用|构成|成立|有效|无效|不属于)")
LEAD = re.compile(r"^\s*(?:选项)?\s*([A-D](?:\s*[、,，]?\s*[A-D])*)\s*(?:选项|项)?\s*[、．.,，]?\s*(?:中|的)?\s*")
ANY = re.compile(r"(?<![A-Za-z])([A-D])\s*(?:选项|项)")
VERDICT = re.compile(r"(正确|错误|成立|不成立|符合|不符合|当选|不选|排除|应选|对|错)")


def clean(t):
    t = t or ""
    for k, v in OCR_FIX.items():
        t = t.replace(k, v)
    for p in JUNK:
        t = p.sub("", t)
    t = re.sub(r"^\s*[\]\)】〕、,，。]+\s*", "", t)
    t = re.sub(r"^原答案\s*(?:为|是)?\s*[A-D][)）\]]?\s*", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def sentences(t):
    out = []
    for seg in re.split(r"(?<=[。；!?！？])", t):
        seg = seg.strip()
        if not seg:
            continue
        if re.match(r"^\s*(?:选项)?\s*[A-D]\s*(?:选项|项)", seg) and len(seg) > 60:
            out.extend([x.strip() for x in re.split(r"(?<=[，,])", seg) if x.strip()])
        else:
            out.append(seg)
    return out


def short(s, limit=56):
    s = re.sub(r"[,，]\s*(?:选项)?[A-D]{1,3}\s*$", "", (s or "").strip()).strip('"“”\' ')
    s = re.sub(r"[,，]?\s*(?:选项)?[A-D](?:选项|项)?\s*(?:正确|错误)[。；]?$", "", (s or "").strip())
    s = re.sub(r"^(?:故|因此|所以|但是|而|并且|另|此外|可见|综上)[,，]?", "", s.strip(" 。；,，"))
    if len(s) <= limit:
        return s
    cut = s[:limit]
    for mark in ("，", "、", "；", " "):
        i = cut.rfind(mark)
        if i >= int(limit * 0.55):
            return cut[:i] + "…"
    return cut + "…"


def strip_tail(s):
    """去掉句尾的『A选项正确 / BCD选项错误』这类评语尾巴。"""
    s = re.sub(r"[,，;；]?\s*(?:选项)?[A-D]+\s*(?:选项|项)?\s*(?:正确|错误|当选|不选)[。；]?\s*$", "", s.strip())
    return s.strip(" ，。")


def pick_conclusion(sents, a):
    for s in sents:
        if CONCL.search(s) and 8 <= len(s) <= 80 and not BARE.match(s):
            return strip_tail(s)
    for s in sents:
        if CONCL2.search(s) and 10 <= len(s) <= 80:
            return s
    for s in sents:
        if re.search(rf"(?<![A-Za-z]){a[0]}\s*(?:选项|项)?\s*.{0,2}(正确|符合|当选)", s) and 8 <= len(s) <= 80:
            return s
    return ""


def attribute(sents):
    got = {}
    for s in sents:
        m = LEAD.match(s)
        if m:
            letters = re.findall(r"[A-D]", m.group(1))
            body = s[m.end():]
        else:
            found = ANY.findall(s)
            if found and VERDICT.search(s):
                letters, body = found, s
            else:
                continue
        body = re.sub(r"^\s*(?:选项)?[A-D](?:选项|项)?\s*", "", body).strip(" ,，。；")
        if not body or len(body) < 10 or re.fullmatch(r"(正确|错误|当选|不选|对|错)(项|选项)?", body):
            continue
        for L in letters:
            got.setdefault(L, body)
    return got


def phrase_reason(option_text, text):
    opt = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", option_text or "")
    if len(opt) < 4:
        return ""
    for size in (12, 10, 8, 6, 5):
        for i in range(0, max(1, len(opt) - size + 1)):
            key = opt[i:i + size]
            if len(key) < size:
                break
            j = text.find(key)
            if j < 0:
                continue
            left = max(text.rfind("。", 0, j), text.rfind("；", 0, j), text.rfind("，", 0, j))
            rights = [x for x in (text.find("。", j), text.find("；", j), text.find("，", j + size)) if x > 0]
            clause = text[left + 1:min(rights) if rights else len(text)].strip(" ,，。；")
            if len(clause) >= 8:
                return clause
    return ""


def strip_title_prefix(sents):
    """『商标权的保护期限 商标法规定…』这种把小标题粘在正文前的，去掉标题部分。"""
    out = []
    for s in sents:
        s = re.sub(r"^[^\s，。；]{2,14}\s+(?=《|[商著专合刑民权]|根据|本题|依据|按照|所谓)", "", s)
        if s.strip():
            out.append(s.strip())
    return out


def drop_lead_title(sents):
    """开头那半句『商标权的保护期限』其实是考点小标题，去掉。"""
    while sents and len(sents[0]) <= 14 and not re.search(r"[，。；]", sents[0]):
        sents = sents[1:]
    return sents


def despac(t):
    """OCR 常把词拆开『本 案中』，中文之间多余空格去掉；数字/字母旁边保留。"""
    t = re.sub(r"(?<=[\u4e00-\u9fff，。；：、）】》])\s+(?=[\u4e00-\u9fff])", "", t)
    t = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-D]\s*选项)", "", t)
    return t


def shape(ans, options):
    a = ans.get("a") or ""
    text = clean(ans.get("e") or "")
    if not text:
        return {"a": a, "e": ""}
    sents = drop_lead_title(strip_title_prefix(sentences(text)))
    concl = pick_conclusion(sents, a)
    per = attribute(sents)
    used = {concl} if concl else set()

    lines, bold, seen_body = [], "", set()
    for L in "ABCD":
        mark = "✓" if L in a else "✗"
        body = per.get(L)
        if not body and options:
            body = phrase_reason(options.get(L, ""), text)
        if body and short(body) in seen_body:      # 同一个理由不重复挂在多个选项下
            body = ""
        if body:
            used.add(body)
            seen_body.add(short(body))
        if L in a and not body:
            # 正确项没有单独评述时，用结论句或最长的一句正文充当理由
            cand = concl if (concl and len(concl) >= 12 and concl not in used
                             and short(concl) not in seen_body) else ""
            if not cand:
                pool = [x for x in sents if x not in used and len(strip_tail(x)) >= 12
                        and short(x) not in seen_body]
                cand = max(pool, key=len) if pool else ""
            body = cand
            if body:
                used.add(body)
                seen_body.add(short(body))
        if body:
            lines.append(f"{L}{mark} {short(body)}")
        else:
            lines.append(f"{L}{mark} {'该项表述正确，见解析' if L in a else '干扰项'}")
    # 结论句如果已经当作正确项理由，就不再多写一行，避免重复
    if concl and any(concl in ln for ln in lines):
        concl = ""

    rest = [s for s in sents if s not in used]
    rest_txt = re.sub(r"^\s*[。；,，]+", "", "".join(rest)).strip()
    if len(rest_txt) > 380:
        rest_txt = rest_txt[:380].rstrip("，。；") + "…"
    parts = []
    lines = [despac(x) for x in lines]
    rest_txt = despac(rest_txt)
    concl = despac(concl) if concl else concl
    if concl and not any(concl[:12] and concl[:12] in ln for ln in lines):
        parts.append("\x01" + short(concl, 64) + "\x02")
    parts.extend(lines)
    if rest_txt:
        parts.append(rest_txt)
    return {"a": a, "e": "\n".join(parts)}


def main():
    ans = json.load(open(SRC, encoding="utf-8"))
    qmap = {}
    for q in json.load(open(os.path.join(ROOT, "data", "tagged.json"), encoding="utf-8")):
        if q["type"] in ("单项选择", "多项选择"):
            qmap[f"{q['year']}-{q['num']}"] = q.get("options") or {}
    out = {k: shape(v, qmap.get(k)) for k, v in ans.items() if not k.startswith("_")}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    real = tot = 0
    for v in out.values():
        for ln in (l for l in v["e"].split("\n") if re.match(r"^[A-D][✓✗] ", l)):
            tot += 1
            if not re.search(r"(正确选项|干扰项)$", ln):
                real += 1
    print(f"{len(out)} 条 -> {os.path.relpath(OUT, ROOT)}；逐项有实质理由 {real}/{tot} = {100*real/tot:.0f}%")


if __name__ == "__main__":
    main()
