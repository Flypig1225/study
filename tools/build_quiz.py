#!/usr/bin/env python3
"""把清洗后的 1,099 道客观题 + answers_remake.json + kb.json 生成单文件刷题页 quiz.html。

用法：
    python3 tools/build_quiz.py
    python3 tools/build_quiz.py --allow-missing
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from clean_questions import load_clean_questions  # noqa: E402

SHELL = os.path.join(ROOT, "刷题", "_shell.html")
OUT = os.path.join(ROOT, "quiz.html")
ANSWERS = os.path.join(ROOT, "data", "answers.json")
MANUAL = os.path.join(ROOT, "data", "answers_manual.json")
REMAKE = os.path.join(ROOT, "data", "answers_remake.json")
KB_PATH = os.path.join(ROOT, "data", "kb.json")

TCODE = {"单项选择": "单", "多项选择": "多", "判断题": "判"}
REFL_JS = re.compile(r"(^|[^A-Za-z0-9])[A-E]([、，,和与及 ]|项|的|对|错|$)")


def norm_answer(raw):
    s = re.sub(r"[^A-Da-d]", "", str(raw or ""))
    return "".join(sorted({c.upper() for c in s}))


def check_no_shuf(exp):
    for line in str(exp or "").split("\n"):
        if not re.match(r"^\s*[A-E][✓✗]", line):
            clean_line = line.replace("\x01", "").replace("\x02", "")
            if REFL_JS.search(clean_line):
                return clean_line
    return None


def build_data(allow_missing=False):
    questions = load_clean_questions()

    answers = {}
    if os.path.exists(ANSWERS):
        raw_ans = json.load(open(ANSWERS, encoding="utf-8"))
        for k, v in raw_ans.items():
            if not k.startswith("_"):
                answers[k] = dict(v)
    if os.path.exists(MANUAL):
        raw_man = json.load(open(MANUAL, encoding="utf-8"))
        for k, v in raw_man.items():
            if not k.startswith("_") and isinstance(v, dict) and v.get("a"):
                answers[k] = dict(answers.get(k, {}), **v)

    remake = {}
    if os.path.exists(REMAKE):
        remake = json.load(open(REMAKE, encoding="utf-8"))

    kb = []
    if os.path.exists(KB_PATH):
        kb = json.load(open(KB_PATH, encoding="utf-8"))

    missing_ans = []
    missing_remake = []
    units = {}

    for q in questions:
        qid = q["id"]
        ans = answers.get(qid) or {}
        a = norm_answer(ans.get("a"))
        if not a:
            missing_ans.append(qid)
            continue

        rm = remake.get(qid)
        if not rm or not rm.get("e"):
            missing_remake.append(qid)
            if not allow_missing:
                continue
            e_text = ans.get("e", "").strip() or "解析待补充。"
            kb_idx = None
            kh_spans = []
            k_text = q["node"]
        else:
            e_text = rm["e"]
            kb_idx = rm.get("kb")
            kh_spans = rm.get("kh") or []
            k_text = ""
            if kb_idx is not None:
                if not (0 <= kb_idx < len(kb)):
                    raise ValueError(f"{qid}: kb index {kb_idx} out of range (len={len(kb)})")
                klen = len(kb[kb_idx])
                for s_i, e_i in kh_spans:
                    if not (0 <= s_i < e_i <= klen):
                        raise ValueError(f"{qid}: kh span [{s_i},{e_i}] out of range for KB[{kb_idx}] len={klen}")

        # 校验 \x01 / \x02 成对
        if e_text.count("\x01") != e_text.count("\x02"):
            raise ValueError(f"{qid}: mismatched \\x01/\\x02 bold markers in explanation")

        # 校验选项乱序安全（不得在非选项行引用孤立字母 A-E）
        bad_refl = check_no_shuf(e_text)
        if bad_refl and not allow_missing:
            raise ValueError(f"{qid}: explanation triggers REFL noShuf: {bad_refl!r}")

        unit = units.setdefault((q["subject"], q["node"]), {
            "sub": q["subject"],
            "name": q["node"],
            "score": 0,
            "qs": [],
        })
        unit["score"] += q["score"]

        item = {
            "id": qid,
            "y": q["year"],
            "t": TCODE[q["type"]],
            "s": q["stem"],
            "o": [q["options"][k] for k in "ABCD"],
            "a": a,
            "e": e_text,
            "k": k_text,
        }
        if kb_idx is not None:
            item["kb"] = kb_idx
            item["kh"] = kh_spans
        unit["qs"].append(item)

    if missing_ans:
        raise RuntimeError(f"Missing answer keys for {len(missing_ans)} questions: {missing_ans[:10]}")
    if missing_remake and not allow_missing:
        raise RuntimeError(f"Missing remade explanations for {len(missing_remake)} questions: {missing_remake[:10]}")

    data = []
    for (subj, node), u in units.items():
        u["qs"].sort(key=lambda x: (x["y"], int(x["id"].split("-")[1])))
        data.append({
            "sub": subj,
            "name": node,
            "w": round(u["score"] / 22.0, 1),
            "L": len(u["qs"]),
            "qs": u["qs"],
        })
    # 与参考模板一致：全局按年均占分 w 降序排列（同 w 按题量降序、科目、名称）
    data.sort(key=lambda u: (-u["w"], -u["L"], u["sub"] != "刑法", u["name"]))
    return data, kb


def main():
    allow_missing = "--allow-missing" in sys.argv
    data, kb = build_data(allow_missing=allow_missing)

    shell = open(SHELL, encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    kb_payload = json.dumps(kb, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = shell.replace("/*__QUIZ_DATA__*/", payload).replace("/*__KB_DATA__*/", kb_payload)

    nq = sum(len(u["qs"]) for u in data)
    covered = sorted({q["y"] for u in data for q in u["qs"]})
    note = f"当前收录 {nq} 道客观真题（{covered[0]}–{covered[-1]}年，共 {len(data)} 个章节单元）。"
    html = html.replace("__COVERAGE__", note)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"章节 {len(data)} 个，题目 {nq} 道，KB {len(kb)} 条 -> {os.path.relpath(OUT, ROOT)} ({len(html)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
