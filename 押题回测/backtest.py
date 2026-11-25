#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""链式回测引擎 v3：逐年预测 2022→2026 主观大题并评分。

两套策略：
- mine_vK：按提示词方法论逐年迭代（每年只用 <= Y-1 数据；依据上一年失分教训调整规则）；
- market：市面预测 PDF 的公开规则固化成模拟器，不逐年迭代。

命中判定（提示词第五条：核心考点一致即命中）：
- L1 考点级：候选 match 命中真题 hit/人工标签，或条文号一致；
- L2 板块级：候选 node 与真题 node 一致。
"""
import json, os, sys, re, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, '押题回测', 'data')
from catalog import CATALOG, EVENTS, SLOTS_398, SLOTS_498, SLOT_BASE

GT398 = json.load(open(os.path.join(D, 'gt_398.json')))
GT498 = json.load(open(os.path.join(D, 'gt_498.json')))
ALL = GT398 + GT498

SLOT_SUBJ = {'X-JD51': '刑法', 'X-JD52': '刑法', 'X-FT55': '刑法', 'X-AL57': '刑法',
             'M-JDa': '民法', 'M-JDb': '民法', 'M-FT56': '民法', 'M-AL58': '民法',
             'L-JD51': '法理学', 'XF-JD52': '中国宪法学', 'S-JD53': '中国法制史',
             'L-FX54': '法理学', 'XF-FX55': '中国宪法学', 'S-FX56': '中国法制史',
             'L-LS57': '法理学', 'LS58': '中国宪法学'}
FAMILY = {'X-JD51': '简答', 'X-JD52': '简答', 'X-FT55': '法条', 'X-AL57': '案例',
          'M-JDa': '简答', 'M-JDb': '简答', 'M-FT56': '法条', 'M-AL58': '案例',
          'L-JD51': '简答', 'XF-JD52': '简答', 'S-JD53': '简答',
          'L-FX54': '材料', 'XF-FX55': '材料', 'S-FX56': '材料',
          'L-LS57': '论述', 'LS58': '论述58'}
FAM_TYPES = {'简答': ('简答', '辨析'), '法条': ('法条分析',), '案例': ('案例分析',),
             '材料': ('分析',), '论述': ('论述',), '论述58': ('论述',)}

BIAN_RE = re.compile(r'区别|不同|界限|对比')

def actual_for_year(Y):
    out = {}
    qy = [q for q in GT398 if q['year'] == Y]
    xf = sorted([q for q in qy if q['subject'] == '刑法' and q['type'] == '简答'], key=lambda x: x['num'])
    if len(xf) >= 2: out['X-JD51'], out['X-JD52'] = xf[0], xf[1]
    mf = sorted([q for q in qy if q['subject'] == '民法' and q['type'] == '简答'], key=lambda x: x['num'])
    if len(mf) >= 2: out['M-JDa'], out['M-JDb'] = mf[0], mf[1]
    ft = {q['subject']: q for q in qy if q['type'] == '法条分析'}
    al = {q['subject']: q for q in qy if q['type'] == '案例分析'}
    out['X-FT55'] = ft.get('刑法'); out['M-FT56'] = ft.get('民法')
    out['X-AL57'] = al.get('刑法'); out['M-AL58'] = al.get('民法')
    for q in [q for q in GT498 if q['year'] == Y]:
        if q['type'] == '简答':
            out[{'法理学': 'L-JD51', '中国宪法学': 'XF-JD52', '中国法制史': 'S-JD53'}[q['subject']]] = q
        elif q['type'] == '分析':
            out[{'法理学': 'L-FX54', '中国宪法学': 'XF-FX55', '中国法制史': 'S-FX56'}[q['subject']]] = q
        elif q['type'] == '论述':
            out['L-LS57' if q['subject'] == '法理学' else 'LS58'] = q
    return {k: v for k, v in out.items() if v}

def cand_matches_q(c, q):
    hit = (q.get('hit') or ''); art = q.get('article') or ''
    if c.get('articles') and art:
        for a in c['articles']:
            base, num = a.split('第')[0], '第' + a.split('第')[1]
            if base in art and num in art: return True
    return any(kw in hit for kw in c.get('match', []))

def node_last_year(hist, subj, node, types=None):
    ys = [q['year'] for q in hist if q['subject'] == subj and q['node'] == node
          and (types is None or q['type'] in types)]
    return max(ys) if ys else 2004

def cand_last_year(hist, c):
    ys = [q['year'] for q in hist if q['subject'] == c['subj'] and cand_matches_q(c, q)]
    return max(ys) if ys else 2004

def freq_t(hist, subj, node, Y, types, win=6):
    return sum(1 for q in hist if q['subject'] == subj and q['node'] == node
               and q['type'] in types and Y - win <= q['year'] <= Y - 1)

def freq_all(hist, subj, node, types=None):
    return sum(1 for q in hist if q['subject'] == subj and q['node'] == node
               and (types is None or q['type'] in types))

def contrast_streak(hist, subj, Y, win=4):
    return sum(1 for q in hist if q['subject'] == subj and q['type'] in ('简答', '辨析')
               and Y - win <= q['year'] <= Y - 1 and BIAN_RE.search(q.get('stem', '')))

def used_articles(hist, subj):
    return [q.get('article') for q in hist if q['subject'] == subj and q['type'] == '法条分析' and q.get('article')]

def art_is_used(c, used):
    for a in c.get('articles', []):
        base, num = a.split('第')[0], '第' + a.split('第')[1]
        for u in used:
            if base in u and num in u: return True
    return False

BIAN_CODE = {  # 民法典各编 → 候选条文判编
    '总则': ['民法总则', '民法典第1', '民法典第2', '民法典第13', '民法典第14', '民法典第15', '民法典第16',
             '民法典第17', '民法典第18', '民法典第19', '民法典第20', '民法典第21', '民法典第25', '民法典第26',
             '民法典第27', '民法典第28', '民法典第29', '民法典第30', '民法典第31', '民法典第32', '民法典第33',
             '民法典第34', '民法典第35', '民法典第36', '民法典第37', '民法典第38', '民法典第39', '民法典第57',
             '民法典第58', '民法典第59', '民法典第13', '民法典第143', '民法典第144', '民法典第145', '民法典第146',
             '民法典第147', '民法典第148', '民法典第149', '民法典第150', '民法典第151', '民法典第152',
             '民法典第165', '民法典第166', '民法典第167', '民法典第168', '民法典第169', '民法典第170',
             '民法典第171', '民法典第172', '民法典第173', '民法典第174', '民法典第175', '民法典第176',
             '民法典第179', '民法典第180', '民法典第183', '民法典第184', '民法典第185', '民法典第186',
             '民法典第187', '民法典第188', '民法典第189', '民法典第190', '民法典第192', '民法典第193',
             '民法典第194', '民法典第195', '民法典第196', '民法典第197', '民法典第198', '民法典第199'],
    '物权': ['物权法', '民法典第205', '民法典第209', '民法典第210', '民法典第215', '民法典第217',
             '民法典第218', '民法典第219', '民法典第231', '民法典第235', '民法典第236', '民法典第240',
             '民法典第245', '民法典第259', '民法典第260', '民法典第266', '民法典第267', '民法典第270',
             '民法典第271', '民法典第272', '民法典第273', '民法典第274', '民法典第278', '民法典第281',
             '民法典第282', '民法典第283', '民法典第284', '民法典第285', '民法典第286', '民法典第287',
             '民法典第288', '民法典第289', '民法典第290', '民法典第291', '民法典第292', '民法典第293',
             '民法典第294', '民法典第295', '民法典第296', '民法典第297', '民法典第298', '民法典第299',
             '民法典第300', '民法典第301', '民法典第302', '民法典第303', '民法典第304', '民法典第305',
             '民法典第306', '民法典第307', '民法典第308', '民法典第309', '民法典第310', '民法典第311',
             '民法典第312', '民法典第313', '民法典第314', '民法典第315', '民法典第316', '民法典第317',
             '民法典第318', '民法典第319', '民法典第320', '民法典第321', '民法典第322', '民法典第323',
             '民法典第324', '民法典第325', '民法典第326', '民法典第327', '民法典第328', '民法典第329',
             '民法典第330', '民法典第331', '民法典第332', '民法典第333', '民法典第334', '民法典第335',
             '民法典第336', '民法典第337', '民法典第338', '民法典第339', '民法典第340', '民法典第341',
             '民法典第342', '民法典第343', '民法典第344', '民法典第345', '民法典第346', '民法典第347',
             '民法典第348', '民法典第349', '民法典第350', '民法典第351', '民法典第352', '民法典第353',
             '民法典第354', '民法典第355', '民法典第356', '民法典第357', '民法典第358', '民法典第359',
             '民法典第360', '民法典第361', '民法典第362', '民法典第363', '民法典第364', '民法典第365',
             '民法典第366', '民法典第367', '民法典第368', '民法典第369', '民法典第370', '民法典第371',
             '民法典第372', '民法典第373', '民法典第374', '民法典第375', '民法典第376', '民法典第377',
             '民法典第378', '民法典第379', '民法典第380', '民法典第381', '民法典第382', '民法典第383',
             '民法典第384', '民法典第385', '民法典第386', '民法典第387', '民法典第388', '民法典第389',
             '民法典第390', '民法典第391', '民法典第392', '民法典第393', '民法典第394', '民法典第395',
             '民法典第396', '民法典第397', '民法典第398', '民法典第399', '民法典第400', '民法典第401',
             '民法典第402', '民法典第403', '民法典第404', '民法典第405', '民法典第406', '民法典第407',
             '民法典第408', '民法典第409', '民法典第410', '民法典第411', '民法典第412', '民法典第413',
             '民法典第414', '民法典第415', '民法典第416', '民法典第417', '民法典第418', '民法典第419',
             '民法典第420', '民法典第421', '民法典第422', '民法典第423', '民法典第424', '民法典第425',
             '民法典第426', '民法典第427', '民法典第428', '民法典第429', '民法典第430', '民法典第431',
             '民法典第432', '民法典第433', '民法典第434', '民法典第435', '民法典第436', '民法典第437',
             '民法典第438', '民法典第439', '民法典第440', '民法典第441', '民法典第442', '民法典第443',
             '民法典第444', '民法典第445', '民法典第446', '民法典第447', '民法典第448', '民法典第449',
             '民法典第450', '民法典第451', '民法典第452', '民法典第453', '民法典第454', '民法典第455',
             '民法典第456', '民法典第457', '民法典第458', '民法典第459', '民法典第460', '民法典第461',
             '民法典第462', '民法典第463', '民法典第464', '民法典第465', '民法典第466', '民法典第467',
             '民法典第468', '民法典第469'],
}

def art_bian(a):
    """返回条文所属编（民法典时代）：总则/物权/其他"""
    for bian, prefixes in BIAN_CODE.items():
        for p in prefixes:
            if a.startswith(p.split('民法典第')[0]) and (p + '条')[:len(p)] <= a:
                pass
    if '物权法' in a: return '物权'
    if '民法总则' in a or '民法通则' in a: return '总则'
    m = re.match(r'民法典第(\d+)条', a)
    if m:
        n = int(m.group(1))
        if n <= 204: return '总则'
        if n <= 469: return '物权'
        return '其他'
    return '其他'

def score_cand(c, slot, Y, hist, cfg):
    subj, node, fam = c['subj'], c['node'], FAMILY[slot]
    types = FAM_TYPES[fam]
    s = cfg['prior']
    # 题族感知频次：本题型近 6 年该板块出现次数
    s += cfg['w_freq'] * min(freq_t(hist, subj, node, Y, types) / 6.0 * 3.0, 1.5)
    if cfg.get('w_allfreq'):
        s += cfg['w_allfreq'] * min(freq_all(hist, subj, node) / 10.0, 1.2)
    gap = (Y - 1) - node_last_year(hist, subj, node)
    for th, b in cfg['gap_curve']:
        if gap >= th: s += b; break
    if cfg.get('gap_dual'):
        gf = (Y - 1) - node_last_year(hist, subj, node, types)
        b_all = 0.0; b_fam = 0.0
        for th, b in cfg['gap_curve']:
            if gap >= th: b_all = b; break
        for th, b in cfg['gap_curve']:
            if gf >= th: b_fam = b; break
        s += max(0.0, b_fam - b_all)
    cy = cand_last_year(hist, c)
    pen_last = cfg.get('pen_cand_last_by_fam', {}).get(fam, cfg['pen_cand_last'])
    if cy == Y - 1: s *= pen_last
    elif cy == Y - 2: s *= cfg['pen_cand_2']
    last1 = [q for q in hist if q['subject'] == subj and q['node'] == node and q['year'] == Y - 1 and q['type'] in types]
    last2 = [q for q in hist if q['subject'] == subj and q['node'] == node and q['year'] == Y - 2 and q['type'] in types]
    if fam != '材料':  # 材料槽由"母机制"规则接管（R2）
        nld = cfg.get('nld_by_subj', {}).get(subj, cfg['node_last_delta'])
        nld = cfg.get('nld_by_fam', {}).get(fam, nld)
        if last1: s += nld
        if last2: s += cfg['node_last2_delta']
    # R2 材料"母机制"：同板块 8 年内在本题型出现 >=3 次 → 持续热门加分
    if cfg.get('recycle_materials') and fam == '材料':
        n8 = freq_t(hist, subj, node, Y, types, win=8)
        if n8 >= 3: s += cfg['recycle_materials']
        elif 3 <= (Y - 1) - node_last_year(hist, subj, node, types) <= 5:
            s += cfg['recycle_materials'] * 0.6
    # R1 论述轮换：近 3 年在本题型考过的板块回避；从未在本题型考过 → 轮空加分
    if cfg.get('lunshu_rotate') and fam in ('论述', '论述58'):
        lys = node_last_year(hist, subj, node, types)
        hot = freq_all(hist, subj, node, types) >= 3
        if hot:
            if (Y - 1) - lys in (1, 2, 3): s += cfg.get('hot_cycle_boost', 0.6)  # #57 母题周期回归
        else:
            if lys > 2004 and (Y - 1) - lys <= 3: s *= 0.6
            elif lys == 2004: s += 0.3
    if c.get('contrast') and contrast_streak(hist, subj, Y) >= cfg['contrast_need']:
        s += cfg['w_contrast']
    curve = cfg.get('newlaw_curve_by_subj', {}).get(subj, cfg['newlaw_curve'])
    fs = cfg.get('newlaw_fam_scale', {}).get(fam, 1.0)
    for ev in c.get('events', []):
        age = (Y - 1) - EVENTS[ev][1]
        if 0 <= age <= len(curve) - 1: s += cfg['w_newlaw'] * curve[age] * fs
    return s, {'gap': gap, 'cand_last': cy if cy > 2004 else None,
               'r6': freq_t(hist, subj, node, Y, types)}

def rank_slot(slot, Y, hist, cfg, exclude=()):
    cands = [c for c in CATALOG if SLOT_BASE[slot] in c['slots'] and c['id'] not in exclude]
    if slot in ('X-FT55', 'M-FT56'):
        used = used_articles(hist, SLOT_SUBJ[slot])
        cands = [c for c in cands if c.get('articles') and not all(
            any((a.split('第')[0] in u) and ('第' + a.split('第')[1]) in u for u in used) for a in c['articles'])]
    if slot == 'X-JD51':
        cands = [c for c in cands if not c['node'].startswith('分则')]
    scored = []
    for c in cands:
        s, info = score_cand(c, slot, Y, hist, cfg)
        if slot == 'X-JD52' and not c['node'].startswith('分则'):
            s *= cfg['jd52_zongze']
        if slot == 'X-AL57' and c['node'] in ('分则·侵犯财产罪', '分则·侵犯人身权利罪'):
            s *= cfg.get('rencai_boost', 1.0)
        if slot in ('X-FT55', 'M-FT56'):
            if cand_last_year(hist, c) <= 2004 and cfg.get('ft_fresh_bonus'):  # 该考点 22 年从未进过大题
                s += cfg['ft_fresh_bonus']
            if art_is_used(c, used):  # 考点内部分条文已考过：换条文重考降权（17条→18条 2025/2026 先例）
                s *= cfg.get('art_used_mild', 0.75)
            # 条文零重但板块可连考：上年同板块 ×mild，连两年 ×0.5
            types = FAM_TYPES['法条']
            n1 = freq_t(hist, c['subj'], c['node'], Y - 1, types, win=1)
            n2 = freq_t(hist, c['subj'], c['node'], Y - 2, types, win=1)
            if n1 and n2: s *= 0.5
            elif n1: s *= cfg.get('ft_node_mild', 0.8)
            # 民法法条"编走廊"：民法典时代总则/物权轮流（v3+ 规则）
            if cfg.get('ft_bian_rule') and slot == 'M-FT56':
                bian = art_bian(c['articles'][0]) if c['articles'] else '其他'
                seq = [art_bian(q['article']) for q in hist if q['subject'] == '民法'
                       and q['type'] == '法条分析' and q['year'] >= 2020 and q.get('article')]
                if seq and all(b in ('总则', '物权') for b in seq[-3:]):
                    if bian in ('总则', '物权'): s += 0.3
                    else: s -= 0.1
        if cfg.get('dynasty_rule') and slot == 'S-FX56':
            if not c['node'].startswith('隋唐') or not cfg.get('dynasty_mother'):
                d1 = [q['node'] for q in hist if q['subject'] == '中国法制史' and q['type'] == '分析' and q['year'] == Y - 1]
                d2 = [q['node'] for q in hist if q['subject'] == '中国法制史' and q['type'] == '分析' and q['year'] == Y - 2]
                if c['node'] in d1: s *= 0.45
                elif c['node'] in d2: s *= 0.7
            if cfg.get('dynasty_mother') and c['node'].startswith('隋唐'):
                s += cfg['dynasty_mother']
        # R3 史简答"破零"：该朝代从未考过简答但史料分析常客 → 破零加分
        if cfg.get('poLing_rule') and slot == 'S-JD53':
            n_jd = freq_all(hist, c['subj'], c['node'], types=('简答',))
            n_fx = freq_all(hist, c['subj'], c['node'], types=('分析',))
            if n_jd == 0:
                s += 0.9 if n_fx >= 3 else (0.5 if n_fx >= 1 else 0.0)
        scored.append((s, c, info))
    scored.sort(key=lambda x: (-x[0], -freq_all(hist, x[1]['subj'], x[1]['node']), x[1]['id']))
    return [(round(s, 3), c, i) for s, c, i in scored]

def rank_ls58(Y, hist, cfg):
    out = []
    subj_hist = [q for q in hist if q['year'] >= 2018 and q['type'] == '论述' and q['num'] == 58]
    sh_n = sum(1 for q in subj_hist if q['subject'] == '中国法制史')
    streak = 0
    for q in reversed(subj_hist):
        if q['subject'] == '中国宪法学': streak += 1
        else: break
    boost = {'XF-LS58': 0.0, 'SH-LS58': 0.0}
    if cfg.get('ls58_share'):
        # 2018 后 #58 主体份额：主导主体（>=0.7）加成、少数主体降权（宪法 8/9 固定化）
        xf_share = 1 - sh_n / max(len(subj_hist), 1)
        if len(subj_hist) >= 5:
            boost['XF-LS58'] = cfg.get('ls58_boost', 0.5) if xf_share >= 0.7 else (
                -cfg.get('ls58_boost', 0.5) * 0.7 if xf_share <= 0.3 else 0.0)
            boost['SH-LS58'] = cfg.get('ls58_boost', 0.5) if xf_share <= 0.3 else (
                -cfg.get('ls58_boost', 0.5) * 0.7 if xf_share >= 0.7 else 0.0)
    elif cfg.get('ls58_rotation') and streak >= cfg.get('ls58_streak_need', 3):
        if sh_n / max(len(subj_hist), 1) >= cfg.get('ls58_min_share', 0.2):
            boost['SH-LS58'] = cfg.get('ls58_boost', 0.5)
            boost['XF-LS58'] = -cfg.get('ls58_boost', 0.5) * 0.6
    for sl in ('XF-LS58', 'SH-LS58'):
        for c in [c for c in CATALOG if sl in c['slots']]:
            s, info = score_cand(c, 'LS58', Y, hist, cfg)
            s += boost[sl]
            out.append((s, c, info))
    out.sort(key=lambda x: (-x[0], x[1]['id']))
    return [(round(s, 3), c, i) for s, c, i in out[:3]]

def predict_year(Y, cfg398, cfg498):
    hist = [q for q in ALL if q['year'] < Y]
    preds = {}
    taken = set()
    for slot in SLOTS_398 + SLOTS_498:
        cfg = cfg398 if slot in SLOTS_398 else cfg498
        if slot == 'LS58':
            preds[slot] = rank_ls58(Y, hist, cfg); continue
        ranked = rank_slot(slot, Y, hist, cfg, exclude=taken)
        preds[slot] = ranked[:3]
        if FAMILY[slot] == '简答' and ranked:
            taken.add(ranked[0][1]['id'])
    return preds

def evaluate(Y, preds):
    acts = actual_for_year(Y)
    rows = []
    for slot, act in acts.items():
        cl = preds.get(slot, [])
        rows.append({'slot': slot, 'year': Y,
                     'actual': act.get('hit', ''), 'node': act['node'],
                     'top1': cl[0][1]['name'] if cl else '',
                     'top1_node': cl[0][1]['node'] if cl else '',
                     'top1_id': cl[0][1]['id'] if cl else '',
                     'top3': [c['id'] for _, c, _ in cl[:3]],
                     'top3_name': [c['name'][:22] for _, c, _ in cl[:3]],
                     'L1': bool(cl) and cand_matches_q(cl[0][1], act),
                     'L1_3': bool(cl) and any(cand_matches_q(c, act) for _, c, _ in cl[:3]),
                     'L2': bool(cl) and cl[0][1]['node'] == act['node'],
                     'L2_3': bool(cl) and any(c['node'] == act['node'] for _, c, _ in cl[:3])})
    return rows

def summarize(rows, name):
    t = len(rows)
    return dict(name=name, total=t,
                L1_1=sum(r['L1'] for r in rows), L1_3=sum(r['L1_3'] for r in rows),
                L2_1=sum(r['L2'] for r in rows), L2_3=sum(r['L2_3'] for r in rows),
                p=dict(L1_1=round(100*sum(r['L1'] for r in rows)/t,1), L1_3=round(100*sum(r['L1_3'] for r in rows)/t,1),
                       L2_1=round(100*sum(r['L2'] for r in rows)/t,1), L2_3=round(100*sum(r['L2_3'] for r in rows)/t,1)))

# ---------------- 配置 ----------------
def base_cfg(**kw):
    c = dict(prior=0.03, w_freq=0.9, w_allfreq=0.0,
             gap_curve=[(7, 1.0), (6, 0.8), (5, 0.5), (4, 0.3), (3, 0.15)],
             pen_cand_last=0.25, pen_cand_2=0.75, pen_cand_last_by_fam={},
             node_last_delta=-0.4, node_last2_delta=-0.15, nld_by_subj={}, nld_by_fam={},
             w_contrast=0.35, contrast_need=2,
             w_newlaw=0.9, newlaw_curve=[1.0, 0.8, 0.5, 0.3, 0.15], newlaw_curve_by_subj={},
             cap=4.0, jd52_zongze=0.75, rencai_boost=1.1, newlaw_fam_scale={}, art_used_mild=0.75, hot_cycle_boost=0.6, ls58_share=False,
             ft_node_mild=0.8, ft_bian_rule=False, dynasty_rule=False,
             recycle_materials=0.0, lunshu_rotate=False, poLing_rule=False, ft_fresh_bonus=0.4,
             gap_dual=False, dynasty_mother=0.0,
             ls58_rotation=False, ls58_boost=0.5, ls58_streak_need=3, ls58_min_share=0.2)
    c.update(kw); return c

V0 = base_cfg()

def mine_cfgs():
    cfgs = {2022: V0}
    # v1（预测2023；依据 2022 失分教训 + ≤2022 可验证规律）：
    #  ① 398 新法加成峰值移至 age2-3（"新法先考选择题，大题滞后1-4年"——2022 知识产权/刑责年龄误判）
    #  ② 民法同板块"换点连考"改加分（≤2021 连考率 15/16）
    #  ③ 材料槽 3-5 年回归加分（备案审查 2015/2019 三现）
    #  ④ 史料朝代轮转（2020/2021 连续两年唐）
    #  ⑤ #58 论述主体轮转 +0.25（2018 后宪法 7:2 主导，防过度押史）
    V1 = base_cfg(
        newlaw_curve_by_subj={'刑法': [0.5, 0.7, 1.0, 0.8, 0.5], '民法': [0.5, 0.7, 1.0, 0.8, 0.5]},
        nld_by_subj={'民法': +0.2, '刑法': -0.35},
        recycle_materials=0.3, dynasty_rule=True,
        ls58_rotation=True, ls58_boost=0.25, ls58_streak_need=3, ls58_min_share=0.25)
    cfgs[2023] = V1
    # v2（预测2024；依据 2023 失分教训）：
    #  ⑥ 题族感知频次（题型内统计，避免法条热度污染简答）【引擎级修正】
    #  ⑦ 论述主题轮换（R1）：#57/#58 近3年同板块回避、从未考过+0.3（2018-2022 #57 五年五主题）
    #  ⑧ 材料"母机制"持续热门（R2）：备案审查 8 年 3 现
    #  ⑨ 史简答"破零"（R3）：隋唐 0 简答 + 11 分析 → 2023 保辜破零验证
    #  ⑩ 案例槽考点惩罚放宽（×0.6，2019/2020 危公连考先例）；新增"可撤销/重大误解"候选（大纲知识点补齐）
    V2 = dict(V1)
    V2.update(pen_cand_last_by_fam={'案例': 0.6},
              nld_by_fam={'案例': -0.15},
              recycle_materials=0.35, lunshu_rotate=True, poLing_rule=True,
              gap_curve=[(15, 1.5), (7, 1.0), (6, 0.8), (5, 0.5), (4, 0.3), (3, 0.15)],
              newlaw_fam_scale={'简答': 0.3}, ls58_share=True, rencai_boost=1.3,
              gap_dual=True, dynasty_mother=0.3, hot_cycle_boost=1.0)
    cfgs[2024] = V2
    # v3（预测2025）：对比题倾向加强（2020-2023 刑法简答对比 3/4）；民法法条"编走廊"（民法典时代 2020-2024 总则/物权 5/5）
    V3 = dict(V2); V3['contrast_need'] = 1; V3['w_contrast'] = 0.4; V3['ft_bian_rule'] = True
    cfgs[2025] = V3
    # v4（预测2026）：冻结参数，稳定性检验
    V4 = dict(V3)
    cfgs[2026] = V4
    return cfgs

def market_cfgs():
    mk398 = base_cfg(w_freq=0.35, w_allfreq=1.15,
                     gap_curve=[(7, 1.0), (6, 0.85), (5, 0.6), (4, 0.35), (3, 0.15)],
                     pen_cand_last=0.3, pen_cand_2=0.8, pen_cand_last_by_fam={'案例': 0.6},
                     node_last_delta=+0.25, node_last2_delta=+0.1,
                     nld_by_subj={'民法': +0.35, '刑法': +0.15}, nld_by_fam={'案例': +0.1},
                     w_contrast=0.45, contrast_need=1,
                     w_newlaw=1.0, newlaw_curve=[0.7, 0.9, 1.0, 0.7, 0.4],
                     newlaw_curve_by_subj={'法理学': [1.0, 0.9, 0.6, 0.3, 0.15], '中国宪法学': [1.0, 0.9, 0.6, 0.3, 0.15]},
                     rencai_boost=1.15, recycle_materials=0.3, lunshu_rotate=True, poLing_rule=True,
                     ft_bian_rule=True, dynasty_rule=True,
                     ls58_rotation=True, ls58_boost=0.4, ls58_streak_need=2, ls58_min_share=0.2)
    mk498 = dict(mk398); mk498['w_newlaw'] = 1.2
    return {Y: (mk398, mk498) for Y in range(2022, 2027)}

NOTES = {
    2022: 'v0 初始模型（规则仅用 05-21 数据设定）',
    2023: 'v1：398新法峰值移至age2-3；民法换点连考+0.2；材料3-5年回归；史料朝代轮转；#58轮转+0.25',
    2024: 'v2：题族感知频次；论述主题轮换R1；材料母机制R2；史简答破零R3；案例惩罚放宽',
    2025: 'v3：对比题倾向加强；民法法条编走廊（总则/物权 5/5）',
    2026: 'v4：冻结参数，稳定性检验',
}

def run(model='mine', verbose=True, detail=None):
    rows_all = []
    mcfg = mine_cfgs() if model == 'mine' else market_cfgs()
    for Y in range(2022, 2027):
        if model == 'mine':
            c398, c498 = mcfg[Y], mcfg[Y]; note = NOTES[Y]
        else:
            c398, c498 = mcfg[Y]; note = '市面规则（固化）'
        preds = predict_year(Y, c398, c498)
        rows = evaluate(Y, preds)
        rows_all.extend(rows)
        if verbose:
            sm = summarize(rows, f'{model}-{Y}')
            print(f"[{model}] {Y}: L1 {sm['L1_1']}/16 (top3 {sm['L1_3']}) | L2 {sm['L2_1']}/16 (top3 {sm['L2_3']})   {note[:38]}")
        if detail == Y:
            for r in rows:
                m1 = '✓' if r['L1'] else ('○' if r['L1_3'] else '×')
                m2 = '✓' if r['L2'] else ('○' if r['L2_3'] else '×')
                print(f"  {m1}{m2} [{r['slot']:8s}] 实际={r['actual'][:18]:18s}({r['node'][:12]}) | 押:{r['top1'][:26]}({r['top1_node'][:10]})")
    return rows_all

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    detail = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if mode in ('mine', 'market', 'all'):
        if mode in ('mine', 'all'):
            rows = run('mine', detail=detail)
            print(json.dumps(summarize(rows, 'mine-chain'), ensure_ascii=False))
        if mode in ('market', 'all'):
            rows = run('market', detail=detail)
            print(json.dumps(summarize(rows, 'market-fixed'), ensure_ascii=False))
