# -*- coding: utf-8 -*-
"""
对比实验：复现"第一个预测.md"的单章节基准模型，与我的迭代4模型在同一数据、
同一 80 题槽位、同一命中标准下硬碰硬，并测试 2022 综合56 错标修正的影响。
"""
import json
import sys
from collections import defaultdict
sys.path.insert(0, 'backtest')
import backtest as bt

# 统一采用 backtest.py 的干净口径：只保留大题（num>=51），排除选择题污染
base = bt.load_subject('data/tagged.json')
zonghe = bt.load_subject('data/zonghe/tagged.json')

YEARS = [2022, 2023, 2024, 2025, 2026]
SLOTS = list(range(51, 59))

# ---------- "单章节基准"模型（原样复现第一个预测.md §3.2 规则） ----------
# 分组：学科×题型；预测 Y 年时只统计 Y-5 至 Y-1 该组 node 出现次数；
# 每组选出现次数最多的 node，并列先最近出现，仍并列按名称字典序；无历史样本不预测。
GROUPS = {
    ('刑法', '简答'), ('民法', '简答'),
    ('刑法', '法条分析'), ('民法', '法条分析'),
    ('刑法', '案例分析'), ('民法', '案例分析'),
    ('法理学', '简答'), ('中国宪法学', '简答'), ('中国法制史', '简答'),
    ('法理学', '分析'), ('中国宪法学', '分析'), ('中国法制史', '分析'),
    ('法理学', '论述'), ('中国宪法学', '论述'), ('中国法制史', '论述'),
}

def node_of(x):
    return x['node']

def group_of(x):
    return (x['subject'], x['type'])

def single_chapter_predict(history, Y, group):
    """单章节基准：Y-5~Y-1 窗口内该组出现次数最多的 node"""
    window = [x for x in history if Y - 5 <= x['year'] <= Y - 1 and group_of(x) == group]
    if not window:
        return None
    counts = defaultdict(list)
    for x in window:
        counts[node_of(x)].append(x['year'])
    # 排序：次数降序 → 最近出现降序 → 名称字典序
    best = sorted(counts.items(), key=lambda kv: (-len(kv[1]), -max(kv[1]), kv[0]))
    return best[0][0]

def run_single_chapter(data_all, fix_2022_56=False):
    """跑单章节基准回测。fix_2022_56 修正 2022 综合56 错标。"""
    # 构造带修正的数据副本
    data = [dict(x) for x in data_all]
    if fix_2022_56:
        for x in data:
            if x['year'] == 2022 and x['num'] == 56 and x['subject'] == '中国法制史':
                x['node'] = '明清法律制度'  # 原文为清史稿秋审，正确标签应为明清
    rows = []
    for Y in YEARS:
        hist = [x for x in data if x['year'] < Y]
        actual = [x for x in data if x['year'] == Y and x['num'] in SLOTS]
        for x in actual:
            g = group_of(x)
            pred = single_chapter_predict(hist, Y, g)
            rows.append(dict(year=Y, slot=x['num'], subject=x['subject'], type=x['type'],
                             actual=x['node'], pred=pred,
                             hit=(pred is not None and pred == x['node'])))
    return rows

# ---------- 我的迭代4模型 ----------
def run_mine(data_all, fix_2022_56=False):
    data = [dict(x) for x in data_all]
    if fix_2022_56:
        for x in data:
            if x['year'] == 2022 and x['num'] == 56 and x['subject'] == '中国法制史':
                x['node'] = '明清法律制度'
    rows = []
    # 分别处理 base（刑法/民法）与 zonghe（法理/宪法/法制史）
    for subj in ('base', 'zonghe'):
        subject_names = {'base': ('刑法', '民法'), 'zonghe': ('法理学', '中国宪法学', '中国法制史')}
        for Y in YEARS:
            hist = [x for x in data if x['year'] < Y and x['subject'] in subject_names[subj]]
            actual = {x['num']: x['node'] for x in data if x['year'] == Y and x['num'] in SLOTS and x['subject'] in subject_names[subj]}
            for slot in SLOTS:
                if slot not in actual:
                    continue
                ranked = bt.my_predict(hist, Y, subj, slot)
                actual_node = actual[slot]
                rows.append(dict(year=Y, slot=slot, actual=actual_node,
                                 top=ranked[0], cover=ranked[:4],
                                 hit=(actual_node == ranked[0]),
                                 cov=(actual_node in ranked[:4])))
    return rows

if __name__ == '__main__':
    # 数据合并（base + zonghe）
    all_data = base + zonghe

    # 1. 单章节基准（原样）
    sc = run_single_chapter(all_data, fix_2022_56=False)
    sc_hit = sum(1 for r in sc if r['hit'])
    print(f'=== 单章节基准模型（原样，未修错标）===')
    print(f'头档命中: {sc_hit}/{len(sc)} = {sc_hit/len(sc):.1%}')
    for Y in YEARS:
        rs = [r for r in sc if r['year']==Y]
        h = sum(1 for r in rs if r['hit'])
        print(f'  {Y}: {h}/{len(rs)}')

    # 2. 单章节基准（修错标）
    sc2 = run_single_chapter(all_data, fix_2022_56=True)
    sc2_hit = sum(1 for r in sc2 if r['hit'])
    print(f'\n=== 单章节基准模型（修正2022综合56错标）===')
    print(f'头档命中: {sc2_hit}/{len(sc2)} = {sc2_hit/len(sc2):.1%}')

    # 3. 我的迭代4模型（原样）
    mine = run_mine(all_data, fix_2022_56=False)
    m_hit = sum(1 for r in mine if r['hit'])
    m_cov = sum(1 for r in mine if r['cov'])
    print(f'\n=== 我的迭代4模型（原样，未修错标）===')
    print(f'头档命中: {m_hit}/{len(mine)} = {m_hit/len(mine):.1%}  覆盖命中: {m_cov}/{len(mine)} = {m_cov/len(mine):.1%}')

    # 4. 我的迭代4模型（修错标）
    mine2 = run_mine(all_data, fix_2022_56=True)
    m2_hit = sum(1 for r in mine2 if r['hit'])
    m2_cov = sum(1 for r in mine2 if r['cov'])
    print(f'\n=== 我的迭代4模型（修正2022综合56错标）===')
    print(f'头档命中: {m2_hit}/{len(mine2)} = {m2_hit/len(mine2):.1%}  覆盖命中: {m2_cov}/{len(mine2)} = {m2_cov/len(mine2):.1%}')

    # 5. 错标修正对我的模型的具体影响
    diff = [(r1['year'], r1['slot'], r1['actual'], r1['top'], r1['hit'], r2['hit'])
            for r1, r2 in zip(mine, mine2) if r1['hit'] != r2['hit']]
    print(f'\n=== 错标修正导致命中变化的题位 ===')
    if diff:
        for d in diff:
            print(f'  {d[0]} #{d[1]} 实际:{d[2]} 我的top:{d[3]} 修前命中:{d[4]} 修后命中:{d[5]}')
    else:
        print('  无变化（错标不影响我的模型头档命中）')
