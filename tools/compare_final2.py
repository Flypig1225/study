#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比《最终版2》V5.2 公式 与 本仓库冻结模型。
同一数据 / 同一槽位池 / 同一链式回测(2022→2026) / 同一板块级命中口径。
V5.2 公式按其报告第三部分复现; 未公开项按文档内可推断的最合理解释实现并在输出中标注。
"""
import sys, re, json, collections
sys.path.insert(0, '/home/user/study/tools')
from compare_models import (predict_generic, evaluate, evaluate_holdout, evaluate_direction,
                            SUBJ_TYPE, key_mine, DIRECTION)
from backtest_subjective import rows, slot_of, actual_slots

YEARS = list(range(2022, 2027))

# ---------- V5.2 新法事件表 (报告 1.2/第三部分列举的施行年) ----------
# (施行年, 科目, 关联节点列表)
EVENTS = [
    (2021, '民法', ['合同通则', '典型合同', '担保物权', '侵权责任', '婚姻家庭', '继承',
                    '物权通则与物权变动', '所有权与共有', '代理', '民事法律行为', '人格权',
                    '诉讼时效与期间', '用益物权']),                      # 民法典
    (2021, '刑法', ['犯罪主体', '正当行为', '分则·破坏市场经济秩序罪',
                    '分则·妨害社会管理秩序罪']),                        # 刑修十一
    (2021, '法理学', ['法的实施（执法与司法）']),                        # 行政处罚法
    (2022, '刑法', ['分则·妨害社会管理秩序罪', '分则·危害公共安全罪']),  # 反电诈/反有组织犯罪
    (2023, '法理学', ['立法体制与立法程序']),                            # 立法法
    (2023, '民法', ['合同通则']),                                        # 合同编通则解释
    (2024, '民法', ['侵权责任']),                                        # 侵权解释一
    (2024, '刑法', ['分则·贪污贿赂罪', '分则·破坏市场经济秩序罪']),      # 刑十二
    (2024, '中国宪法学', ['国家机构（国家主席、国务院与军委）']),         # 国务院组织法
    (2025, '中国宪法学', ['国家机构（监察委与法检司法机关）']),           # 监察法修正
    (2025, '法理学', ['法的实施（执法与司法）']),                        # 新监督法(法理侧)
    (2025, '中国宪法学', ['国家机构（全国人大及其常委会）']),             # 新监督法/代表法
    (2025, '民法', ['婚姻家庭']),                                        # 婚家解释二
    (2025, '法理学', ['法治理论与法治中国']),                            # 民营经济促进法
    (2025, '刑法', ['分则·破坏市场经济秩序罪']),                         # 民营经济促进法(刑侧)
    (2026, '刑法', ['分则·妨害社会管理秩序罪']),                         # 治安管理处罚法
]
# 报告给出的曲线 (0.5/0.7/1.0/0.8/0.5) 对应 age1..5, 峰值 age3; 综合课时滞1-2年(1.2节)故平移
CURVE_398 = {1: 0.5, 2: 0.7, 3: 1.0, 4: 0.8, 5: 0.5}
CURVE_498 = {1: 0.7, 2: 1.0, 3: 0.8, 4: 0.5, 5: 0.3}

CONTRAST_RE = re.compile(r'区别|界限|异同|比较')

def _gap_bonus(gap):
    if gap >= 15: return 1.5
    if gap >= 7:  return 1.0
    if gap >= 6:  return 0.8
    if gap >= 5:  return 0.5
    if gap >= 4:  return 0.3
    if gap >= 3:  return 0.15
    return 0.0

def key_v52(sk, n, hist, P, cross=True, law=True):
    subj, qt, skey = SUBJ_TYPE[sk]
    if sk == 'xl':
        subj = P['subj58']
    Y = max(r['year'] for r in hist) + 1
    same_subj = [r for r in hist if r['node'] == n and r['subject'] == subj]
    same_type = [r for r in same_subj if r['type'] == qt]
    years_any = [r['year'] for r in same_subj]
    years_type = [r['year'] for r in same_type]
    last_any = max(years_any) if years_any else None
    last_type = max(years_type) if years_type else None
    gap_any = (Y - last_any) if last_any else 99
    gap_type = (Y - last_type) if last_type else 99

    # 1) 题族感知频次: 近6年本题型出现次数, 0.9×封顶1.35
    c6 = sum(1 for y in years_type if Y - 6 <= y <= Y - 1)
    s = 0.03 + min(0.9 * c6, 1.35)

    # 2) 轮空加成: 双口径取较大档
    s += _gap_bonus(max(gap_any, gap_type))

    # 3) 母机制
    c8 = sum(1 for y in years_type if Y - 8 <= y <= Y - 1)
    if c8 >= 3:
        s += 0.35
    elif 3 <= gap_type <= 5:
        s += 0.21

    # 4) ×近考惩罚 (案例族上年 ×0.6, 其余上年 ×0.25; 前年 ×0.75)
    pen = 1.0
    if last_any == Y - 1:
        pen *= 0.6 if sk in ('xa', 'ma') else 0.25
    elif last_any == Y - 2:
        pen *= 0.75
    # 5) ×法条槽 (仅 xt/mt): 条文已考降权
    if sk in ('xt', 'mt'):
        ft_years = {r['year'] for r in hist
                    if r['node'] == n and r['subject'] == subj and r['type'] == '法条分析'}
        if (Y - 1 in ft_years) and (Y - 2 in ft_years):
            pen *= 0.5
        elif Y - 1 in ft_years:
            pen *= 0.8
        elif ft_years:
            pen *= 0.85
    s *= pen

    # 6) 民法换点连考 +0.2 / 刑法连考 −0.35 (按1.2: 民法连考优先, 刑法轮空优先)
    if last_any == Y - 1:
        if subj == '民法':
            s += 0.2
        elif subj == '刑法':
            s -= 0.35

    # 7) 对比型倾向 +0.4 (该节点历史题干含"区别/界限/异同/比较")
    if any(CONTRAST_RE.search(r.get('stem') or '') for r in same_subj):
        s += 0.4

    # 8) 新法事件 w=0.9 × age曲线; 简答族 ×0.3
    if law:
        curve = CURVE_398 if subj in ('刑法', '民法') else CURVE_498
        for L, esubj, enodes in EVENTS:
            if esubj == subj and n in enodes:
                v = curve.get(Y - L, 0.0)
                if v:
                    s += 0.9 * v * (0.3 if qt == '简答' else 1.0)

    # 9) 法条槽: 22年从未进过法条分析 +0.4
    if sk in ('xt', 'mt') and not any(r['type'] == '法条分析' for r in same_subj):
        s += 0.4

    # 10) 史简答破零: 法史节点从未考过简答但史料(分析)常客 +0.9 (仅 fs)
    if sk == 'fs':
        if not any(r['type'] == '简答' for r in same_subj) and \
           any(r['type'] == '分析' for r in same_subj):
            s += 0.9

    # 11) 史料分析: 隋唐母朝 +0.3; 其他朝代 d1×0.45 / d2×0.7 (仅 xs, 乘法在最后)
    xs_dyn = 1.0
    if sk == 'xs':
        if n == '隋唐法律制度':
            s += 0.3
        elif last_any == Y - 1:
            xs_dyn = 0.45
        elif last_any == Y - 2:
            xs_dyn = 0.7

    # 12) #57 法治理论母题 3 年周期回归 +1.0
    if sk == 'fl' and n == '法治理论与法治中国' and gap_any == 3:
        s += 1.0

    # (报告的 #58 宪法池+0.5/史池−0.35: 池按同一5年规则预选, 池内为常数, 对排序无影响 — 不实现)

    # 13) 跨型频率: 同科其他题型出现年份占比 ×0.3 (吸收自《第二次预测》)
    if cross:
        subj_years = {r['year'] for r in hist if r['subject'] == subj}
        other_years = {r['year'] for r in same_subj if r['type'] != qt}
        if subj_years:
            s += 0.3 * len(other_years) / len(subj_years)

    s *= xs_dyn

    # 14) 案例槽人财/婚家板块 ×1.3
    if sk == 'xa' and n in ('分则·侵犯人身权利罪', '分则·侵犯财产罪'):
        s *= 1.3
    if sk == 'ma' and n in ('婚姻家庭',):
        s *= 1.3
    return s

# ---------- 运行 ----------
def show(name, res, tot, per_year):
    line = ' | '.join(f'{Y}:{per_year[Y][1]}/{per_year[Y][3]}/{per_year[Y][4]}' for Y in YEARS)
    print(f'{name:<46} Top1 {res[1]:>2}/{tot} ({res[1]/tot:.1%})  Top3 {res[3]:>2}/{tot} ({res[3]/tot:.1%})  Top4 {res[4]:>2}/{tot} ({res[4]/tot:.1%})   [逐年T1/T3/T4 {line}]')

print('== 同一数据/同一槽位池/链式2022-2026, 板块级命中 ==')
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, key_mine))
show('A. 本仓库冻结模型', res, tot, py)
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, key_v52))
show('V5.2 最终版2公式(完整复现)', res, tot, py)
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, lambda sk,n,hist,P: key_v52(sk,n,hist,P,cross=False)))
show("V5.2' 去掉跨型频率(检验其'+1'声明)", res, tot, py)
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, lambda sk,n,hist,P: key_v52(sk,n,hist,P,law=False)))
show("V5.2'' 去掉新法事件(敏感性)", res, tot, py)

print()
print('== 他们的自报数字 (L2=板块级, 同名口径) ==')
print('  V5.2 自报:   Top1 13/80 (16.2%)  Top3 24/80 (30.0%)  Top4 30/80 (37.5%)')
print('  第二次预测自报: Top1 9/80 (11.2%)  Top3 —        Top4 28/80 (35.0%)')
print('  注: 其L1(考点级, 更细)自报 Top1 9/80、Top3 23/80 — 我方标签为板块级, L1不可复现')

print()
print('== 纯验证年 2024-2026 ==')
for name, fn in [
    ('A 冻结模型', lambda Y: predict_generic(Y, key_mine)),
    ('V5.2 完整', lambda Y: predict_generic(Y, key_v52)),
    ("V5.2' 无跨型", lambda Y: predict_generic(Y, lambda sk,n,hist,P: key_v52(sk,n,hist,P,cross=False))),
]:
    r, t = evaluate_holdout(fn)
    print(f'  {name:<16} Top1 {r[1]}/{t} ({r[1]/t:.1%})  Top3 {r[3]}/{t} ({r[3]/t:.1%})  Top4 {r[4]}/{t} ({r[4]/t:.1%})')

print()
print('== 大板块级(方向合并) ==')
for name, fn in [('A 冻结模型', lambda Y: predict_generic(Y, key_mine)),
                 ('V5.2 完整', lambda Y: predict_generic(Y, key_v52))]:
    r, t, py = evaluate_direction(fn)
    p1 = format(r[1]/t, '.1%'); p4 = format(r[4]/t, '.1%')
    print(f'  {name:<16} 方向Top1 {r[1]:>2}/{t} ({p1})  方向Top4 {r[4]:>2}/{t} ({p4})')

print()
print('== 2027 预测对比 (Top1) ==')
pA = predict_generic(2027, key_mine)
pV = predict_generic(2027, key_v52)
label = {'xj1':'398#51刑简','xj2':'398#52刑简分','mj1':'398#53民简A','mj2':'398#54民简B',
         'xt':'398#55刑条','mt':'398#56民条','xa':'398#57刑案','ma':'398#58民案',
         'fj':'498#51法简','xf':'498#52宪简','fs':'498#53法史简','fx':'498#54法分',
         'xx':'498#55宪分','xs':'498#56法史分','fl':'498#57法论述','xl':'498#58论'}
for sk in ['xj1','xj2','mj1','mj2','xt','mt','xa','ma','fj','xf','fs','fx','xx','xs','fl','xl']:
    print(f'  {label[sk]:<12} A:{pA[sk][0]:<20} V5.2:{pV[sk][0]}')

# 与《最终版2》第四部分 S档人工对照 (其S档Top1, 逐槽)
print()
print('== 与《最终版2》第四部分 S档(人工)对照 ==')
THEIR_S = {
    'xj1': '正当行为(防卫避险对比)', 'xj2': '分则·贪污贿赂罪(行贿)',
    'mj1': '诉讼时效与期间', 'mj2': '人格权',
    'xt': '分则·妨害社会管理秩序罪(帮信掩隐)', 'mt': '民法总则与基本原则(1188监护)',
    'xa': '分则·侵犯财产罪', 'ma': '婚姻家庭',
    'fj': '法律责任与法律制裁', 'xf': '公民基本权利(基本义务)',
    'fs': '明清法律制度', 'fx': '法的实施(法律监督)',
    'xx': '国家机构(国务院)', 'xs': '宋元法律制度',
    'fl': '法治理论与法治中国', 'xl': '国家机构(监察委)',
}
agree_t1 = agree_t3 = 0
for sk in ['xj1','xj2','mj1','mj2','xt','mt','xa','ma','fj','xf','fs','fx','xx','xs','fl','xl']:
    a3 = pA[sk][:3]
    t1 = THEIR_S[sk]
    hit1 = t1 == pA[sk][0]
    hit3 = any(t1.split('(')[0] in x or x.split('(')[0] in t1 for x in a3)
    agree_t1 += hit1; agree_t3 += hit3
    mark = 'T1✓' if hit1 else ('T3✓' if hit3 else '×')
    print(f'  {label[sk]:<12} 其S1:{t1:<24} A_top3:{" > ".join(a3):<52} {mark}')
print(f'  汇总: 其S1与A的Top1重合 {agree_t1}/16, 与A的Top3重合 {agree_t3}/16')
