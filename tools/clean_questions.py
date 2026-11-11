#!/usr/bin/env python3
"""加载并清洗 1,099 道客观真题（应用 question_fixes.json、node_overrides.json 及系统性 OCR/水印清洗）。"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGGED_PATH = os.path.join(ROOT, "data", "tagged.json")
EXCLUDE_PATH = os.path.join(ROOT, "data", "exclude_questions.json")
FIXES_PATH = os.path.join(ROOT, "data", "question_fixes.json")
OVERRIDES_PATH = os.path.join(ROOT, "data", "node_overrides.json")

# 通用 OCR / 错字归一规则（不误伤正常词）
OCR_REPLACES = [
    # 千 -> 于
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
    # 人 -> 入
    ("进人", "进入"),
    ("投人", "投入"),
    ("收人", "收入"),
    ("植人", "植入"),
    ("出人", "出入"),
    ("落人", "落入"),
    ("侵人", "侵入"),
    ("介人", "介入"),
    ("并人", "并入"),
    ("深人", "深入"),
    ("输人", "输入"),
    ("加人", "加入"),
    ("嵌人", "嵌入"),
    ("人室", "入室"),
    ("人狱", "入狱"),
    ("人境", "入境"),
    ("人户", "入户"),
    ("人伙", "入伙"),
    ("推人", "推入"),
    ("驶人", "驶入"),
    ("坠人", "坠入"),
    ("倒人", "倒入"),
    ("转人", "转入"),
    ("纳人", "纳入"),
    ("注人", "注入"),
    ("卷人", "卷入"),
    # 已 -> 己
    ("自已", "自己"),
    ("已方", "己方"),
    ("已身", "己身"),
    ("已见", "己见"),
    # 常见形近错别字
    ("室息", "窒息"),
    ("间谋", "间谍"),
    ("衣户", "农户"),
    ("遗瞩", "遗嘱"),
    ("强好", "强奸"),
    ("未得遥", "未得逞"),
    ("特救", "特赦"),
    ("既救", "既赦"),
    ("又救", "又赦"),
    ("宜告", "宣告"),
    ("孽息", "孳息"),
    ("教咬", "教唆"),
    ("合吲", "合同"),
    ("即遂", "既遂"),
    ("感清", "感情"),
    ("玩要", "玩耍"),
    ("物法权", "物权法"),
    ("侦务", "债务"),
    ("分但", "分担"),
    ("元期徒刑", "无期徒刑"),
    ("追溯期限", "追诉期限"),
    ("徇私枉法紫", "徇私枉法罪"),
    ("增殖税", "增值税"),
    ("合仪庭", "合议庭"),
    ("酪配大醉", "酩酊大醉"),
    ("早请仲裁", "申请仲裁"),
    ("签汀", "签订"),
    ("自行行车", "自行车"),
    ("入员", "人员"),
    ("3入", "3人"),
    ("罄粟", "罂粟"),
    ("蔬忽", "疏忽"),
    ("适用千", "适用于"),
    ("寻畔滋事", "寻衅滋事"),
    ("寻滋事罪", "寻衅滋事罪"),
    ("非发拘禁", "非法拘禁"),
    ("淫移", "淫秽"),
    ("竟合", "竞合"),
    ("狠亵", "猥亵"),
    ("那一种", "哪一种"),
    ("受款", "收款"),
    ("枚利人", "权利人"),
    ("英榜", "英镑"),
    ("人园", "入园"),
    ("潜人", "潜入"),
]

# 2023 真题独有水印残留（行尾或空格隔开的孤立字/短串）
WM_2023_TAIL = re.compile(
    r"(?:\s+(?:车频\s*尚|霖特品|照品|视\s*频|讲\s*解|现\s*预|视频|讲解|视|频|讲|解|口|可|税|品))+\s*$"
)
WM_2023_MID = re.compile(
    r"(?<=[\u4e00-\u9fff，。、；：！？（）“”《》])\s+(?:车频\s*尚|霖特品|照品|视频|讲解|口\s*视\s*频|讲\s*解)\s+(?=[\u4e00-\u9fff，。、；：！？（）“”《》])"
)

HEADER_GLUE = re.compile(r"\s*20\d{2}年全国法律硕士.*$")
SUBQ_TAIL = re.compile(r"\s*[三九][、.．]\s*简答题.*$")

CJK_CHAR = r"\u4e00-\u9fff，。、；：！？（）“”《》【】"
INTRA_CJK_SPACE = re.compile(rf"([{CJK_CHAR}])\s+([{CJK_CHAR}])")


def normalize_text(text, year=None):
    s = str(text or "").strip()
    # 去掉粘连页眉与后续大题标题
    s = HEADER_GLUE.sub("", s)
    s = SUBQ_TAIL.sub("", s)
    if year == 2023:
        s = WM_2023_MID.sub("", s)
        s = WM_2023_TAIL.sub("", s)
    # 清除全角/中文之间因 PDF 换行产生的多余空格
    for _ in range(3):
        s = INTRA_CJK_SPACE.sub(r"\1\2", s)
    # 常见 OCR 错字替换
    for old, new in OCR_REPLACES:
        s = s.replace(old, new)
    s = re.sub(r"(?<!徇)私枉法罪", "徇私枉法罪", s)
    # 压缩多个空白为单个空格，再去掉标点前的误空格
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = re.sub(r"\s+([，。、；：！？）】”》])", r"\1", s)
    s = re.sub(r"([（【“《])\s+", r"\1", s)
    return s


def normalize_stem(stem, year=None):
    s = normalize_text(stem, year=year)
    # 清理末尾各种残缺/重复的括号碎片，如 "( (。" / ")." / "( 0。" / "(.。" / "(:·" / "()"
    s = re.sub(r"[（(][\s.:·0oO（()）]*[\s。．.,，]*$", "（ ）。", s)
    s = re.sub(r"(?<=[\u4e00-\u9fff：，是的有为属])\s*[)）][\s。．.,，]*$", "（ ）。", s)
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


def load_clean_questions():
    tagged = json.load(open(TAGGED_PATH, encoding="utf-8"))
    excluded = set(json.load(open(EXCLUDE_PATH, encoding="utf-8"))) if os.path.exists(EXCLUDE_PATH) else set()
    fixes = json.load(open(FIXES_PATH, encoding="utf-8")) if os.path.exists(FIXES_PATH) else {}
    overrides = json.load(open(OVERRIDES_PATH, encoding="utf-8")) if os.path.exists(OVERRIDES_PATH) else {}

    case_map = {}
    for grp in fixes.get("shared_cases", []):
        for qid in grp["ids"]:
            case_map[qid] = grp["case"].strip()
    patches = fixes.get("patches", {})

    cleaned = []
    for raw in tagged:
        if raw["type"] not in ("单项选择", "多项选择"):
            continue
        qid = f"{raw['year']}-{raw['num']}"
        if qid in excluded:
            continue
        q = {
            "id": qid,
            "year": raw["year"],
            "num": raw["num"],
            "subject": raw["subject"],
            "type": raw["type"],
            "score": raw["score"],
            "node": overrides.get(qid, raw["node"]),
            "stem": raw["stem"],
            "options": dict(raw["options"]),
        }
        p = patches.get(qid, {})
        if "stem" in p:
            q["stem"] = p["stem"]
        if "options" in p:
            for ok, ov in p["options"].items():
                q["options"][ok] = ov

        q["stem"] = normalize_stem(q["stem"], year=q["year"])
        for ok in "ABCD":
            q["options"][ok] = normalize_option(q["options"][ok], year=q["year"])

        if qid in case_map:
            q["case"] = case_map[qid]
            if not q["stem"].startswith("【案情】"):
                q["stem"] = f"【案情】{q['case']}\n{q['stem']}"

        cleaned.append(q)
    return cleaned


if __name__ == "__main__":
    qs = load_clean_questions()
    print(f"Loaded {len(qs)} clean objective questions.")
    # Audit
    issues = []
    for q in qs:
        s_plain = q["stem"].replace("（", "(").replace("）", ")")
        if s_plain.count("(") != s_plain.count(")"):
            issues.append(("PAREN", q["id"], q["stem"][-40:]))
        for field, val in [("stem", q["stem"])] + [(k, q["options"][k]) for k in "ABCD"]:
            if any(w in val for w in ["简答题", "法律硕士", "讲 解", "视 频", "霖特品", "照品", "车频"]):
                issues.append(("GLUE", q["id"], field, val[-40:]))
            if re.search(r"[0-9][lIO]|[lIO][0-9]|l万元|l千万元|l年", val):
                issues.append(("OCR_NUM", q["id"], field, val))
            if field != "stem" and len(val) > 75:
                issues.append(("LONG_OPT", q["id"], field, val))
            if re.search(r"[A-D][.．、]\S", val) and q["id"] != "2023-13":
                # check embedded next question/option
                if re.search(r"\d{1,2}\.\s*[\u4e00-\u9fff]|^[A-D]\.", val):
                    issues.append(("EMBED_OPT", q["id"], field, val))
    print(f"Audit issues found: {len(issues)}")
    for it in issues[:30]:
        print(" ", it)
    from collections import Counter
    units = Counter((q["subject"], q["node"]) for q in qs)
    print(f"Units: {len(units)}")
    for (sub, name), cnt in sorted(units.items(), key=lambda x: (x[0][0], -x[1])):
        print(f"  {sub} | {name:16s} | {cnt}")
