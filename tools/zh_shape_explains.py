#!/usr/bin/env python3
"""将 data/zonghe/answers.json + answers_manual.json + answers_manual_remake.json + answers_amend.json
精炼整理为刷题页直接使用的 data/zonghe/answers_remake.json，同时匹配 kb 与 kh 区间。

设计准则（对齐 398 quiz.html）：
1. 仅使用 \x01...\x02 加粗标记，禁止 \x03/\x04。
2. 首行 \x01总结句\x02；中间 A✓/✗..D✓/✗ 逐项精析；底部为去除孤立字母 A-E 的深度拓展解析。
3. 100% 通过 REFL 选项乱序安全校验（非选项行不含孤立 A-E 字母）。
4. 为每道题匹配最优 data/zonghe/kb.json 卡片及精确 kh [[start, end], ...] 高亮区间。
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONGHE = os.path.join(ROOT, "data", "zonghe")
TAGGED_PATH = os.path.join(ZONGHE, "tagged.json")
ANS_PATH = os.path.join(ZONGHE, "answers.json")
MANUAL_PATH = os.path.join(ZONGHE, "answers_manual.json")
MANUAL_RM_PATH = os.path.join(ZONGHE, "answers_manual_remake.json")
AMEND_PATH = os.path.join(ZONGHE, "answers_amend.json")
KB_PATH = os.path.join(ZONGHE, "kb.json")
KB_META_PATH = os.path.join(ZONGHE, "kb_meta.json")
OUT_PATH = os.path.join(ZONGHE, "answers_remake.json")

REFL_JS = re.compile(r"(^|[^A-Za-z0-9])[A-E]([、，,和与及 ]|项|的|对|错|$)")

OCR_REPLACES = [
    ("属千", "属于"), ("由千", "由于"), ("对千", "对于"), ("位千", "位于"), ("在千", "在于"),
    ("高千", "高于"), ("低千", "低于"), ("便千", "便于"), ("利千", "利于"), ("关千", "关于"),
    ("先千", "先于"), ("仅千", "仅于"), ("源千", "源于"), ("基千", "基于"), ("归千", "归于"),
    ("止千", "止于"), ("终千", "终于"), ("大千", "大于"), ("小千", "小于"), ("多千", "多于"),
    ("少千", "少于"), ("过千", "过于"), ("用千", "用于"), ("胜千", "胜于"), ("敢千", "敢于"),
    ("千元朝", "于元朝"), ("进人", "进入"), ("出人", "出入"), ("纳人", "纳入"), ("落人", "落入"),
    ("加人", "加入"), ("嵌人", "嵌入"), ("侵人", "侵入"), ("投人", "投入"), ("买人", "买入"),
    ("购人", "购入"), ("输人", "输入"), ("收人", "收入"), ("吸人", "吸入"), ("载人", "载入"),
    ("列人", "列入"), ("并人", "并入"), ("带人", "带入"), ("人罪", "入罪"), ("出人罪", "出入罪"),
    ("自已", "自己"), ("已身", "己身"), ("已任", "己任"), ("建立咋", "建立在"), ("咋", "在"),
    ("知识的、观点、", "知识、观点、"), ("知识和行李的总称", "知识和心理的总称"),
    ("行李的总称", "心理的总称"), ("首恶比办", "首恶必办"), ("胁从者不问", "胁从不问"),
    ("行事立法", "刑事立法"), ("明例", "名例"), ("据库", "厩库"), ("扇形", "擅兴"),
    ("斗松", "斗讼"), ("大清新型律", "大清新刑律"), ("斩行章程", "暂行章程"),
    ("總麻", "缌麻"), ("渊淜", "渊源"), ("大浩", "大诰"), ("兼桃", "兼祧"),
    ("答刑", "笞刑"), ("答掠", "笞掠"), ("答五十", "笞五十"), ("答一百", "笞一百"),
    ("魏微", "魏徵"), ("病狂督", "病狂昏"), ("達斩", "遂斩"), ("催用劳动", "雇佣劳动"),
    ("一中遍及", "一种遍及"), ("有于审判独立", "有悖于审判独立"), ("从新指定", "重新制定"),
    ("社会福利意识", "社会意识"), ("文运法", ""), ("海瑞", "海瑞"),
    ("一、单向选择题", ""), ("二、多向选择题", ""),
    ("儿个", "几个"), ("儿十", "几十"), ("一定式的权利", "一定的权利"),
    ("规定人们有权做一定\"可为模式\"行为或不做一定行为的规则,即规定人们的\"的规则", "规定人们有权做一定行为或不做一定行为的规则，即规定“可为模式”的规则"),
    ("规定人们有权做一定 \" 可为模式\"行为或不做一定行为的规则,即规定人们的 \"的规则", "规定人们有权做一定行为或不做一定行为的规则，即规定“可为模式”的规则"),
    ("规定人们有权做一定\" 可为模行为或不做一定行为的规则,即规定人们的 \"的规则", "规定人们有权做一定行为或不做一定行为的规则，即规定“可为模式”的规则"),
    ("有权做一定\" 可为模行为或不做一定行为的规则,即规定人们的 \"的规则", "有权做一定行为或不做一定行为的规则，即规定“可为模式”的规则"),
    ("有权做一定 \" 可为模行为或不做一定行为的规则,即规定人们的 \"的规则", "有权做一定行为或不做一定行为的规则，即规定“可为模式”的规则"),
    ("赋予人们以一定式的权利", "赋予人们以一定的权利"),
    ("赋予人们以一定 式的权利", "赋予人们以一定的权利"),
    ("卡尔•冯•萨维尼", "卡尔·冯·萨维尼"), ("托马斯•霍布斯", "托马斯·霍布斯"),
    ("陈发危害国家安全", "惩罚危害国家安全"), ("权力形态见。", "权力形态。"),
]

JUNK_RES = [
    re.compile(r"更多考研精品资料[^。\n]*"),
    re.compile(r"[-—]\s*\d{1,3}\s*[-—]\s*\]?"),
    re.compile(r"(?m)^\s*[\]\)】〕]\s*"),
    re.compile(r"修订提示[:：]\s*[A-D]{1,4}\s*[（(]原答案为\s*[A-D]{1,4}\s*[）)]\s*[\]】）)]?\s*"),
    re.compile(r"[（(]?原答案为\s*[A-D]{1,4}\s*[）)]?\s*[\]】]?\s*"),
    re.compile(r"【解析】\s*|【答案】\s*[A-D]{1,4}\s*"),
]

BARE_ANS_RE = re.compile(
    r"^(?:因此|故|所以|综上|可见|据此)?[，,]?\s*(?:本题)?(?:的)?(?:正确)?(?:答案|选项)(?:应|就)?(?:为|是|选|全选)?\s*[:：]?\s*[A-D、,，和与及 ]{1,14}\s*(?:项)?\s*(?:全选)?\s*[。．.]?\s*$"
)
CONCL_START = re.compile(r"(故选|答案为|答案选|本题答案|正确答案|应选|正确选项为|答案是|故本题选|本题选|本题[A-D]+项全选)")
CITE_RE = re.compile(r"《[^》]{2,34}》(?:第[〇一二三四五六七八九十百零\d]+条(?:第[〇一二三四五六七八九十百零\d]+款)?)?")

VERDICT_WORD = r"(?:均|都|皆|全)?(?:表述|说法|观点)?(?:均|都)?(?:正确|错误|不成立|成立|符合题意|不符合题意|符合|不符合|不当|不准确|准确|恰当|合法|违法|当选|不选|应选|不可选|排除)"
# 后缀判语：...，(因此)? (选项)? A(、B)? (选项|项)? 错误/正确
SUFFIX_MARK = re.compile(
    rf"(?:[,，;；]\s*(?:因此|所以|故|可见|据此)?\s*|(?<![A-Za-z0-9]))(?:选项)?\s*([A-D](?:\s*[、,，和与及]\s*[A-D])*)\s*(?:选项|项)?\s*{VERDICT_WORD}(?![\u4e00-\u9fff])"
)
# 前缀判语：(选项)? A(、B)? (选项|项)? 错误/正确[,，：:] ... 或 A 因果颠倒，...
PREFIX_MARK = re.compile(
    rf"^\s*(?:选项)?\s*([A-D](?:\s*[、,，和与及]\s*[A-D])*)\s*(?:选项|项)?\s*(?:中|的)?\s*(?:{VERDICT_WORD}|因果颠倒|明显不符合题意|说法过于绝对|表述有误|表述准确)?[，,：:、\s]+"
)


def norm_ans(raw):
    return "".join(sorted({c.upper() for c in re.sub(r"[^A-Da-d]", "", str(raw or ""))}))


def despac(t):
    t = re.sub(r"(?<=[\u4e00-\u9fff，。；：、）】》“”])\s+(?=[\u4e00-\u9fff“（《])", "", t)
    t = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-D]\s*选项)", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"“\s+", "“", t)
    t = re.sub(r"\s+”", "”", t)
    return t.strip()


def clean_prose(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    t = despac(t)
    for k, v in OCR_REPLACES:
        t = t.replace(k, v)
    for p in JUNK_RES:
        t = p.sub("", t)
    t = re.sub(r"^\s*[\]\)】〕、,，。]+\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return despac(t)


def split_units(text):
    """按句号、分号及『选项A错误，』『，A项正确。』边界精准切分文本单元。"""
    # 在 ", 选项A 错误" 或 "；B 正确" 前插分隔符
    t = re.sub(
        r"(?<=[。；;！!？?])\s*|[,，]\s*(?=(?:因此|所以|故|据此)?[，,]?\s*(?:选项)?\s*[A-D](?:\s*[、,，和与及]\s*[A-D])*\s*(?:选项|项)?\s*(?:中|的|" + VERDICT_WORD + "|明显|因果))",
        "\n", text
    )
    # 在 "A项正确，" 这类前缀判语与后面正文之间，若紧跟同一选项的句内说明则保留同行，若后面跟另一段不同句号单元已被 \n 切分
    out = []
    for seg in t.split("\n"):
        seg = seg.strip(" \t\r\n")
        if seg:
            out.append(seg)
    return out


def extract_option_reasons(text, opts):
    """双向提取每个选项 A/B/C/D 的实质解析：支持前缀标号、后缀标号、句内多标号与关键词匹配。"""
    units = split_units(text)
    got_specific = {}
    got_group = {}

    for i, u in enumerate(units):
        if BARE_ANS_RE.match(u):
            continue
        # 1. 后缀标号优先：看句尾/句中是否有 "...，A项错误" 或 "...，A、C正确"
        s_marks = list(SUFFIX_MARK.finditer(u))
        if s_marks:
            prev = 0
            for m in s_marks:
                before = u[prev:m.start()].strip(" ,，;；。")
                prev = m.end()
                letters = re.findall(r"[A-D]", m.group(1))
                # 若 before 为空但前面 units[i-1] 是单纯说理句（如 "..., A项错误" 前被逗号拆开），拼回上一句
                if not before and i > 0 and not SUFFIX_MARK.search(units[i - 1]) and not re.match(r"^\s*(?:选项)?[A-D]", units[i - 1]):
                    before = units[i - 1].strip(" ,，;；。")
                # 清理开头可能残留的 "选项B 正确" 或 "选项A 中"
                before = re.sub(r"^\s*(?:因此|所以|故|据此|此外|另|而|但)?[，,]?\s*(?:选项)?[A-D](?:\s*[、,，和与及]\s*[A-D])*\s*(?:选项|项)?\s*(?:中|的)?\s*(?:" + VERDICT_WORD + r")?[，,:：]?\s*", "", before).strip(" ,，;；。")
                if len(before) >= 6 and not re.fullmatch(r"(?:正确|错误|当选|不选|符合|不符合|成立|不成立)(?:项|选项)?", before):
                    target = got_specific if len(letters) == 1 else got_group
                    for L in letters:
                        target.setdefault(L, before)
            # 若最后标号之后还有紧接的解释（如 "选项C 正确，比如刑法对于..."）
            tail = u[prev:].strip(" ,，;；。")
            if tail and len(tail) >= 8 and s_marks:
                last_letters = re.findall(r"[A-D]", s_marks[-1].group(1))
                if len(last_letters) == 1 and last_letters[0] not in got_specific:
                    got_specific[last_letters[0]] = tail
            continue

        # 2. 前缀标号：如 "B 错误，西汉经学兴盛，法学未独立" 或 "选项A中“...”错误"
        pm = PREFIX_MARK.match(u)
        if pm:
            letters = re.findall(r"[A-D]", pm.group(1))
            body = u[pm.end():].strip(" ,，;；。")
            body = re.sub(r"^(?:是|为)?(?:正确|错误|不当|不成立|成立|符合题意|不符合题意)[的，,：:\s]*", "", body).strip(" ,，;；。")
            if len(body) >= 6:
                target = got_specific if len(letters) == 1 else got_group
                for L in letters:
                    target.setdefault(L, body)

    # 合并 single + group
    merged = dict(got_group)
    merged.update(got_specific)

    # 3. 对尚未匹配到的选项，按『最专属于该选项』的句段匹配（比较该句与四个选项的重叠度，避免张冠李戴）
    sents_all = [x.strip() for x in re.split(r"(?<=[。；！？;])", text) if x.strip()]
    opt_norms = {
        L: re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", (opts or {}).get(L, ""))
        for L in "ABCD"
    }
    STOP_2G = {"下列", "关于", "表述", "说法", "正确", "的是", "法律", "制度", "规定", "原则", "主要", "行为", "社会", "国家", "应当", "可以", "不是", "属于", "没有"}

    def _sent_opt_score(s_norm, o_norm):
        if len(o_norm) < 2:
            return 0
        # 优先看最长公共连续子串
        best_sub = 0
        for size in (12, 10, 8, 6, 4, 3):
            if len(o_norm) < size:
                continue
            for idx in range(0, len(o_norm) - size + 1):
                sub = o_norm[idx:idx + size]
                if sub in STOP_2G:
                    continue
                if sub in s_norm:
                    best_sub = size
                    break
            if best_sub:
                break
        # 加上 2 字词重叠奖励
        grams = {o_norm[i:i + 2] for i in range(max(0, len(o_norm) - 1))} - STOP_2G
        g_hits = sum(1 for g in grams if g in s_norm)
        return best_sub * 3 + g_hits

    for L in "ABCD":
        if L in merged:
            continue
        best_c = ""
        best_sc = 0
        for s in sents_all:
            if BARE_ANS_RE.match(s) or not (8 <= len(s) <= 240):
                continue
            # 跳过已显式属于其他选项字母的句段
            if PREFIX_MARK.match(s) or SUFFIX_MARK.search(s):
                ls_in_s = set(re.findall(r"[A-D]", " ".join(
                    (PREFIX_MARK.findall(s) or []) + (SUFFIX_MARK.findall(s) or [])
                )))
                if ls_in_s and L not in ls_in_s:
                    continue
            s_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
            scores = {L2: _sent_opt_score(s_norm, opt_norms[L2]) for L2 in "ABCD"}
            my_sc = scores[L]
            other_max = max(scores[L2] for L2 in "ABCD" if L2 != L)
            # 必须确实命中至少一个 3字词 或 2个有效2-gram，且严格优于其他三个选项
            if my_sc >= 9 and my_sc > other_max and my_sc > best_sc:
                best_sc = my_sc
                best_c = s
        if best_c:
            merged[L] = best_c

    return merged, sents_all, _sent_opt_score, opt_norms


def strip_opt_refs(text, opts=None):
    """彻底移除非选项行中的孤立选项字母 A-E，确保 0 条 REFL 乱序冲突。"""
    t = text
    # 1. 删除句尾“故选A”“故本题选BCD”等
    t = re.sub(r"[，,;；。]?\s*(?:因此|所以|故|综上|据此|可见)?[，,]?\s*(?:本题)?(?:的)?(?:正确)?(?:答案|选项)(?:应|就)?(?:为|是|选|全选)?\s*[:：]?\s*[A-D、,，和与及项项 ]+\s*(?:全选)?[。．.]?\s*$", "。", t)
    t = re.sub(r"(?:故选|应选|答案选|答案为|本题选|故答案选|正确答案是|正确答案为|故本题选择|本题选择)\s*[A-D、,，和与及项 ]+[。．.]?", "", t)
    # 2. 如果句子里有 "选项A/B/C/D"，优先替换为对应选项短文本（若提供 opts），否则替换为“该表述”
    def _opt_txt(m):
        ls = re.findall(r"[A-D]", m.group(0))
        if opts and len(ls) == 1 and opts.get(ls[0]):
            o = re.sub(r"[《》“”]", "", opts[ls[0]]).strip(" 。，；")
            if 2 <= len(o) <= 18:
                return f"“{o}”"
        return "相关表述"

    t = re.sub(r"(?:因此|所以|故|据此|综上|可见)?[，,]?\s*(?:选项)?\s*[A-D](?:\s*[、,，和与及/]\s*[A-D])*\s*(?:选项|项)?\s*(?:均|都|皆|全)?\s*(?:表述|说法)?(?:正确|错误|不成立|成立|符合|不符合|不当|不准确|当选|不选|应选|全选|明显不符合题意)[。；，,]?", "", t)
    t = re.sub(r"(?<![A-Za-z0-9])(?:选项)?\s*[A-D](?:\s*[、,，和与及/]\s*[A-D])*\s*(?:选项|项)\s*(?:中|的)?", _opt_txt, t)
    t = re.sub(r"(?<![A-Za-z0-9])(?:选项)\s*[A-D](?:\s*[、,，和与及/]\s*[A-D])*", _opt_txt, t)
    # 3. 处理如 "A 因果颠倒..."（前缀孤立字母+空格）
    t = re.sub(r"(^|[；;。！？\s])([A-D])\s+(?=[\u4e00-\u9fff])", lambda m: m.group(1) + (_opt_txt(m) + "：" if opts and opts.get(m.group(2)) and len(opts[m.group(2)]) <= 16 else ""), t)
    # 4. 兜底：只要仍能命中 REFL_JS，就把该孤立字母换成“该项”
    def _rep_refl(m):
        return (m.group(1) or "") + "该项" + (m.group(2) if m.group(2) in ("、", "，", ",", "和", "与", "及", "的", "对", "错", " ") else "")
    while REFL_JS.search(t):
        nt = REFL_JS.sub(_rep_refl, t)
        if nt == t:
            break
        t = nt
    t = re.sub(r"[。；]{2,}", "。", t)
    t = re.sub(r"[，,]{2,}", "，", t)
    t = re.sub(r"[;；]\s*。", "。", t)
    t = re.sub(r"^[，,；;。.\s]+", "", t)
    return t.strip()


def trim_reason(text, limit=95):
    t = strip_opt_refs(despac(text)).strip(" 。；，,")
    t = re.sub(r"^(?:因此|所以|故|可见|综上|但是|而|另外|此外|其中|据此|由此可见|这里|即)[,，]?\s*", "", t)
    t = re.sub(r"^(?:该表述中|该项中|该表述|相关表述中|相关表述|该项|中)[，,:：\s]*", "", t)
    t = re.sub(r"[,，;；]?\s*(?:说法|表述|观点)?(?:均|都)?(?:正确|错误|当选|不选|对|错|不准确|不当)[。；;]?$", "", t).strip(" 。；;，,")
    if len(t) > limit:
        cut = t[:limit]
        idx = max(cut.rfind("。"), cut.rfind("；"), cut.rfind("，"))
        t = cut[:idx] if idx >= int(limit * 0.48) else cut + "…"
    return t.strip(" 。；;，,")


def highlight_inline(t):
    if "\x01" in t:
        return t
    t = CITE_RE.sub(lambda m: f"\x01{m.group(0)}\x02", t)
    if "\x01" not in t:
        t = re.sub(r"“([^”]{2,18})”", lambda m: f"\x01“{m.group(1)}”\x02", t, count=1)
    return t


def make_conclusion(sents, ans, opts):
    cands = []
    for s in sents:
        if BARE_ANS_RE.match(s) or CONCL_START.search(s):
            continue
        sc = strip_opt_refs(s, opts).strip(" 。，；;:,：")
        sc = re.sub(r"^本题考查(?:的是)?", "", sc).strip(" ：:，。；;")
        if 10 <= len(sc) <= 88:
            cands.append(sc)
    for c in cands:
        c2 = re.sub(r"^(?:因此|所以|故|据此|综上|可见)[，,\s]*(?:相关表述|该表述)?[，,\s]*", "", c).strip(" ：:，。；;")
        if c2 and not re.match(r"^(?:首先|其次|再次|另|此外)[，,\s]", c2) and any(k in c2 for k in ("核心", "主要", "指", "属于", "包括", "规定", "确立", "体现", "原则", "特征", "本质")):
            return c2.rstrip("。；;，,") + "。"
    for c in cands:
        c2 = re.sub(r"^(?:因此|所以|故|据此|综上|可见|首先|其次|再次)[，,\s]*(?:相关表述|该表述)?[，,\s]*", "", c).strip(" ：:，。；;")
        if len(c2) >= 10:
            return c2.rstrip("。；;，,") + "。"
    if len(ans) == 1 and opts.get(ans):
        return f"依据题干考查要点，正确表述为“{opts[ans][:32]}”。"
    return "依据题干与现行制度规定综合判断作答。"


def shape_auto(q, raw_ans):
    a = norm_ans(raw_ans.get("a"))
    text = clean_prose(raw_ans.get("e") or "")
    opts = q.get("options") or {}
    if not text:
        return {"a": a, "e": ""}

    per, sents, score_fn, opt_norms = extract_option_reasons(text, opts)
    concl = make_conclusion(sents, a, opts)
    ask_positive = not bool(re.search(r"(不正确|错误|不能成立|不成立|不属于|不包括|不恰当|违反)", q["stem"]))

    opt_lines = []
    used_bodies = set()
    used_norms = []
    for L in "ABCD":
        mark = "✓" if L in a else "✗"
        body = per.get(L) or ""
        if body:
            r = trim_reason(body)
            dup = r in used_bodies and (L not in a or any(L2 not in a for L2 in per if per.get(L2) == body))
            if r and len(r) >= 6 and not dup:
                used_bodies.add(r)
                used_norms.append(re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", r))
                opt_lines.append(f"{L}{mark} {highlight_inline(r)}")
                continue
        # 若正确项缺具体条，仅从“非他项专用、无反证批判语气、且确实与本选项或题干主旨契合”的句子中找阐释句
        if L in a:
            picked = ""
            stem_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", q["stem"])
            for s in sents:
                if BARE_ANS_RE.match(s):
                    continue
                if PREFIX_MARK.match(s) or SUFFIX_MARK.search(s):
                    ls_in_s = set(re.findall(r"[A-D]", " ".join(
                        (PREFIX_MARK.findall(s) or []) + (SUFFIX_MARK.findall(s) or [])
                    )))
                    if ls_in_s and L not in ls_in_s:
                        continue
                if ask_positive and re.search(r"(并非|并不是|不可能|说法错误|夸大了|不符合题意|混淆了)", s):
                    continue
                s_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
                scores = {L2: score_fn(s_norm, opt_norms[L2]) for L2 in "ABCD"}
                if max(scores[L2] for L2 in "ABCD" if L2 != L) > 0 and max(scores[L2] for L2 in "ABCD" if L2 != L) >= scores[L]:
                    continue
                # 若本句根本不含正确选项自身词也不含题干核心词（即可能是列举别的学者/制度的句子），跳过
                if scores[L] < 6 and score_fn(s_norm, stem_norm) < 9:
                    continue
                r2 = trim_reason(s)
                r2_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", r2)
                if len(r2) >= 10 and r2 not in used_bodies and r2.strip("。") != concl.strip("。") and not any(r2_norm == u for u in used_norms):
                    picked = r2
                    break
            if picked:
                used_bodies.add(picked)
                used_norms.append(re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", picked))
                opt_lines.append(f"{L}{mark} {highlight_inline(picked)}")
                continue
        o_short = re.sub(r"^[《“]|([》”])?$", "", opts.get(L, ""))[:18]
        if L in a:
            opt_lines.append(f"{L}{mark} 符合题意及现行制度规定（\x01{o_short}\x02）")
        else:
            opt_lines.append(f"{L}{mark} 与题干设问或现行制度要件不符，故不选")

    bottom_sents = []
    concl_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", concl)
    for s in sents:
        if BARE_ANS_RE.match(s):
            continue
        sc = strip_opt_refs(s, opts)
        sc = re.sub(r"^本题考查(?:的是)?[^。]{2,22}[。]?\s*", "", sc).strip()
        if not sc or len(sc) < 8:
            continue
        sc_norm = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", sc)
        # 跳过已经原封不动放进首行结论或某条选项分析里的句子（避免底部冗余重复）
        if sc_norm == concl_norm or any(sc_norm and (sc_norm in u or u in sc_norm) and abs(len(sc_norm) - len(u)) <= 10 for u in used_norms):
            continue
        if sc not in bottom_sents:
            bottom_sents.append(sc)
    bottom = " ".join(bottom_sents).strip()
    if len(bottom) > 650:
        cut = bottom[:650]
        i = max(cut.rfind("。"), cut.rfind("；"))
        bottom = cut[:i + 1] if i > 300 else cut + "…"
    bottom = highlight_inline(bottom)

    lines = [f"\x01{concl}\x02"] + opt_lines
    if bottom:
        lines.append(bottom)
    return {"a": a, "e": "\n".join(lines)}


def pick_kb_and_kh(q, exp_text, kb_texts, kb_meta):
    sub = q["subject"]
    node = q["node"]
    blob = " ".join([
        q["stem"],
        " ".join((q.get("options") or {}).values()),
        exp_text.replace("\x01", "").replace("\x02", ""),
    ])
    cands = [m for m in kb_meta if m["sub"] == sub]
    best_idx = cands[0]["idx"]
    best_score = -1
    best_kws = []

    for m in cands:
        card = kb_texts[m["idx"]]
        score = 20 if m["node"] == node else 0
        hits = []
        for kw in m["kws"]:
            if kw in blob:
                score += 6 + len(kw)
                hits.append(kw)
        for tok in set(re.findall(r"《[^》]{2,16}》|“[^”]{2,12}”", blob)):
            t_s = tok.strip("《》“”")
            if t_s in card:
                score += 8
                hits.append(t_s)
        for phrase in re.findall(r"[\u4e00-\u9fff]{3,6}", q["stem"] + " ".join((q.get("options") or {}).values())):
            if phrase in card:
                score += 3
                hits.append(phrase)
        if score > best_score:
            best_score = score
            best_idx = m["idx"]
            best_kws = hits

    card = kb_texts[best_idx]
    spans = []
    pos = 0
    for seg in re.split(r"(?<=[。；\n])", card):
        if not seg:
            continue
        s_len = len(seg)
        seg_s = seg.strip()
        if len(seg_s) >= 8:
            sc = 0
            for kw in best_kws:
                if kw in seg_s:
                    sc += 5 + len(kw)
            for phrase in re.findall(r"[\u4e00-\u9fff]{2,5}", q["stem"] + " ".join((q.get("options") or {}).values())):
                if phrase in seg_s and phrase not in ("下列关于", "表述正确", "正确的是", "不正确的", "下列说法", "我国现行"):
                    sc += 2
            if sc > 0:
                start = pos + (len(seg) - len(seg.lstrip()))
                end = pos + len(seg.rstrip())
                spans.append((sc, start, end))
        pos += s_len

    spans.sort(key=lambda x: (-x[0], x[1]))
    chosen = []
    for _, s_i, e_i in spans[:2]:
        if all(not (s_i < pe and e_i > ps) for ps, pe in chosen):
            chosen.append([s_i, e_i])
    chosen.sort()

    if not chosen:
        first_nl = card.find("\n")
        start = first_nl + 1 if 0 <= first_nl < len(card) - 10 else 0
        end = min(len(card), card.find("。", start) + 1 if card.find("。", start) > start else start + 80)
        chosen = [[start, end]]

    return best_idx, chosen


def main():
    tagged = json.load(open(TAGGED_PATH, encoding="utf-8"))
    raw_ans = json.load(open(ANS_PATH, encoding="utf-8"))
    man_ans = json.load(open(MANUAL_PATH, encoding="utf-8")) if os.path.exists(MANUAL_PATH) else {}
    man_rm = json.load(open(MANUAL_RM_PATH, encoding="utf-8")) if os.path.exists(MANUAL_RM_PATH) else {}
    amend = json.load(open(AMEND_PATH, encoding="utf-8")) if os.path.exists(AMEND_PATH) else {}
    kb_texts = json.load(open(KB_PATH, encoding="utf-8"))
    kb_meta = json.load(open(KB_META_PATH, encoding="utf-8"))

    ans_map = {k: dict(v) for k, v in raw_ans.items() if not k.startswith("_")}
    for k, v in man_ans.items():
        if not k.startswith("_") and isinstance(v, dict) and v.get("a"):
            ans_map[k] = dict(ans_map.get(k, {}), **v)

    out = {}
    refl_bad = []
    real_opt_reasons = 0
    total_opt_lines = 0

    for q in tagged:
        if q["type"] not in ("单项选择", "多项选择"):
            continue
        qid = f"{q['year']}-{q['num']}"
        a_obj = ans_map.get(qid)
        if not a_obj:
            raise RuntimeError(f"Missing answer key for {qid}")

        if qid in man_rm and man_rm[qid].get("e"):
            shaped = {"a": norm_ans(a_obj["a"]), "e": man_rm[qid]["e"]}
        else:
            shaped = shape_auto(q, a_obj)

        e_text = shaped["e"]
        if qid in amend and amend[qid]:
            note = amend[qid].strip()
            e_text = (e_text + "\n" + note).strip()

        if e_text.count("\x01") != e_text.count("\x02"):
            raise ValueError(f"{qid}: mismatched \\x01/\\x02 in explanation: {e_text!r}")

        for line in e_text.split("\n"):
            if not re.match(r"^\s*[A-E][✓✗]", line):
                clean_line = line.replace("\x01", "").replace("\x02", "")
                if REFL_JS.search(clean_line):
                    refl_bad.append((qid, clean_line))
            else:
                total_opt_lines += 1
                if not re.search(r"(与题干设问或现行制度要件不符|符合题意及现行制度规定)", line):
                    real_opt_reasons += 1

        kb_idx, kh_spans = pick_kb_and_kh(q, e_text, kb_texts, kb_meta)
        out[qid] = {"e": e_text, "kb": kb_idx, "kh": kh_spans}

    json.dump(out, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"Generated {len(out)} remade explanations -> {os.path.relpath(OUT_PATH, ROOT)}")
    print(f"Substantive option lines: {real_opt_reasons}/{total_opt_lines} ({100*real_opt_reasons/total_opt_lines:.1f}%)")
    print(f"REFL safety failures: {len(refl_bad)}")
    for qid, ln in refl_bad[:10]:
        print("  REFL:", qid, ln)


if __name__ == "__main__":
    main()
