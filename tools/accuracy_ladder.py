#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""准确率阶梯分析：fine(板块级) vs family(家族级) 粒度 × 新法事件表 v2 × top-k 覆盖曲线"""
import sys
sys.path.insert(0, 'tools')
from backtest_dati import *
from collections import defaultdict, Counter

# ---------- 家族映射（把近义板块并族，模拟"押题方向"的真实颗粒度） ----------
FAM_MIN = {
    '典型合同': '合同', '合同通则': '合同',
    '物权通则与物权变动': '物权', '所有权与共有': '物权', '担保物权': '物权', '用益物权': '物权',
    '民事主体': '主体', '民法总则与基本原则': '主体', '民事法律行为': '主体',
    '诉讼时效与期间': '主体', '代理': '主体',
    '侵权责任': '侵权', '婚姻家庭': '婚姻', '继承': '继承', '人格权': '人格',
    '知识产权': '知产', '无因管理与不当得利': '债',
}
FAM_X = {
    '分则·侵犯人身权利罪': '人财', '分则·侵犯财产罪': '人财',
    '分则·破坏市场经济秩序罪': '经贪', '分则·贪污贿赂罪': '经贪',
    '分则·妨害社会管理秩序罪': '妨管', '分则·危害公共安全罪': '公危',
    '分则·渎职罪': '渎', '分则·危害国家安全罪': '危安',
}
def fam(n, exam):
    if exam == '398':
        return FAM_MIN.get(n) or FAM_X.get(n) or n
    return n

# ---------- 新法事件表 v2（修正 y0 = 首个可受益的考试年；补齐 2025/2026 核实过的新法） ----------
LAW398_2 = [
    (2021, '知识产权', 1.2),
    (2021, '犯罪主体', 1.0), (2021, '分则·危害公共安全罪', 0.8), (2021, '分则·侵犯人身权利罪', 0.6),
    (2022, '人格权', 1.2),                      # 个人信息保护法 2021-11 施行
    (2023, '民事法律行为', 1.0),                # 总则编解释 2022-03（2022-12 考起可用）
    (2024, '合同通则', 1.3),                    # 合同编通则解释 2023-12-05（2023-12 考起）
    (2024, '分则·危害公共安全罪', 0.8),         # 醉驾意见 2023-12
    (2025, '分则·贪污贿赂罪', 1.5), (2025, '分则·破坏市场经济秩序罪', 1.5),   # 刑修十二 2024-03-01 施行→2024-12 考起
    (2025, '侵权责任', 1.3),                    # 侵权解释一 2024-09 → 2024-12 考起
    (2026, '婚姻家庭', 1.5),                    # 婚家解释二 2025-02 → 2025-12 考起
    (2026, '分则·妨害社会管理秩序罪', 0.8),     # 掩隐罪新解释 2025-08-26
    (2026, '正当行为', 1.0),                    # 新治安管理处罚法 2026-01-01（2025-12 考试分析已收）
    (2027, '分则·贪污贿赂罪', 1.2),             # 贪贿解释二 2026-05-01（仅作用于 2027 预测）
    (2027, '侵权责任', 1.0),                    # 道交解释二 2026-06-30
]
LAW498_2 = [
    (2023, '立法体制与立法程序', 1.5), (2023, '法治理论与法治中国', 0.6),   # 立法法 2023-03
    (2025, '国家机构（全国人大及其常委会）', 1.5),   # 监督法修正 2024-11 通过
    (2025, '国家机构（国家主席、国务院与军委）', 1.3),  # 国务院组织法 2024-03 通过
    (2026, '国家机构（监察委与法检司法机关）', 1.3),    # 监察法修正 2024-12 通过、2025-06 施行
    (2026, '政权组织形式与选举制度', 1.2),              # 代表法 2025-03
    (2026, '国家性质与政党/基层群众自治', 1.2),         # 村委会组织法 2025-10 通过、2026-01-01 施行
    (2026, '法治理论与法治中国', 1.2),                  # 法治宣传教育法 2025-11-01 施行
    (2026, '公民基本权利（监督、财产权、社文与义务）', 0.8),  # 民营经济促进法 2025-05
    (2027, '法治理论与法治中国', 1.5),                  # 生态环境法典 2026-08-15 施行＋普法法深化
    (2027, '宪法效力、解释与合宪性审查', 1.0),          # 法典化/备案审查语境
]

a398 = load_actual_398(); a498 = load_actual_498()
bt398 = Backtester(a398, SLOT398, None, LAW_398, '398')
bt498 = Backtester(a498, SLOT498, None, LAW_498, '498')
bt398v2 = Backtester(a398, SLOT398, None, LAW398_2, '398')
bt498v2 = Backtester(a498, SLOT498, None, LAW498_2, '498')

def run_cov(bt, mode, cfg, years, fammode=False):
    """mode1=原版 predict；mode2=predict2(题位反重复)。返回 {k:[hit,total]}"""
    res = {k: [0, 0] for k in range(1, 7)}
    def predict2(bt, Y, slot, cfg):
        preds = bt.predict(Y, slot, cfg)
        last_slot = bt.slot_hist[Y-1].get(slot, set())
        sub = bt.slotdef[slot][0]
        subs = [sub] if sub != '压轴' else ['中国宪法学', '中国法制史']
        last_subj = set()
        for s in subs: last_subj |= bt.hist[Y-1][s]
        out = [(n, s0 - 1.2*(1.0 if n in last_slot else 0.0) + 0.4*(1.0 if n in last_subj else 0.0)) for n, s0 in preds]
        out.sort(key=lambda x: -x[1]); return out
    for Y in years:
        for slot in sorted(bt.slotdef):
            act = bt.actual.get(Y, {}).get(slot)
            if not act: continue
            preds = bt.predict(Y, slot, cfg) if mode == 1 else predict2(bt, Y, slot, cfg)
            if fammode:
                A = {fam(n, bt.exam) for n in act}
                P = [fam(n, bt.exam) for n, _ in preds]
            else:
                A = act; P = [n for n, _ in preds]
            uniq = list(dict.fromkeys(P))  # 保持分数序的去重 top-k（嵌套，单调）
            for k in range(1, 7):
                res[k][1] += 1
                if set(uniq[:k]) & A: res[k][0] += 1
    return res

def rand_cov(bt, fammode=False, n_sim=2000):
    import random
    random.seed(7)
    res = {k: [0, 0] for k in range(1, 7)}
    for Y in range(2022, 2027):
        for slot in sorted(bt.slotdef):
            act = bt.actual.get(Y, {}).get(slot)
            if not act: continue
            pool = [n for n, _ in bt.predict(Y, slot, (0, 0, 0, 0))]
            if fammode:
                pool = list(dict.fromkeys(fam(n, bt.exam) for n in pool))
                A = {fam(n, bt.exam) for n in act}
            else:
                A = act
            for _ in range(n_sim // 40):
                s = random.sample(pool, min(6, len(pool)))
                for k in range(1, 7):
                    res[k][1] += 1
                    if set(s[:k]) & A: res[k][0] += 1
    return res

YEARS = list(range(2022, 2027))
C2A = (2.0, 0.3, 0.0, 0.0); C2B = (1.5, 0.0, 0.0, 0.0)
print("=" * 76)
for bt, bt2, name, cfg in [(bt398, bt398v2, '398', C2A), (bt498, bt498v2, '498', C2B)]:
    rb_f = rand_cov(bt); rb_fa = rand_cov(bt, fammode=True)
    base_f = run_cov(bt, 2, cfg, YEARS); base_fa = run_cov(bt, 2, cfg, YEARS, fammode=True)
    v2_f = run_cov(bt2, 2, cfg, YEARS); v2_fa = run_cov(bt2, 2, cfg, YEARS, fammode=True)
    v2l_f = run_cov(bt2, 2, (cfg[0], cfg[1], 0.4, cfg[3]), YEARS)
    v2l_fa = run_cov(bt2, 2, (cfg[0], cfg[1], 0.4, cfg[3]), YEARS, fammode=True)
    print(f"### {name}  （随机基线 fine / family）")
    print("k      ", "  ".join(f"top{k}" for k in range(1, 7)))
    print("随机   ", "  ".join(f"{rb_f[k][0]/rb_f[k][1]*100:5.1f}%" for k in range(1, 7)),
          "|", "  ".join(f"{rb_fa[k][0]/rb_fa[k][1]*100:5.1f}%" for k in range(1, 7)))
    print("v1模型 ", "  ".join(f"{base_f[k][0]/base_f[k][1]*100:5.1f}%" for k in range(1, 7)),
          "|", "  ".join(f"{base_fa[k][0]/base_fa[k][1]*100:5.1f}%" for k in range(1, 7)))
    print("v2模型 ", "  ".join(f"{v2_f[k][0]/v2_f[k][1]*100:5.1f}%" for k in range(1, 7)),
          "|", "  ".join(f"{v2_fa[k][0]/v2_fa[k][1]*100:5.1f}%" for k in range(1, 7)))
    print("v2+新法", "  ".join(f"{v2l_f[k][0]/v2l_f[k][1]*100:5.1f}%" for k in range(1, 7)),
          "|", "  ".join(f"{v2l_fa[k][0]/v2l_fa[k][1]*100:5.1f}%" for k in range(1, 7)))
    print()

# 每题位家族候选数（设计兜底清单用）
print("=== 每题位家族级候选规模（2018-2026 出现过的家族数 / 全期有效候选） ===")
for bt, name in [(bt398v2, '398'), (bt498v2, '498')]:
    for slot in sorted(bt.slotdef):
        fams = set()
        for y in range(2018, 2027):
            for n in bt.slot_hist[y].get(slot, set()):
                fams.add(fam(n, bt.exam))
        print(f"  {name} {slot}: 近9年出现家族 {len(fams)} 个: {sorted(fams)}")
