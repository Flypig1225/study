#!/usr/bin/env python3
"""加载并清洗 2005-2026 专业综合课 1,433 题（1,270 客观 + 163 主观）。"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q_PATH = os.path.join(ROOT, "data", "zonghe", "questions.json")
TAGGED_PATH = os.path.join(ROOT, "data", "zonghe", "tagged.json")
FIXES_PATH = os.path.join(ROOT, "data", "zonghe", "question_fixes.json")
OVERRIDES_PATH = os.path.join(ROOT, "data", "zonghe", "node_overrides.json")

OCR_REPLACES = [
    ("关千", "关于"),
    ("属千", "属于"),
    ("对千", "对于"),
    ("基千", "基于"),
    ("在千", "在于"),
    ("由千", "由于"),
    ("处千", "处于"),
    ("等千", "等于"),
    ("小千", "小于"),
    ("大千", "大于"),
    ("高千", "高于"),
    ("低千", "低于"),
    ("至千", "至于"),
    ("位千", "位于"),
    ("出千", "出于"),
    ("以千", "以于"),
    ("千是", "于是"),
    ("进人", "进入"),
    ("投人", "投入"),
    ("收人", "收入"),
    ("纳人", "纳入"),
    ("深人", "深入"),
    ("加人", "加入"),
    ("侵人", "侵入"),
    ("介人", "介入"),
    ("坠人", "坠入"),
    ("并人", "并入"),
    ("列人", "列入"),
    ("出境人境", "出境入境"),
    ("自已", "自己"),
    ("已方", "己方"),
    ("已身", "己身"),
    ("答刑", "笞刑"),
    ("答杖", "笞杖"),
    ("答、杖", "笞、杖"),
    ("易答", "易笞"),
    ("从答入杖", "从笞入杖"),
    ("答二十", "笞二十"),
    ("答五十", "笞五十"),
    ("答五百", "笞五百"),
    ("大浩", "大诰"),
    ("兼桃", "兼祧"),
    ("總麻", "缌麻"),
    ("伽号", "枷号"),
    ("东接和继受", "承接和继受"),
    ("没立的", "设立的"),
    ("那一种", "哪一种"),
    ("三风十您", "三风十愆"),
    ("囧", ""),
    ("冏", ""),
]

WM_2023_TAIL = re.compile(r"(?:\s+(?:车频\s*尚|霖特品|照品|烧品|视频|讲解|现\s*预))+\s*$")
RUBRIC_TAIL = re.compile(
    r"(?:\s*分[,，]共\s*\d+\s*分[。.]?\s*(?:下列每题.*?不得分[。.]?|要求结合所学.*?不得分[。.]?|要求结合所学.*?回答问题[。.]?|请将答案写在答题卡.*?内[。.]?)?"
    r"|\s*(?:下列每题给出的四个选项中.*?(?:不得分|涂黑)[。.]?|至少有两个选项是符合(?:题目|试题)要求的[。.]?多选.*?(?:不得分|涂黑)[。.]?|两个选项是符合(?:题目|试题)要求的[。.]?多选.*?(?:不得分|涂黑)[。.]?|要求的[。.]?(?:请在答题卡.*?(?:不得分|涂黑)|多选、少选或错选均不得分)\s*[)）]?)"
    r"|\s*(?:请将答案)?写在答题卡指定位置[^。]*[。.]?|\s*指定位置上\s*[)）]?)\s*$"
)
CJK_CHAR = r"\u4e00-\u9fff，。、；：！？（）“”《》【】"
INTRA_CJK_SPACE = re.compile(rf"([{CJK_CHAR}])\s+([{CJK_CHAR}])")


def normalize_text(text, year=None):
    s = str(text or "").strip()
    for _ in range(2):
        s = RUBRIC_TAIL.sub("", s)
    s = re.sub(r"\s*士?\(?(?:20\d{2}\s*年)?全国法律硕士.*$", "", s)
    if year == 2023:
        s = WM_2023_TAIL.sub("", s)
    for _ in range(3):
        s = INTRA_CJK_SPACE.sub(r"\1\2", s)
    for old, new in OCR_REPLACES:
        s = s.replace(old, new)
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"\s+([，。、；：！？）】”》])", r"\1", s)
    s = re.sub(r"([（【“《])\s+", r"\1", s)
    return s


def clean_unmatched_parens(s):
    """清除跨行导致的孤立右括号碎片，绝不误删合法的成对括号如（何）（一）（新疆）。"""
    # 若存在孤立 `)。` / `)` 在正文中间导致括号深度 < 0，删去这些多余的孤立右括号及紧随的句点
    out = []
    depth = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "(（":
            depth += 1
            out.append(ch)
            i += 1
        elif ch in ")）":
            if depth > 0:
                depth -= 1
                out.append(ch)
                i += 1
            else:
                # 孤立多余的 `)` 或 `)。`：跳过右括号，若后面紧跟 `。` 或 `.` 且不是整句末尾，也跳过
                i += 1
                if i < len(s) and s[i] in "。．." and i < len(s) - 1:
                    i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def normalize_stem(stem, year=None):
    s = normalize_text(stem, year=year)
    s = re.sub(r"\s*·\s*(?=[\u4e00-\u9fff])", "", s)
    s = s.replace(".·", "……")
    s = clean_unmatched_parens(s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"[（(][\s.:·0oO囧冏（()）]*[\s。．.,，]*(?:\s*要求的.*)?$", "（ ）。", s)
    s = re.sub(r"(?<=[\u4e00-\u9fff：，是的有为属在之])\s*[)）][\s。．.,，]*$", "（ ）。", s)
    s = re.sub(r"(是|有|为|指|于|的是|的有|称作|称为|属于|在于)\s*[。．.]?\s*$", r"\1（ ）。", s)
    s = re.sub(r"（\s*）\s*[。．.,，]?\s*$", "（ ）。", s)
    return s.strip()


def normalize_option(opt, year=None):
    s = normalize_text(opt, year=year)
    s = re.sub(r"^\.\s*", "", s)
    s = re.sub(r"\s*[·.]+\s*$", "", s)
    p = s.replace("（", "(").replace("）", ")")
    if p.count(")") > p.count("("):
        s = re.sub(r"\s*[)）]\s*$", "", s)
    return s.strip()


def load_clean_questions(include_subjective=False):
    src = TAGGED_PATH if os.path.exists(TAGGED_PATH) else Q_PATH
    raw_list = json.load(open(src, encoding="utf-8"))
    fixes = json.load(open(FIXES_PATH, encoding="utf-8")) if os.path.exists(FIXES_PATH) else {}
    overrides = json.load(open(OVERRIDES_PATH, encoding="utf-8")) if os.path.exists(OVERRIDES_PATH) else {}
    patches = fixes.get("patches", {})

    out = []
    for raw in raw_list:
        is_obj = raw["type"] in ("单项选择", "多项选择")
        if not include_subjective and not is_obj:
            continue
        qid = f"{raw['year']}-{raw['num']}"
        q = {
            "id": qid,
            "year": raw["year"],
            "num": raw["num"],
            "subject": raw["subject"],
            "type": raw["type"],
            "score": raw["score"],
            "node": overrides.get(qid, raw.get("node", "")),
            "stem": raw["stem"],
            "options": dict(raw.get("options") or {}),
        }
        p = patches.get(qid, {})
        if "stem" in p:
            q["stem"] = p["stem"]
        if "options" in p:
            for ok, ov in p["options"].items():
                q["options"][ok] = ov

        q["stem"] = normalize_stem(q["stem"], year=q["year"]) if is_obj else normalize_text(q["stem"], year=q["year"])
        for ok in list(q["options"]):
            q["options"][ok] = normalize_option(q["options"][ok], year=q["year"])
        out.append(q)
    return out


if __name__ == "__main__":
    qs = load_clean_questions(include_subjective=True)
    obj = [q for q in qs if q["type"] in ("单项选择", "多项选择")]
    subj = [q for q in qs if q not in obj]
    print(f"Loaded {len(obj)} objective + {len(subj)} subjective = {len(qs)} clean 498 questions.")
    issues = []
    for q in obj:
        s_plain = q["stem"].replace("（", "(").replace("）", ")")
        if s_plain.count("(") != s_plain.count(")"):
            issues.append(("PAREN", q["id"], q["stem"][-45:]))
        for field, val in [("stem", q["stem"])] + [(k, q["options"][k]) for k in "ABCD"]:
            if any(w in val for w in ["简答题", "法律硕士", "多选、少选", "共20分", "共30分", "烧品", "照品", "车频"]):
                issues.append(("GLUE", q["id"], field, val[-45:]))
            if field != "stem" and len(val) > 85:
                issues.append(("LONG_OPT", q["id"], field, val))
    print("Audit issues:", len(issues))
    for it in issues:
        print(" ", it)
