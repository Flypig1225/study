#!/usr/bin/env python3
"""把 tagged.json + answers.json 生成为单文件刷题页 刷题/法硕基础课-真题刷题.html。

用法：
    python3 tools/build_quiz.py                 # 要求答案全覆盖
    python3 tools/build_quiz.py --allow-missing # 缺答案也生成（占位，仅用于验收界面）

answers.json 结构：
    {"2005-1": {"a": "A", "e": "解析正文…"}, "2005-21": {"a": "ABD", "e": "…"}}
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL = os.path.join(ROOT, "刷题", "_shell.html")
OUT = os.path.join(ROOT, "刷题", "法硕基础课-真题刷题.html")
TAGGED = os.path.join(ROOT, "data", "tagged.json")
ANSWERS = os.path.join(ROOT, "data", "answers.json")

TCODE = {"单项选择": "单", "多项选择": "多", "判断题": "判"}
CHAPTER_ORDER_HINT = {}  # 预留：如需固定章节顺序可在此填


def norm_answer(raw):
    """把各种写法的答案归一成 'A' / 'ABD' 形式。"""
    s = re.sub(r"[^A-Da-d]", "", str(raw or ""))
    return "".join(sorted({c.upper() for c in s}))


def clean_expl(text):
    """去掉解析里重复的『答案：X』抬头，压缩多余空行。"""
    t = str(text or "").strip()
    t = re.sub(r"^\s*[【\[]?\s*答案\s*[】\]]?\s*[:：]?\s*[A-Da-d,，、\s]*\n", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def build_data(tagged, answers, allow_missing=False):
    missing = []
    units = {}
    for q in tagged:
        if q["type"] not in TCODE:
            continue
        key = f"{q['year']}-{q['num']}"
        ans = answers.get(key) or {}
        a = norm_answer(ans.get("a"))
        if not a:
            missing.append(key)
        unit = units.setdefault((q["subject"], q["node"]), {
            "sub": q["subject"], "name": q["node"], "score": 0, "qs": []})
        unit["score"] += q["score"]
        unit["qs"].append({
            "id": key,
            "y": q["year"],
            "t": TCODE[q["type"]],
            "s": q["stem"].strip(),
            "o": [q["options"][k] for k in "ABCD"],
            "a": a,
            "e": clean_expl(ans.get("e")),
            "k": q["node"],
        })
    if missing and not allow_missing:
        print(f"缺少 {len(missing)} 条答案，先补 data/answers.json（示例：{missing[:5]}）")
        sys.exit(1)

    data = []
    for (subj, node), u in units.items():
        u["qs"].sort(key=lambda q: (q["y"], q["id"]))
        data.append({
            "sub": subj,
            "name": node,
            "w": round(u["score"] / 22.0, 1),   # 平均每年占分
            "L": len(u["qs"]),
            "qs": u["qs"],
        })
    data.sort(key=lambda u: (u["sub"] != "刑法", -sum(q["t"] != "判" for q in u["qs"]), u["name"]))
    return data, missing


def main():
    allow_missing = "--allow-missing" in sys.argv
    tagged = json.load(open(TAGGED, encoding="utf-8"))
    answers = {}
    if os.path.exists(ANSWERS):
        answers = json.load(open(ANSWERS, encoding="utf-8"))
        answers = {k: v for k, v in answers.items() if not k.startswith("_")}
    data, missing = build_data(tagged, answers, allow_missing)

    shell = open(SHELL, encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    html = shell.replace("/*__QUIZ_DATA__*/", payload)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    nq = sum(len(u["qs"]) for u in data)
    print(f"章节 {len(data)} 个，题目 {nq} 道 -> {os.path.relpath(OUT, ROOT)} "
          f"（{len(html)/1024/1024:.2f} MB）")
    if missing:
        print(f"警告：{len(missing)} 题答案为空，判分不可用：{missing[:5]} …")


if __name__ == "__main__":
    main()
