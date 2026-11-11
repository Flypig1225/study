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
    """把『…,B选项正确,A选项错误』这类句子按评语位置切开，分别挂到各自的选项上。"""
    got = {}
    MARK = re.compile(r"(?<![A-Za-z])([A-D])\s*(?:选项|项)?\s*(?:正确|错误|当选|不选|对|错)(?![一-龥])")
    for s in sents:
        marks = list(MARK.finditer(s))
        if marks:
            prev = 0
            for m in marks:
                seg = s[prev:m.start()].strip(" ,，。；")
                prev = m.end()
                seg = re.sub(r"^\s*(?:选项)?[A-D](?:选项|项)?\s*[、,，：:]?\s*", "", seg).strip(" ,，。；")
                if (len(seg) >= 8 and not re.match(r"^(都|均|皆|全|只有|选项)", seg)
                        and not re.fullmatch(r"(正确|错误|当选|不选|对|错)", seg)):
                    got.setdefault(m.group(1), seg)
            continue
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
        if (not body or len(body) < 10
                or re.fullmatch(r"(正确|错误|当选|不选|对|错)(项|选项)?", body)
                or re.match(r"^(都|均|皆|全|一律|只有|选项)", body)):
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


CITE = re.compile
CITE = re.compile(r"《[^》]{2,34}》(?:第[〇一二三四五六七八九十百零\d]+条(?:第[〇一二三四五六七八九十百零\d]+款)?)?")
CRIME = re.compile(r"(?:不)?(?:构成|属于|成立)[^，。；、]{2,18}?罪")


def hl(t):
    """补充要点里的重点：法条、罪名用红字加粗包起来（\x03…\x04）。"""
    t = CITE.sub(lambda m: "\x03" + m.group(0) + "\x04", t)
    t = CRIME.sub(lambda m: "\x03" + m.group(0) + "\x04", t)
    return re.sub(r"\x03(\x03[^\x04]*\x04)\x04", r"\1", t)


def clause_split(t):
    return [c for c in re.split(r"[，,、；;。]", t or "") if c.strip()]


VERBISH = re.compile(r"(不|是|为|属于|构成|应当|可以|不得|无效|有效|优先|没有|须|需|按|依|即|指)")
BADDOT = re.compile(r"^(选项|都|均|皆|全|只有)")
GOODEND = re.compile(r"(罪|行为|顺序|原则|规定|权利|义务|责任|效力|有效|无效|成立|不成立|优先受偿|约束力|期限|范围)$")
STRONG = re.compile(r"((?:不)?构成[^，。；]{0,14}罪|符合[^，。；]{0,20}罪|罪的构成要件|优先受偿|无效|不成立|可以|不得)")
VERD = re.compile(r"(构成[^，。；]{0,14}罪|不构成[^，。；]{0,10}罪|优先受偿|无效|有效|成立|不成立|应当|不得|不予|属于|不属于|按|按照)")
FILLER = re.compile(r"^(可见|本题中|本案中|因此|所以|故|但是|但|而|并|且|则|据此|综上|另|此外)[,，]?\s*")


def gist(body, option_text, limit=22):
    """选项下面那一行：只留最关键的一句，长度控制在框里放得下。"""
    t = despac(strip_tail(body or "")).strip(" 。，；")
    t = FILLER.sub("", t)
    if not t:
        return ""
    cls = [FILLER.sub("", c).strip(" ,，。；") for c in clause_split(t)]
    cls = [c for c in cls if c]
    # 法条出处那半句（根据《…》…规定）不算概要
    cls = [c for c in cls if not re.match(r"^\s*(根据|依据|按照)?\s*《", c)
           and not re.match(r"^\s*根据[^，。；]{0,30}(规定|条)", c)] or cls
    if not cls:
        return t[:limit]
    opt = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", option_text or "")
    pick = None
    for c in cls:                                   # 首选“构成/不构成…罪、优先受偿、无效”这类硬结论
        if STRONG.search(c) and len(c) <= limit + 6:
            pick = c
            break
    for c in cls:                                   # 再找带结论词的短句
        if not pick and VERD.search(c) and len(c) <= limit + 2:
            pick = c
            break
    if not pick and opt:                            # 再找命中选项关键词的短句
        for c in cls:
            if len(c) > limit:
                continue
            for size in (8, 6, 5, 4):
                if any(opt[i:i + size] and opt[i:i + size] in c
                       for i in range(0, max(1, len(opt) - size + 1))):
                    pick = c
                    break
            if pick:
                break
    if not pick:
        c = min(cls, key=len)
        if len(c) <= 16:
            pick = c
    if pick and (BADDOT.search(pick)
                 or (not GOODEND.search(pick) and len(pick) > 12)
                 or (not GOODEND.search(pick) and not VERBISH.search(pick))):
        pick = None                       # 半截话/空缺短语不要，改成通用提示
    if not pick:
        return ""
    if len(pick) <= limit:
        return pick
    cut = pick[:limit]
    for mark in ("，", "、", "；", "的"):
        i = cut.rfind(mark)
        if i >= int(limit * 0.5):
            return cut[:i]
    return cut


def shape(ans, options):
    a = ans.get("a") or ""
    text = clean(ans.get("e") or "")
    if not text:
        return {"a": a, "e": ""}
    sents = drop_lead_title(strip_title_prefix(sentences(text)))
    concl = pick_conclusion(sents, a)
    per = attribute(sents)
    used = {concl} if concl else set()

    lines, detail, seen_body = [], [], set()
    for L in "ABCD":
        mark = "✓" if L in a else "✗"
        body = per.get(L)
        if not body and options:
            body = phrase_reason(options.get(L, ""), text)
            # 错项的理由必须是否定性的，否则多半是在讲正确项，宁可不挂
            if body and L not in a and not re.search(r"(不|非|并非|而非|不是|错误|排除|无关|不符)", body) \
                    and not re.search(rf"{L}\s*(?:选项|项)", body):
                body = ""
        NEG = re.compile(r"(不构成|不是|不属于|并非|而非|没有|并未|排除|错误|不符|不能|不得|不应该)")
        if body and L not in a and not NEG.search(body) and not re.search(rf"{L}\s*(?:选项|项)", body):
            body = ""                     # 讲的是别项/正确项，不硬挂
        if body and gist(body, None) in seen_body:      # 同一个理由不重复挂在多个选项下
            body = ""
        if body:
            used.add(body)
            seen_body.add(gist(body, None))
        if L in a and not body:
            cand = concl if (concl and len(concl) >= 12 and concl not in used
                             and gist(concl, None) not in seen_body) else ""
            if not cand:
                pool = [x for x in sents if x not in used and len(strip_tail(x)) >= 12
                        and gist(x, None) not in seen_body]
                cand = max(pool, key=len) if pool else ""
            body = cand
            if body:
                used.add(body)
                seen_body.add(gist(body, None))
        if body:
            g = gist(body, (options or {}).get(L, ""))
            if not g:
                g = "表述正确，详见下方" if L in a else "本题不选，理由见下方"
            lines.append(f"{L}{mark} {g}")
            full = despac(strip_tail(body)).strip(" 。，；")
            if len(full) > len(g) + 4:
                if len(full) > 190:
                    cut = full[:190]
                    i = max(cut.rfind("。"), cut.rfind("；"), cut.rfind(","))
                    full = cut[:i + 1] if i > 100 else cut + "…"
                detail.append(f"{L} 项：{hl(full)}")
        else:
            lines.append(f"{L}{mark} {'表述正确，详见下方' if L in a else '本题不选，理由见下方'}")

    if concl and any(concl in ln for ln in lines):
        concl = ""

    # 底部解析：直接用原文（去 OCR 空格、法条罪名红字），不再只放“剩余内容”
    orig = despac(re.sub(r"\s+", " ", text)).strip()
    orig = re.sub(r"(?<=[。；])\s*(?![”\"])", "\n", orig).strip()   # 一句一行，读起来清楚
    if len(orig) > 1500:
        cut = orig[:1500]
        i = max(cut.rfind("。"), cut.rfind("；"))
        orig = cut[:i + 1] if i > 700 else cut.rstrip("，。；") + "…"
    orig = hl(orig)

    parts = [despac(x) for x in lines]
    parts.append(orig)                    # 底部就是原解析全文
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
