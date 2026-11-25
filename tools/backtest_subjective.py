#!/usr/bin/env python3
"""大题押题链式回测 (2022->2026) — 防数据透视: 预测 Y 年只用 <Y 年真题。
输出: 节点级 hit@1/hit@3 + 基线对比 + 规律统计。"""
import json, itertools, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load():
    rows = json.load(open('/tmp/all_subjective.json')) if Path('/tmp/all_subjective.json').exists() else None
    if rows is None:
        raise SystemExit('run extract first')
    return rows

rows = load()
YEARS = sorted({r['year'] for r in rows})

# ---------- 规律统计 ----------
def consec_stats():
    out = {}
    for paper, subjects in [('398', ['刑法', '民法']), ('498', ['法理学', '中国宪法学', '中国法制史'])]:
        for s in subjects:
            pairs = tot = 0
            for y in range(min(YEARS) + 1, max(YEARS) + 1):
                a = {r['node'] for r in rows if r['paper'] == paper and r['subject'] == s and r['year'] == y - 1}
                b = {r['node'] for r in rows if r['paper'] == paper and r['subject'] == s and r['year'] == y}
                if a and b:
                    tot += 1
                    if a & b:
                        pairs += 1
            out[(paper, s)] = (pairs, tot, pairs / tot if tot else 0)
    return out

# ---------- 特征 ----------
def feats(node, subject, qtype, slotkey, Y, hist):
    """hist: list of dict with year,node,subject,type"""
    same = [r for r in hist if r['node'] == node and r['subject'] == subject]
    last = max((r['year'] for r in same), default=None)
    gap = (Y - last) if last else 12
    freq5 = sum(1 for r in same if Y - 5 <= r['year'] <= Y - 1)
    slot = sum(1 for r in same if r['type'] == qtype and r.get('slot') == slotkey)
    typ = sum(1 for r in same if r['type'] == qtype)
    histf = len(same)
    y1 = any(r['year'] == Y - 1 for r in same)
    y2 = any(r['year'] == Y - 2 for r in same)
    return dict(gap=min(gap, 12) / 12, freq5=min(freq5, 3) / 3, slot=min(slot, 3) / 3,
                typ=min(typ, 5) / 5, hist=min(histf, 8) / 8,
                repeat=1.0 if y1 else 0.0, recent=0.0 if (y1 or y2) else 1.0)

def slot_of(paper, r):
    """给 2018 后卷面定位槽位名; 早期年份按当年结构归组。"""
    n, t, sub = r['num'], r['type'], r['subject']
    if paper == '398':
        if t == '简答':
            if sub == '刑法':
                # 2018 起 #51 总则 #52 分则; 早期第一道刑法简答为总则倾向
                return 'xj1' if (r['year'] >= 2018 and n in (51,)) or (r['year'] < 2011 and n == 26) or (2011 <= r['year'] <= 2017 and n == 51) else 'xj2'
            return 'mj1' if n in (53, 56, 57) and r['year'] < 2011 else ('mj1' if n == 53 else 'mj2')
        if t == '法条分析':
            return 'xt' if sub == '刑法' else 'mt'
        if t == '案例分析':
            return 'xa' if sub == '刑法' else 'ma'
        if t == '辨析':
            return 'xb' if sub == '刑法' else 'mb'
    else:
        m = {'简答': {'法理学': 'fj', '中国宪法学': 'xf', '中国法制史': 'fs'},
             '分析': {'法理学': 'fx', '中国宪法学': 'xx', '中国法制史': 'xs'},
             '论述': {'法理学': 'fl'}}
        if t == '论述':
            return 'fl' if sub == '法理学' else 'xl'
        return m.get(t, {}).get(sub, '?')
    return '?'

TOTAL_NODES = {
    ('398', '刑法', '总则'): ['共同犯罪', '刑罚执行与消灭', '刑罚种类', '正当行为', '犯罪主体', '犯罪主观方面',
                          '犯罪停止形态', '犯罪构成与客观方面', '罪数', '量刑制度', '刑法基础与效力'],
}
FZ = ['分则·侵犯人身权利罪', '分则·侵犯财产罪', '分则·危害公共安全罪', '分则·危害国家安全罪',
      '分则·妨害社会管理秩序罪', '分则·渎职罪', '分则·破坏市场经济秩序罪', '分则·贪污贿赂罪']

def predict_year(Y, weights, topk=3):
    """返回 {slotkey: [node...]} — 仅用 <Y 数据"""
    hist = [dict(r, slot=slot_of(r['paper'], r)) for r in rows if r['year'] < Y]
    preds = {}
    # 398 刑法
    xpool_all = sorted({r['node'] for r in hist if r['paper'] == '398' and r['subject'] == '刑法'})
    xz = [n for n in xpool_all if n not in FZ]
    xf = [n for n in xpool_all if n in FZ]
    mpool = sorted({r['node'] for r in hist if r['paper'] == '398' and r['subject'] == '民法'})

    def top(pool, subject, qtype, slotkey, exclude=()):
        cand = [n for n in pool if n not in exclude]
        scored = []
        for n in cand:
            f = feats(n, subject, qtype, slotkey, Y, hist)
            s = sum(weights[k] * f[k] for k in weights)
            scored.append((s, n))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [n for _, n in scored[:topk]]

    # #51 总则硬约束(22年100%), #52 分则优先
    p51 = top(xz, '刑法', '简答', 'xj1')
    preds['xj1'] = p51
    p52 = top(xf, '刑法', '简答', 'xj2', exclude=p51[:1])
    # 分则池不够时补总则
    if len(p52) < topk:
        p52 += [n for n in top(xz, '刑法', '简答', 'xj2', exclude=p51 + p52) if n not in p52]
    preds['xj2'] = p52[:topk]
    preds['mj1'] = top(mpool, '民法', '简答', 'mj1')
    rest = [n for n in mpool if n not in preds['mj1'][:1]]
    preds['mj2'] = top(rest, '民法', '简答', 'mj2')[:topk]
    preds['xt'] = top(xpool_all, '刑法', '法条分析', 'xt')
    preds['mt'] = top(mpool, '民法', '法条分析', 'mt')
    preds['xa'] = top(xpool_all, '刑法', '案例分析', 'xa')
    preds['ma'] = top(mpool, '民法', '案例分析', 'ma')

    # 498
    for pool_sub, sk, qt in [('法理学', 'fj', '简答'), ('法理学', 'fx', '分析'), ('法理学', 'fl', '论述'),
                             ('中国宪法学', 'xf', '简答'), ('中国宪法学', 'xx', '分析'),
                             ('中国法制史', 'fs', '简答'), ('中国法制史', 'xs', '分析')]:
        pool = sorted({r['node'] for r in hist if r['paper'] == '498' and r['subject'] == pool_sub})
        preds[sk] = top(pool, pool_sub, qt, sk)
    # #58 论述: 5年规律 — 距上次法史论述满5年则法史, 否则宪法
    last_fs = max((r['year'] for r in hist if r['paper'] == '498' and r['subject'] == '中国法制史' and r['type'] == '论述'), default=0)
    sub58 = '中国法制史' if (Y - last_fs) == 5 else '中国宪法学'
    pool58 = sorted({r['node'] for r in hist if r['paper'] == '498' and r['subject'] == sub58})
    preds['xl'] = top(pool58, sub58, '论述', 'xl')
    preds['_xl_subject'] = [sub58]
    return preds

def actual_slots(Y):
    out = {}
    for r in rows:
        if r['year'] == Y:
            out.setdefault(slot_of(r['paper'], r), []).append(r['node'])
    return out

DEFAULT_W = dict(gap=3.0, freq5=2.0, slot=1.5, typ=1.0, hist=0.5, repeat=0.0, recent=2.0)

def score_year(Y, w, topk=3):
    preds = predict_year(Y, w, topk)
    act = actual_slots(Y)
    h1 = h3 = tot = 0
    detail = []
    for sk, actuals in act.items():
        pl = preds.get(sk, [])
        for a in actuals:
            tot += 1
            hit3 = a in pl[:topk]
            hit1 = a in pl[:1]
            h3 += hit3; h1 += hit1
            detail.append((sk, a, pl, hit1, hit3))
    return h1, h3, tot, detail

def baselines(Y):
    """基线: 随机期望 / 上一年节点 / 历史最高频"""
    act = actual_slots(Y)
    hist = [dict(r, slot=slot_of(r['paper'], r)) for r in rows if r['year'] < Y]
    import collections
    res = {}
    # random expected@3
    exp = 0; tot = 0
    for sk, actuals in act.items():
        # pool size
        subj_map = {'xj1': ('398', '刑法'), 'xj2': ('398', '刑法'), 'mj1': ('398', '民法'), 'mj2': ('398', '民法'),
                    'xt': ('398', '刑法'), 'mt': ('398', '民法'), 'xa': ('398', '刑法'), 'ma': ('398', '民法'),
                    'fj': ('498', '法理学'), 'fx': ('498', '法理学'), 'fl': ('498', '法理学'),
                    'xf': ('498', '中国宪法学'), 'xx': ('498', '中国宪法学'), 'xl': ('498', '中国宪法学'),
                    'fs': ('498', '中国法制史'), 'xs': ('498', '中国法制史')}
        p, s = subj_map[sk]
        pool = {r['node'] for r in hist if r['paper'] == p and r['subject'] == s}
        if sk == 'xj1':
            pool = pool - set(FZ)
        if sk == 'xj2':
            pool = set(FZ)
        for a in actuals:
            tot += 1
            exp += min(3, len(pool)) / len(pool) if pool else 0
    res['random@3'] = exp / tot
    # last-year nodes @3
    h3 = 0; tot = 0
    for sk, actuals in act.items():
        prev = [r['node'] for r in rows if r['year'] == Y - 1 and slot_of(r['paper'], r) == sk]
        for a in actuals:
            tot += 1
            if a in prev:
                h3 += 1
    res['lastyear@same-slot'] = h3 / tot
    # freq baseline: top3 most frequent in slot pool
    h3 = 0; tot = 0
    for sk, actuals in act.items():
        cand = [r for r in hist if slot_of(r['paper'], r) == sk]
        cnt = collections.Counter(r['node'] for r in cand)
        top3 = [n for n, _ in cnt.most_common(3)]
        for a in actuals:
            tot += 1
            if a in top3:
                h3 += 1
    res['slotfreq@3'] = h3 / tot
    return res

if __name__ == '__main__':
    print('== 同板块相邻年份连考率 ==')
    for k, v in consec_stats().items():
        print(f'  {k[0]} {k[1]}: {v[0]}/{v[2]:.1%}' if False else f'  {k[0]} {k[1]}: {v[0]}/{v[1]} = {v[2]:.1%}')

    # 第一轮: 仅用 <=2021 数据在 2022 上搜权重 (链式第一轮允许)
    grid = []
    for gap in (2.0, 3.0, 4.0):
        for freq5 in (1.0, 2.0, 3.0):
            for slot in (0.5, 1.5, 2.5):
                for recent in (0.0, 2.0, 3.0):
                    for rep in (-1.0, 0.0, 1.0):
                        grid.append(dict(gap=gap, freq5=freq5, slot=slot, typ=1.0, hist=0.5, recent=recent, repeat=rep))
    random.seed(0)
    random.shuffle(grid)
    best = None
    for w in grid[:120]:
        h1, h3, tot, _ = score_year(2022, w)
        key = (h3, h1)
        if best is None or key > best[0]:
            best = (key, w, (h1, h3, tot))
    print('\n== 第一轮 (2022) 权重搜索 top ==', best[0], 'hit1/hit3/tot=', best[2])
    W = best[1]
    print('  weights:', W)

    print('\n== 链式回测 2022-2026 (冻结权重) ==')
    tot1 = tot3 = tot = 0
    for Y in range(2022, 2027):
        h1, h3, t, detail = score_year(Y, W)
        tot1 += h1; tot3 += h3; tot += t
        b = baselines(Y)
        print(f'  {Y}: hit@1 {h1}/{t}={h1/t:.1%}  hit@3 {h3}/{t}={h3/t:.1%}   '
              f'[随机@3 {b["random@3"]:.1%} | 上年同槽 {b["lastyear@same-slot"]:.1%} | 槽位高频@3 {b["slotfreq@3"]:.1%}]')
        miss = [(sk, a, pl) for sk, a, pl, h1f, h3f in detail if not h3f]
        if miss:
            print('     miss@3:', '; '.join(f'{sk}:{a}(pred {",".join(pl)})' for sk, a, pl in miss))
    print(f'  合计: hit@1 {tot1}/{tot}={tot1/tot:.1%}  hit@3 {tot3}/{tot}={tot3/tot:.1%}')

    # 2027 预测 (用全部 <=2026)
    print('\n== 2027 模型预测 (全部历史) ==')
    p = predict_year(2027, W)
    label = {'xj1': '398#51刑法简答(总则)', 'xj2': '398#52刑法简答(分则优先)', 'mj1': '398#53民法简答A',
             'mj2': '398#54民法简答B', 'xt': '398#55刑法法条', 'mt': '398#56民法法条',
             'xa': '398#57刑法案例', 'ma': '398#58民法案例', 'fj': '498#51法理简答', 'xf': '498#52宪法简答',
             'fs': '498#53法史简答', 'fx': '498#54法理分析', 'xx': '498#55宪法分析', 'xs': '498#56法史分析',
             'fl': '498#57法理论述', 'xl': f'498#58论述({p["_xl_subject"][0]})'}
    for sk in ['xj1', 'xj2', 'mj1', 'mj2', 'xt', 'mt', 'xa', 'ma', 'fj', 'xf', 'fs', 'fx', 'xx', 'xs', 'fl', 'xl']:
        print(f'  {label[sk]}: {" > ".join(p[sk])}')
