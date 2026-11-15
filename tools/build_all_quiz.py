#!/usr/bin/env python3
"""将 398 基础课（1,099 题）与 498 综合课（1,270 题）合并为单文件全科刷题页 quiz_all.html，
默认按 2027 考研预测考点比重排序，并支持按 22 年历史均分切换。

用法：
    python3 tools/build_all_quiz.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build_quiz import build_data as build_398  # noqa: E402
from zh_build_quiz import build_data as build_498  # noqa: E402
from predict_2027 import compute_unit_prediction  # noqa: E402

SHELL = os.path.join(ROOT, "刷题", "_shell_all.html")
OUT = os.path.join(ROOT, "quiz_all.html")

SUB_ORDER = {
    "刑法": 0,
    "民法": 1,
    "法理学": 2,
    "中国宪法学": 3,
    "中国法制史": 4,
}


def build_combined():
    d398, kb398 = build_398()
    d498, kb498 = build_498()

    kb_offset = len(kb398)
    kb_all = list(kb398) + list(kb498)

    units = []
    for ex, id_prefix, data, kb_shift in (
        ("398", "jc:", d398, 0),
        ("498", "zh:", d498, kb_offset),
    ):
        for u in data:
            qs = []
            for q in u["qs"]:
                item = dict(q)
                item["id"] = id_prefix + q["id"]
                if item.get("kb") is not None:
                    item["kb"] = item["kb"] + kb_shift
                qs.append(item)

            pred = compute_unit_prediction(u["sub"], u["name"], qs)
            units.append({
                "ex": ex,
                "sub": u["sub"],
                "name": u["name"],
                "w": pred["w"],
                "w5": pred["w5"],
                "wh": pred["wh"],
                "bt": pred["bt"],
                "pt": pred["pt"],
                "L": len(qs),
                "qs": qs,
            })

    units.sort(
        key=lambda u: (
            -u["w"],
            -u["w5"],
            -u["L"],
            SUB_ORDER.get(u["sub"], 9),
            u["name"],
        )
    )
    return units, kb_all


def main():
    data, kb = build_combined()

    shell = open(SHELL, encoding="utf-8").read()
    payload = "[\n" + ",\n".join(
        json.dumps(u, ensure_ascii=False, separators=(",", ":")) for u in data
    ) + "\n]"
    payload = payload.replace("</", "<\\/")
    kb_payload = "[\n" + ",\n".join(
        json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in kb
    ) + "\n]"
    kb_payload = kb_payload.replace("</", "<\\/")

    html = shell.replace("/*__QUIZ_DATA__*/", payload).replace("/*__KB_DATA__*/", kb_payload)

    nq = sum(len(u["qs"]) for u in data)
    n398 = sum(len(u["qs"]) for u in data if u["ex"] == "398")
    n498 = sum(len(u["qs"]) for u in data if u["ex"] == "498")
    covered = sorted({q["y"] for u in data for q in u["qs"]})
    note = (
        f"当前合并收录 {nq} 道客观真题（398 基础课 {n398} 题 + 498 综合课 {n498} 题，"
        f"{covered[0]}–{covered[-1]}年，共 {len(data)} 个章节单元）。"
    )
    html = html.replace("__COVERAGE__", note)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(
        f"合并章节 {len(data)} 个，题目 {nq} 道（398:{n398} + 498:{n498}），"
        f"KB {len(kb)} 条 -> {os.path.relpath(OUT, ROOT)} ({len(html)/1024/1024:.2f} MB)"
    )


if __name__ == "__main__":
    main()
