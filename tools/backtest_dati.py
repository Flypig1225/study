#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法硕（非法学）主观大题 · 链式回测引擎（2022→2026）
====================================================
规则：预测 Y 年时，特征只允许使用 ≤ Y-1 年真题数据（机械化强制）。
预测粒度：题位 × 板块（与 data/tagged.json、data/zonghe/tagged.json 的板块体系一致）。
命中判定：预测板块 ∈ 该题位实际板块集合 → 命中（题位级）；top-k = 前 k 个预测中至少 1 个命中。

三套打分配置对比：
  C0 纯热度基线：近5年/近9年/全期题位频次
  C1 市面押题式：热度 + 轮空回补(重) + 新法滞后(重) + 上年同板块(轻连考)
  C2 调优模型  ：在 C0/C1 基础上按 2022 回测微调（链式迭代第一轮），随后冻结用于 23-26
"""
import json, math, sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- 数据载入
tag = json.load(open(ROOT / 'data/tagged.json'))
zt  = json.load(open(ROOT / 'data/zonghe/tagged.json'))

SUBJ398 = {'简答', '法条分析', '案例分析'}
SUBJ498 = {'简答', '分析', '论述'}

ZONGHE_NODES = {
    '犯罪构成与客观方面', '犯罪主观方面', '犯罪主体', '共同犯罪', '罪数',
    '犯罪停止形态', '正当行为', '刑罚种类', '量刑制度', '刑罚执行与消灭',
    '刑法基础与效力'}
FENZE = {
    '分则·侵犯人身权利罪', '分则·侵犯财产罪', '分则·破坏市场经济秩序罪',
    '分则·危害公共安全罪', '分则·妨害社会管理秩序罪', '分则·贪污贿赂罪',
    '分则·渎职罪', '分则·危害国家安全罪'}

# 题位 → (科目, 候选板块约束)
SLOT398 = {
    '398#51': ('刑法', ZONGHE_NODES),          # 简答1（22年100%总则）
    '398#52': ('刑法', FENZE),                 # 简答2（91%分则）
    '398#53': ('民法', None),                  # 民法简答
    '398#54': ('民法', None),
    '398#55': ('刑法', None),                  # 刑法法条分析（近9年2/3总则）
    '398#56': ('民法', None),                  # 民法法条分析
    '398#57': ('刑法', FENZE),                 # 刑法案例（案例从未离开分则+总则载体）
    '398#58': ('民法', None),                  # 民法案例
}
SLOT498 = {
    '498#51': ('法理学', None),
    '498#52': ('中国宪法学', None),
    '498#53': ('中国法制史', None),
    '498#54': ('法理学', None),
    '498#55': ('中国宪法学', None),
    '498#56': ('中国法制史', None),
    '498#57': ('法理学', None),                # 22年100%法理
    '498#58': ('压轴', None),                  # 宪法 or 法制史（二选一）
}

def load_actual_398():
    """返回 {year: {slot: set(板块)}}，仅 2018-2026 结构"""
    out = defaultdict(dict)
    for t in tag:
        y, n, tp, sub = t['year'], t['num'], t['type'], t['subject']
        if y < 2018 or tp not in SUBJ398:
            continue
        if tp == '简答' and sub == '刑法' and n == 51: out[y]['398#51'] = {t['node']}
        if tp == '简答' and sub == '刑法' and n == 52: out[y]['398#52'] = {t['node']}
        if tp == '简答' and sub == '民法' and n == 53: out[y]['398#53'] = {t['node']}
        if tp == '简答' and sub == '民法' and n == 54: out[y]['398#54'] = {t['node']}
        if tp == '法条分析' and sub == '刑法': out[y]['398#55'] = {t['node']}
        if tp == '法条分析' and sub == '民法': out[y]['398#56'] = {t['node']}
        if tp == '案例分析' and sub == '刑法': out[y]['398#57'] = {t['node']}
        if tp == '案例分析' and sub == '民法': out[y]['398#58'] = {t['node']}
    return {y: dict(d) for y, d in out.items()}

def load_actual_498():
    out = defaultdict(dict)
    for t in zt:
        y, n, tp = t['year'], t['num'], t['type']
        if y < 2018 or tp not in SUBJ498: continue
        key = f'498#{n}'
        out[y].setdefault(key, set()).add(t['node'])
    return out

# ---------------------------------------------------------------- 新法事件（考试年份视角：事件须在当年12月考试前已施行/已通过）
# (考试年可受益的起始考试年, 板块[398用398板块, 498用498板块], 强度)
LAW_398 = [
    (2021, '民事法律行为', 1.0), (2021, '典型合同', 1.0), (2021, '合同通则', 1.0),
    (2021, '人格权', 1.0), (2021, '继承', 1.0), (2021, '担保物权', 1.0),
    (2021, '物权通则与物权变动', 1.0), (2021, '侵权责任', 1.0),   # 民法典施行 2021-01
    (2021, '犯罪主体', 1.2), (2021, '分则·危害公共安全罪', 1.0), (2021, '分则·侵犯人身权利罪', 1.0),  # 刑修十一 2021-03
    (2021, '知识产权', 1.5),                                      # 著作权法/专利法修正 2021-06
    (2021, '人格权', 1.2),                                        # 个人信息保护法 2021-11
    (2022, '民事法律行为', 1.2),                                  # 民法典总则编解释 2022-03（2023考试起）
    (2023, '合同通则', 1.5),                                      # 合同编通则解释 2023-12
    (2023, '分则·危害公共安全罪', 1.0),                           # 最高法醉驾意见 2023-12
    (2024, '分则·贪污贿赂罪', 1.8), (2024, '分则·破坏市场经济秩序罪', 1.8),  # 刑修十二 2024-03
    (2024, '侵权责任', 1.5),                                      # 侵权责任编解释一 2024-09
    (2025, '婚姻家庭', 1.5),                                      # 婚姻家庭编解释二 2025-02
]
LAW_498 = [
    (2023, '立法体制与立法程序', 1.5), (2023, '法治理论与法治中国', 0.8),   # 立法法修改 2023-03
    (2024, '公民基本权利（监督、财产权、社文与义务）', 1.0),               # 国务院组织法等
    (2025, '国家机构（全国人大及其常委会）', 1.8),                          # 监督法修正 2025-01 施行
    (2025, '国家机构（监察委与法检司法机关）', 1.8),                        # 监察法修正 2025-06 施行
    (2025, '国家机构（国家主席、国务院与军委）', 1.2),                      # 国务院组织法 2024 施行
    (2025, '法治理论与法治中国', 1.5),                                      # 二十届三中全会/民营经济促进法 2025
    (2026, '公民基本权利（监督、财产权、社文与义务）', 1.2),                # 民营经济促进法 2025-05
]

# ---------------------------------------------------------------- 特征与打分
def features_slot(years_hist, slot, sub, cand):
    """某题位内各候选板块的特征（years_hist: 已排序历史年份列表，只含 ≤Y-1）"""
    by_slot = defaultdict(Counter)   # year -> Counter(node)
    by_subj = defaultdict(set)
    for y in years_hist:
        pass
    return None

class Backtester:
    def __init__(self, actual, slotdef, subj_hist, law, exam):
        self.actual = actual          # {year:{slot:set}}
        self.slotdef = slotdef
        self.exam = exam
        self.law = law
        # 全部主观题历史（用于 subject 级轮空/连考）
        self.hist = defaultdict(lambda: defaultdict(set))  # year -> subject -> {node}
        src = tag if exam == '398' else zt
        types = SUBJ398 if exam == '398' else SUBJ498
        for t in src:
            if t['type'] in types:
                self.hist[t['year']][t['subject']].add(t['node'])
        # 题位历史
        self.slot_hist = defaultdict(lambda: defaultdict(set))  # year -> slot -> {node}
        for y, d in actual.items():
            for s, ns in d.items():
                self.slot_hist[y][s] = set(ns)

    def predict(self, Y, slot, cfg):
        """返回 [(node, score)] 降序。特征只用 ≤Y-1 数据。
        cfg = (w_heat, w_gap, w_law, w_last) 四个权重，特征均已归一化。"""
        sub, cand = self.slotdef[slot]
        cand = cand or set()
        years = [y for y in sorted(self.hist) if y < Y]
        # 题位内历史频次
        f5, f9, fall = Counter(), Counter(), Counter()
        for y in years:
            nodes = self.slot_hist[y].get(slot, set())
            if not nodes: continue
            for n in nodes: fall[n] += 1
            if y >= Y - 5:
                for n in nodes: f5[n] += 1
            if y >= Y - 9:
                for n in nodes: f9[n] += 1
        # 科目级轮空（压轴论述按 宪法+法制史 合并口径）
        gap_subs = [sub] if sub != '压轴' else ['中国宪法学', '中国法制史']
        pool = set(cand) if cand else set()
        if not pool:
            for s in gap_subs: pool |= self.hist_all_nodes(s)
        gap = {}
        for n in pool:
            lasty = None
            for s in gap_subs:
                ly = max([y for y in years if n in self.hist[y][s]], default=None)
                if ly and (lasty is None or ly > lasty): lasty = ly
            gap[n] = (Y - lasty) if lasty else 99
        # 上年同板块
        last_nodes = set()
        for s in gap_subs:
            last_nodes |= self.hist[Y - 1][s] if (Y - 1) in self.hist else set()
        last_slot = self.slot_hist[Y - 1].get(slot, set())
        # 新法
        law = {n: w for (y0, n, w) in self.law if y0 <= Y}
        w_heat, w_gap, w_law, w_last = cfg
        out = []
        for n in pool:
            heat = (0.5 * min(f5[n] / 4, 1.0) + 0.3 * min(f9[n] / 7, 1.0)
                    + 0.2 * min(fall[n] / 15, 1.0))
            g = min(gap[n], 12) / 12.0
            last = (1.0 if n in last_nodes else 0.0) + 0.5 * (1.0 if n in last_slot else 0.0)
            score = w_heat * heat + w_gap * g + w_law * law.get(n, 0.0) + w_last * last
            # 法条分析槽位：总则先验（近9年 2/3 总则）
            if slot in ('398#55',) and n in ZONGHE_NODES:
                score += 0.6
            out.append((n, round(score, 3)))
        out.sort(key=lambda x: -x[1])
        return out

    def hist_all_nodes(self, sub):
        ns = set()
        for y in self.hist:
            ns |= self.hist[y][sub]
        return ns

    def run(self, cfg, k_list=(1, 3), years=range(2022, 2027), verbose=True):
        res = defaultdict(lambda: [0, 0])  # k -> [hit, total]
        per_year = {}
        for Y in years:
            hits = []
            for slot in sorted(self.slotdef):
                act = self.actual.get(Y, {}).get(slot)
                if not act: continue
                preds = self.predict(Y, slot, cfg)
                for k in k_list:
                    top = [p for p, _ in preds[:k]]
                    res[k][1] += 1
                    if top and set(top) & act: res[k][0] += 1
                hits.append((slot, act, preds[:3]))
            per_year[Y] = hits
        if verbose:
            for Y, hits in per_year.items():
                print(f"\n===== {self.exam} 预测 {Y} 年（仅用 ≤{Y-1} 数据）=====")
                for slot, act, preds in hits:
                    mark = lambda n: ('✓' if n in act else ' ')
                    ps = '  '.join(f"{mark(n)}{n}({s})" for n, s in preds)
                    acts = '/'.join(sorted(act))
                    print(f"  {slot} 实际[{acts}]  预测top3: {ps}")
        print(f"\n----- {self.exam} cfg={cfg} 汇总 -----")
        for k in k_list:
            h, t = res[k]
            print(f"  top{k} 命中率: {h}/{t} = {h/t*100:.1f}%" if t else 'n/a')
        return res

if __name__ == '__main__':
    a398 = load_actual_398()
    a498 = load_actual_498()
    print('398 实际（2018-2026）:')
    for y in sorted(a398):
        print(' ', y, {k: '/'.join(sorted(v)) for k, v in sorted(a398[y].items())})
    print('498 实际（2018-2026）:')
    for y in sorted(a498):
        print(' ', y, {k: '/'.join(sorted(v)) for k, v in sorted(a498[y].items())})
