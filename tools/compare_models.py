#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比《第二次预测》的模型思路与本仓库冻结模型。
同一数据、同一槽位池、同一链式回测(2022→2026)、同一命中口径(板块级)。
输出 Top1/Top3/Top4 命中, 逐年与合计; 并做关键信号消融。
"""
import sys, json, collections
sys.path.insert(0, '/home/user/study/tools')
from backtest_subjective import rows, slot_of, actual_slots, FZ, predict_year, score_year

YEARS = list(range(2022, 2027))
MY_W = json.load(open('/tmp/W.json'))  # 冻结权重 gap1 typ1 hist1 repeat-1

# ---------- 共用: 候选池与打分框架 ----------
def pools(hist):
    xall = sorted({r['node'] for r in hist if r['paper']=='398' and r['subject']=='刑法'})
    xz = [n for n in xall if n not in FZ]
    xf = [n for n in xall if n in FZ]
    m = sorted({r['node'] for r in hist if r['paper']=='398' and r['subject']=='民法'})
    def sub_nodes(paper, subj):
        return sorted({r['node'] for r in hist if r['paper']==paper and r['subject']==subj})
    last_fs = max((r['year'] for r in hist if r['paper']=='498' and r['subject']=='中国法制史' and r['type']=='论述'), default=0)
    return dict(xz=xz, xf=xf, m=m,
                fj=sub_nodes('498','法理学'), xf498=sub_nodes('498','中国宪法学'),
                fs=sub_nodes('498','中国法制史'),
                subj58='中国法制史' if (2027-last_fs)==5 else '中国宪法学')

def rank(pool, keyfn, exclude=(), topk=5):
    cand = [n for n in pool if n not in exclude]
    scored = [(keyfn(n), n) for n in cand]
    scored.sort(key=lambda x: (-x[0], x[1]))   # 稳定排序: 分数降序, 名称升序
    return [n for _, n in scored[:topk]]

def predict_generic(Y, key_for):
    """key_for(slotkey, node, hist, P) -> score. 返回 {slot: top5}"""
    hist = [dict(r, slot=slot_of(r['paper'], r)) for r in rows if r['year'] < Y]
    P = pools(hist)
    out = {}
    k51 = lambda n: key_for('xj1', n, hist, P)
    p51 = rank(P['xz'], k51, topk=5); out['xj1'] = p51
    k52 = lambda n: key_for('xj2', n, hist, P)
    p52 = rank(P['xf'], k52, exclude=p51[:1], topk=5)
    if len(p52) < 5:
        p52 += [n for n in rank(P['xz'], k52, exclude=p51+p52, topk=5) if n not in p52]
    out['xj2'] = p52[:5]
    out['mj1'] = rank(P['m'], lambda n: key_for('mj1', n, hist, P), topk=5)
    rest = [n for n in P['m'] if n not in out['mj1'][:1]]
    out['mj2'] = rank(rest, lambda n: key_for('mj2', n, hist, P), topk=5)
    out['xt']  = rank(P['xz']+P['xf'], lambda n: key_for('xt', n, hist, P), topk=5)
    out['mt']  = rank(P['m'], lambda n: key_for('mt', n, hist, P), topk=5)
    out['xa']  = rank(P['xz']+P['xf'], lambda n: key_for('xa', n, hist, P), topk=5)
    out['ma']  = rank(P['m'], lambda n: key_for('ma', n, hist, P), topk=5)
    for sk, subj, qt in [('fj','法理学','简答'),('fx','法理学','分析'),('fl','法理学','论述'),
                         ('xf','中国宪法学','简答'),('xx','中国宪法学','分析'),
                         ('fs','中国法制史','简答'),('xs','中国法制史','分析')]:
        out[sk] = rank(P['fj' if subj=='法理学' else ('xf498' if subj=='中国宪法学' else 'fs')],
                       lambda n, sk=sk: key_for(sk, n, hist, P), topk=5)
    pool58 = P['fj'] if False else (P['xf498'] if P['subj58']=='中国宪法学' else P['fs'])
    out['xl'] = rank(pool58, lambda n: key_for('xl', n, hist, P), topk=5)
    return out

def evaluate(preds_fn, ks=(1,3,4)):
    res = {k: 0 for k in ks}; tot = 0
    per_year = collections.defaultdict(lambda: {k:0 for k in ks})
    details = []
    for Y in YEARS:
        preds = preds_fn(Y)
        act = actual_slots(Y)
        for sk, actuals in act.items():
            pl = preds.get(sk, [])
            for a in actuals:
                tot += 1
                for k in ks:
                    if a in pl[:k]:
                        res[k] += 1; per_year[Y][k] += 1
                details.append((Y, sk, a, pl, a in pl[:1], a in pl[:3], a in pl[:4]))
    return res, tot, per_year, details

# ---------- 模型 A: 本仓库冻结模型 ----------
def key_mine(sk, n, hist, P):
    from backtest_subjective import feats
    f = feats(n, None, None, None, None, hist) if False else None
    # 复用原 feats 需要 subject/type —— 直接调 predict_year 的内部逻辑: 用原 score_year 的特征
    return _mine_score(sk, n, hist)

# 直接从 backtest_subjective 拿 feats, 但需要 subject/qtype/slotkey
SUBJ_TYPE = {'xj1':('刑法','简答','xj1'),'xj2':('刑法','简答','xj2'),
             'mj1':('民法','简答','mj1'),'mj2':('民法','简答','mj2'),
             'xt':('刑法','法条分析','xt'),'mt':('民法','法条分析','mt'),
             'xa':('刑法','案例分析','xa'),'ma':('民法','案例分析','ma'),
             'fj':('法理学','简答','fj'),'fx':('法理学','分析','fx'),'fl':('法理学','论述','fl'),
             'xf':('中国宪法学','简答','xf'),'xx':('中国宪法学','分析','xx'),
             'fs':('中国法制史','简答','fs'),'xs':('中国法制史','分析','xs'),
             'xl':('中国宪法学','论述','xl')}

def _mine_score(sk, n, hist):
    from backtest_subjective import feats
    subj, qt, skey = SUBJ_TYPE[sk]
    if sk == 'xl':
        # xl 的 subject 取决于年份规则 — feats 里 subject 用于过滤, 用实际池科目
        pass
    Y = max(r['year'] for r in hist) + 1
    f = feats(n, subj, qt, skey, Y, hist)
    return sum(MY_W[k]*f[k] for k in MY_W)

# ---------- 模型 B: 《第二次预测》公式(近似复现) ----------
# score = 2.5*近5年槽位内频率占比 + 0.8*跨型频率占比 + 0.7*轮空(封顶8)/8
#         + 0.8*7-13年周期回归 + 新法信号(分科) + 0.6*上年连考 - 法史朝代切出惩罚
def slot_freq5(sk, n, hist, Y):
    subj, qt, skey = SUBJ_TYPE[sk]
    c = sum(1 for r in hist if r['node']==n and r['subject']==subj and r['type']==qt
            and Y-5 <= r['year'] <= Y-1)
    return c / 5.0

def cross_type_freq(n, subj, hist, Y):
    years = {r['year'] for r in hist if r['node']==n and r['subject']==subj}
    return len(years)

def key_theirs(sk, n, hist, P):
    Y = max(r['year'] for r in hist) + 1
    subj, qt, skey = SUBJ_TYPE[sk]
    if sk == 'xl':
        subj = P['subj58'] if P['subj58']=='中国宪法学' else '中国宪法学'
    same = [r for r in hist if r['node']==n and r['subject']==subj]
    last = max((r['year'] for r in same), default=None)
    gap = (Y-last) if last else 12
    # 1) 近5年槽位内频率占比
    s1 = 2.5 * slot_freq5(sk, n, hist, Y)
    # 2) 跨型频率占比 (同科其他题型出现年份数, 归一到候选最大值)
    ct = cross_type_freq(n, subj, hist, Y)
    s2 = 0.8 * (ct / 10.0)   # 归一: 10年封顶
    # 3) 轮空 封顶8年
    s3 = 0.7 * min(gap, 8) / 8.0
    # 4) 7-13年周期回归
    s4 = 0.8 * (1.0 if 7 <= gap <= 13 else 0.0)
    # 5) 新法信号(分科近似表)
    s5 = newlaw_signal(subj, n, Y)
    # 6) 上年连考惯性 +0.6
    s6 = 0.6 * (1.0 if last == Y-1 else 0.0)
    # 7) 法史朝代连考切出惩罚: 法史节点在 Y-1、Y-2 连续出现 → 惩罚
    s7 = 0.0
    if subj == '中国法制史':
        yrs = {r['year'] for r in same}
        if (Y-1 in yrs) and (Y-2 in yrs):
            s7 = -1.0
    return s1+s2+s3+s4+s5+s6+s7

# 近似新法表 (只用可核验的施行年; 398: T+2~4 弱(0.4), 498: T+1~2 强(0.8))
NEWLAW = [
    # (paper_subj_match, node_sublist, enacted_year, strength_kind)
    ('民法', ['合同通则','典型合同','婚姻家庭','继承','侵权责任','物权通则与物权变动','所有权与共有','担保物权','代理','民事主体','民事法律行为','人格权','无因管理与不当得利','知识产权','用益物权','诉讼时效与期间','民法总则与基本原则'], 2021, '398'),  # 民法典2021施行
    ('刑法', ['分则·贪污贿赂罪','分则·破坏市场经济秩序罪'], 2024, '398'),  # 刑修十二 2024-03
    ('刑法', ['分则·妨害社会管理秩序罪','分则·危害公共安全罪'], 2022, '398'),  # 反电诈法2022/反有组织犯罪法
    ('刑法', ['犯罪主体','正当行为'], 2021, '398'),  # 刑修十一 2021-03
    ('民法', ['合同通则','侵权责任'], 2023, '398'),  # 合同编通则解释2023-12 / 侵权解释一2024-09
    ('法理学', ['立法体制与立法程序'], 2023, '498'),  # 立法法2023
    ('法理学', ['法的实施（执法与司法）','法治理论与法治中国'], 2021, '498'),  # 行政处罚法2021
    ('中国宪法学', ['国家机构（国家主席、国务院与军委）'], 2024, '498'),  # 国务院组织法2024
    ('中国宪法学', ['国家机构（监察委与法检司法机关）'], 2024, '498'),  # 监察法修正2024-12
    ('中国宪法学', ['政权组织形式与选举制度','国家机构（全国人大及其常委会）'], 2025, '498'),  # 代表法2025修改
    ('中国宪法学', ['公民基本权利（平等、政治、自由）','公民基本权利（监督、财产权、社文与义务）'], 2024, '498'),  # AI/离线权热点
    ('法理学', ['法治理论与法治中国','法的实施（执法与司法）'], 2025, '498'),  # 民营经济促进法2025
]
def newlaw_signal(subj, node, Y):
    s = 0.0
    for s_subj, nodes, L, kind in NEWLAW:
        if subj != s_subj or node not in nodes: continue
        if kind == '398':
            if Y - L in (2,3,4): s += 0.4
        else:
            if Y - L in (1,2): s += 0.8
    return s

# ---------- 消融: 冻结模型 + 单项信号 ----------
def key_ablation(sk, n, hist, P, add_cross=False, repeat_sign=+1, add_dynasty=False, add_cycle=False, add_law=False):
    base = _mine_score(sk, n, hist)
    Y = max(r['year'] for r in hist) + 1
    subj, qt, skey = SUBJ_TYPE[sk]
    if sk=='xl': subj = P['subj58']
    if repeat_sign != -1:
        # 把 repeat 从 -1 改为 repeat_sign: 修正 = (sign - (-1)) * 1 * f.repeat
        from backtest_subjective import feats
        f = feats(n, subj, qt, skey, Y, hist)
        base += (repeat_sign - (-1)) * f['repeat']
    if add_cross:
        base += 0.8 * min(cross_type_freq(n, subj, hist, Y), 10)/10.0
    if add_dynasty and subj=='中国法制史':
        yrs = {r['year'] for r in hist if r['node']==n and r['subject']==subj}
        if (Y-1 in yrs) and (Y-2 in yrs): base -= 1.0
    if add_cycle:
        same=[r for r in hist if r['node']==n and r['subject']==subj]
        last=max((r['year'] for r in same), default=None); gap=(Y-last) if last else 12
        base += 0.8*(1.0 if 7<=gap<=13 else 0.0)
    if add_law:
        base += newlaw_signal(subj, n, Y)
    return base

# ---------- 运行 ----------
def show(name, res, tot, per_year):
    line = ' | '.join(f'{Y}:{per_year[Y][1]}/{per_year[Y][3]}/{per_year[Y][4]}' for Y in YEARS)
    print(f'{name:<44} Top1 {res[1]:>2}/{tot} ({res[1]/tot:.1%})  Top3 {res[3]:>2}/{tot} ({res[3]/tot:.1%})  Top4 {res[4]:>2}/{tot} ({res[4]/tot:.1%})   [逐年T1/T3/T4 {line}]')

print('== 同一数据/同一槽位池/链式2022-2026, 板块级命中 ==')
models = {}
# A 冻结模型
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, key_mine))
show('A. 本仓库冻结模型(gap1,typ1,hist1,rep-1)', res, tot, py); models['A']=(res,tot,det)
# B 第二次预测公式(近似复现, 含新法表)
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, key_theirs))
show('B. 第二次预测公式(近似复现, 含新法)', res, tot, py); models['B']=(res,tot,det)
# B' 无新法项(新法表不可完全复现, 看纯统计部分)
def key_theirs_nolaw(sk,n,hist,P):
    return key_theirs(sk,n,hist,P) - newlaw_signal((P['subj58'] if sk=='xl' else SUBJ_TYPE[sk][0]), n, max(r['year'] for r in hist)+1)
res, tot, py, det = evaluate(lambda Y: predict_generic(Y, key_theirs_nolaw))
show("B'. 第二次预测公式(不含新法项)", res, tot, py)

# 消融: 冻结模型 + 他们的信号
for label, kw in [
    ('C. 冻结+连考改+0.6(替代-1)', dict(repeat_sign=+1)),
    ('D. 冻结+跨型频率', dict(add_cross=True)),
    ('E. 冻结+法史朝代切出', dict(add_dynasty=True)),
    ('F. 冻结+7-13周期回归', dict(add_cycle=True)),
    ('G. 冻结+新法分科表', dict(add_law=True)),
    ('H. 冻结+跨型+周期+新法+法史(保留rep=-1)', dict(add_cross=True, add_cycle=True, add_law=True, add_dynasty=True)),
    ('I. H+连考改+0.6', dict(add_cross=True, add_cycle=True, add_law=True, add_dynasty=True, repeat_sign=+1)),
]:
    res, tot, py, det = evaluate(lambda Y, kw=kw: predict_generic(Y, lambda sk,n,hist,P: key_ablation(sk,n,hist,P,**kw)))
    show(label, res, tot, py)

# 纯验证集 2024-2026 视角 (模型A是22+23调参冻结, B及其衍生未调参但开发时看过全期 — 如实标注)
print()
print('== 纯验证年 2024-2026 (仅A有真正的冻结协议; B/衍生开发时用过全期, 标注为in-sample) ==')
def evaluate_holdout(preds_fn, ks=(1,3,4)):
    res={k:0 for k in ks}; tot=0
    for Y in (2024,2025,2026):
        preds=preds_fn(Y); act=actual_slots(Y)
        for sk, actuals in act.items():
            pl=preds.get(sk,[])
            for a in actuals:
                tot+=1
                for k in ks:
                    if a in pl[:k]: res[k]+=1
    return res, tot
for name, fn in [
    ('A 冻结模型', lambda Y: predict_generic(Y, key_mine)),
    ('B 第二次预测(近似)', lambda Y: predict_generic(Y, key_theirs)),
    ('I 最佳混合', lambda Y: predict_generic(Y, lambda sk,n,hist,P: key_ablation(sk,n,hist,P,add_cross=True,add_cycle=True,add_law=True,add_dynasty=True,repeat_sign=+1))),
]:
    r, t = evaluate_holdout(fn)
    print(f'  {name:<20} Top1 {r[1]}/{t} ({r[1]/t:.1%})  Top3 {r[3]}/{t} ({r[3]/t:.1%})  Top4 {r[4]}/{t} ({r[4]/t:.1%})')

# 保存 B 与 I 的2027 预测供对比
print()
print('== 2027 预测对比 (S档Top1) ==')
pB = predict_generic(2027, key_theirs)
pI = predict_generic(2027, lambda sk,n,hist,P: key_ablation(sk,n,hist,P,add_cross=True,add_cycle=True,add_law=True,add_dynasty=True,repeat_sign=+1))
pA = predict_generic(2027, key_mine)
label = {'xj1':'398#51刑简','xj2':'398#52刑简分','mj1':'398#53民简A','mj2':'398#54民简B',
         'xt':'398#55刑条','mt':'398#56民条','xa':'398#57刑案','ma':'398#58民案',
         'fj':'498#51法简','xf':'498#52宪简','fs':'498#53法史简','fx':'498#54法分',
         'xx':'498#55宪分','xs':'498#56法史分','fl':'498#57法论述','xl':'498#58论'}
for sk in ['xj1','xj2','mj1','mj2','xt','mt','xa','ma','fj','xf','fs','fx','xx','xs','fl','xl']:
    print(f'  {label[sk]:<12} A:{pA[sk][0]:<18} B:{pB[sk][0]:<18} I:{pI[sk][0]}')

# ---------- 追加: 大板块级(21方向合并)同口径对比 ----------
# 按《第二次预测》25天方案的21个方向合并节点; 未列出的节点按科目补入相邻方向(文档化)
DIRECTION = {}
def _m(nodes, d):
    for n in nodes: DIRECTION[n] = d
_m(['合同通则','典型合同','担保物权'], '合同')
_m(['法治理论与法治中国','法的实施（执法与司法）','法律解释、推理与论证'], '法理·法治实施解释')
_m(['公民基本权利（平等、政治、自由）','公民基本权利（监督、财产权、社文与义务）',
    '国家机构（全国人大及其常委会）','国家机构（监察委与法检司法机关）','国家机构（国家主席、国务院与军委）'], '宪法·权利机构')
_m(['犯罪主体','犯罪构成与客观方面','犯罪主观方面','共同犯罪','犯罪停止形态','正当行为',
    '罪数','量刑制度','刑罚种类','刑罚执行与消灭','刑法基础与效力'], '刑法总则')
_m(['分则·贪污贿赂罪'], '分则·贪贿')
_m(['汉朝法律制度','中国法制史综合专题'], '法史·汉与综合')
_m(['分则·破坏市场经济秩序罪'], '分则·经济')
_m(['侵权责任'], '侵权')
_m(['知识产权'], '知产')
_m(['民法总则与基本原则','民事法律行为','代理','民事主体','诉讼时效与期间',
    '无因管理与不当得利','人格权'], '民法总则与代理')
_m(['分则·妨害社会管理秩序罪'], '分则·社管')
_m(['分则·渎职罪'], '分则·渎职')
_m(['继承'], '继承')
_m(['物权通则与物权变动','所有权与共有','用益物权'], '物权')
_m(['婚姻家庭'], '婚家')
_m(['清末与民国法律制度'], '法史·清末民国')
_m(['隋唐法律制度'], '法史·隋唐')
_m(['夏商西周法律制度'], '法史·西周')
_m(['宋元法律制度'], '法史·宋元')
_m(['明清法律制度'], '法史·明清')
_m(['三国两晋南北朝法律制度'], '法史·三国')
# 补: 21方向未列但真题存在的节点
_m(['分则·侵犯人身权利罪'], '分则·人身')
_m(['分则·侵犯财产罪'], '分则·财产')
_m(['分则·危害公共安全罪','分则·危害国家安全罪'], '分则·公安国安')
_m(['法律责任与法律制裁','法律关系','法律要素与法律体系','法系与法的演进','法与社会关系',
    '立法体制与立法程序','法的作用与价值','绪论与法的本质特征'], '法理·其他')
_m(['国家性质与政党/基层群众自治','政权组织形式与选举制度','宪法效力、解释与合宪性审查',
    '宪法基本理论与演进'], '宪法·其他')

def evaluate_direction(preds_fn, ks=(1,4)):
    res={k:0 for k in ks}; tot=0
    per_year=collections.defaultdict(lambda:{k:0 for k in ks})
    for Y in YEARS:
        preds=preds_fn(Y); act=actual_slots(Y)
        for sk, actuals in act.items():
            pl=[DIRECTION.get(n, '?'+n) for n in preds.get(sk,[])]
            # 方向去重保持顺序
            seen=set(); pl2=[]
            for d in pl:
                if d not in seen: seen.add(d); pl2.append(d)
            for a in actuals:
                ad = DIRECTION.get(a, '?'+a); tot+=1
                for k in ks:
                    if ad in pl2[:k]:
                        res[k]+=1; per_year[Y][k]+=1
    return res, tot, per_year

print()
print('== 大板块级(方向合并)同口径: 两模型都用同一张合并表 ==')
for name, fn in [('A 冻结模型(节点→方向)', lambda Y: predict_generic(Y, key_mine)),
                 ('B 第二次预测(节点→方向)', lambda Y: predict_generic(Y, key_theirs))]:
    r, t, py = evaluate_direction(fn)
    line=' | '.join(f'{Y}:{py[Y][1]}/{py[Y][4]}' for Y in YEARS)
    p1 = format(r[1]/t, '.1%'); p4 = format(r[4]/t, '.1%')
    print(f'  {name:<28} 方向Top1 {r[1]:>2}/{t} ({p1})  方向Top4 {r[4]:>2}/{t} ({p4})   [逐年T1/T4 {line}]')
print('  (第二次预测自报: 方向Top1 42/80=52.5%, 方向Top4 61/80=76.2% — 其合并表未公开, 此处为其Top5节点经本表合并后的下界估计)')
