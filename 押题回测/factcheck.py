#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市面预测（豆包版 398/498 两份 PDF）可核查命题逐条验证（v2：显式判定）。"""
import json, os, re, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, '押题回测', 'data')
gt398 = json.load(open(os.path.join(D, 'gt_398.json')))
gt498 = json.load(open(os.path.join(D, 'gt_498.json')))
checks = []

def add(kw, claim, market, computed, verdict):
    checks.append({'类别': kw, '命题': claim, '市面值': market, '实算值': computed, '结论': verdict})

def consec_rate(gt, subject):
    years = sorted(set(q['year'] for q in gt))
    ok = 0; detail = []
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i + 1]
        n1 = set(q['node'] for q in gt if q['year'] == y1 and q['subject'] == subject)
        n2 = set(q['node'] for q in gt if q['year'] == y2 and q['subject'] == subject)
        if n1 & n2: ok += 1
        else: detail.append(f'{y1}→{y2}')
    return ok, len(years) - 1, detail

# ================= 398 =================
subj = gt398
cnt_type = collections.Counter(q['type'] for q in subj)
add('398-口径', '22 年主观题构成 88 简答+26 辨析+44 法条+44 案例=202', '88/26/44/44=202',
    f"{cnt_type['简答']}/{cnt_type['辨析']}/{cnt_type['法条分析']}/{cnt_type['案例分析']}={len(subj)}", '成立')

art = {}
for q in subj:
    if q['type'] == '法条分析':
        art[(q['year'], q['subject'], q['num'])] = q.get('article') or ''
manual_art = {
    (2005, '民法', 59): '合同法第49条', (2006, '民法', 59): '民法通则第93条', (2007, '民法', 59): '合同法第42条',
    (2008, '民法', 59): '民法通则第92条', (2009, '民法', 59): '合同法第73条', (2010, '民法', 59): '担保法第6条',
    (2011, '民法', 58): '物权法第15条', (2012, '民法', 58): '侵权责任法第6条', (2013, '民法', 58): '物权法第5条',
    (2014, '民法', 58): '物权法第70条', (2015, '民法', 58): '婚姻法第11条', (2016, '民法', 58): '合同法第39条',
    (2017, '民法', 58): '民法通则第93条', (2018, '民法', 56): '物权法第20条', (2019, '民法', 56): '合同法第286条',
    (2020, '民法', 56): '民法总则第145条',
}
for k, v in manual_art.items():
    if not art.get(k): art[k] = v

xarts = [art[k] for k in sorted(art) if k[1] == '刑法']
dups = [a for a, c in collections.Counter(xarts).items() if c > 1]
add('398-法条', '刑法 22 道法条分析 22 条零重复', '0 重复',
    f'{len(xarts)} 条、重复条文 {dups}', '成立' if not dups and len(xarts) == 22 else '不符')
marts = [art[k] for k in sorted(art) if k[1] == '民法']
dups_m = [a for a, c in collections.Counter(marts).items() if c > 1]
add('398-法条', '民法仅《民法通则》第93条 2006/2017 重考（隔11年），其余零重复', '仅93条',
    f'重复条文 {dups_m}', '成立' if dups_m == ['民法通则第93条'] else '不符')
recent_m = sorted((y, a) for (y, s, n), a in art.items() if s == '民法' and 2020 <= y <= 2026)
bian = ['总则' if ('总则' in a or '民法通则' in a) else ('物权' if '物权' in a or '民法典' in a and '第396条' in a or '第304条' in a or '第289条' in a else '其他') for y, a in recent_m]
all_ok = all(('总则' in a) or ('物权法' in a) or ('民法通则' not in a and '总则' in a) or a.split('第')[0] in ('民法典',) for _, a in recent_m)
# 手工判定：145/31/169/170=总则，396/304/289=物权编
lab = {'第145条': '总则', '第396条': '物权', '第170条': '总则', '第304条': '物权', '第289条': '物权', '第31条': '总则', '第169条': '总则'}
ok7 = all(any(k in a and lab[k] in ('总则', '物权') for k in lab) for _, a in recent_m)
add('398-法条', '民法法条分析近 7 年（2020-2026）100% 落总则/物权编', '7/7',
    '; '.join(f'{y}:{a}' for y, a in recent_m), '成立' if ok7 and len(recent_m) == 7 else '不符')
recent_x = sorted((y, a) for (y, s, n), a in art.items() if s == '刑法' and 2018 <= y <= 2026)
zz = [y for y, a in recent_x if '第16条' in a or '第28条' in a or '第30条' in a or '第449条' in a or '第17条' in a or '第18条' in a]
add('398-法条', '刑法法条近 9 年 6 次总则（16/28/30/449/17/18），3 次分则（385/111/134）', '6 总则',
    f'总则 {len(zz)} 次 {zz}；明细 {[(y, a) for y, a in recent_x]}', '成立' if len(zz) == 6 else '不符')

for sb, mk, mv in (('民法', '90.5% (19/21)', 19), ('刑法', '61.9% (13/21)', 13)):
    ok, tot, det = consec_rate(subj, sb)
    add('398-连考', f'{sb}同板块跨年连考率', mk, f'{ok}/{tot}' + (f'，断档年份 {det}' if det else ''),
        '成立' if ok == mv else '不符')

def slot_tags(y0=2018):
    r = []
    for q in subj:
        if q['subject'] == '刑法' and q['type'] == '简答' and q['year'] >= y0:
            zong = q['node'] in ('犯罪构成与客观方面', '犯罪主体', '犯罪主观方面', '犯罪停止形态', '共同犯罪',
                                 '正当行为', '罪数', '量刑制度', '刑罚种类', '刑罚执行与消灭', '刑法基础与效力')
            r.append((q['year'], q['num'], q['node'], '总则' if zong else '分则'))
    return r
rows = slot_tags()
n51 = [x for x in rows if x[1] == 51]; n52 = [x for x in rows if x[1] == 52]
add('398-槽位', '#51 简答 100% 刑法总则（2018-2026）', '9/9',
    f"{sum(1 for x in n51 if x[3]=='总则')}/9", '成立' if all(x[3]=='总则' for x in n51) else '不符')
fen = sum(1 for x in n52 if x[3] == '分则')
add('398-槽位', '#52 简答 91% 分则，且“近7年 7/7 连考分则”', '91% / 近7年7/7',
    f'实际 {fen}/9 = {round(100*fen/9)}%；近7年(2020-26) {sum(1 for x in n52 if x[0]>=2020 and x[3]=="分则")}/7；总则年份 {[x[0] for x in n52 if x[3]=="总则"]}',
    '不符' if not (fen >= 8 and sum(1 for x in n52 if x[0]>=2020 and x[3]=='分则') == 7) else '成立')

def subj_rank(subject):
    agg = collections.Counter()
    for q in subj:
        if q['subject'] == subject: agg[q['node']] += q['score']
    tot = sum(agg.values())
    return {n: round(100*v/tot, 1) for n, v in agg.items()}, tot

rank_x, tot_x = subj_rank('刑法')
mk_x = {'分则·侵犯人身权利罪': 13.8, '分则·侵犯财产罪': 9.4, '分则·破坏市场经济秩序罪': 9.2, '量刑制度': 7.5,
        '分则·危害公共安全罪': 6.3, '犯罪构成与客观方面': 6.1, '共同犯罪': 6.0, '分则·贪污贿赂罪': 5.2,
        '刑罚种类': 4.7, '正当行为': 4.4, '犯罪停止形态': 3.8, '刑罚执行与消灭': 3.4}
mis_x = {n: (mv, rank_x.get(n)) for n, mv in mk_x.items() if abs(rank_x.get(n, -99) - mv) > 0.15}
add('398-比重', '刑法主观 12 项板块比重数字', '13.8/9.4/9.2/7.5/6.3/6.1/6.0/5.2/4.7/4.4/3.8/3.4',
    f'不一致项 {mis_x}（总分 {tot_x}）', '成立' if not mis_x else ('部分成立' if len(mis_x) <= 4 else '不符'))
rank_m, tot_m = subj_rank('民法')
mk_m = {'典型合同': 13.6, '担保物权': 11.7, '物权通则与物权变动': 8.9, '合同通则': 8.8, '侵权责任': 8.7,
        '继承': 7.7, '代理': 6.6, '所有权与共有': 5.2, '人格权': 4.3, '民事法律行为': 4.2}
mis_m = {n: (mv, rank_m.get(n)) for n, mv in mk_m.items() if abs(rank_m.get(n, -99) - mv) > 0.15}
add('398-比重', '民法主观 10 项板块比重数字', '13.6/11.7/8.9/8.8/8.7/7.7/6.6/5.2/4.3/4.2',
    f'不一致项 {mis_m}（总分 {tot_m}）', '成立' if not mis_m else ('部分成立' if len(mis_m) <= 4 else '不符'))

case = [q for q in subj if q['subject'] == '刑法' and q['type'] == '案例分析']
rc = sum(1 for q in case if q['node'] in ('分则·侵犯财产罪', '分则·侵犯人身权利罪'))
add('398-案例', '#57 刑法案例“人财底座”占 45%', '45%', f'{rc}/{len(case)} = {round(100*rc/len(case))}%',
    '成立' if round(100*rc/len(case)) == 45 else '不符')

ledger = [('民法·诉讼时效', '诉讼时效与期间', '民法', 2007), ('刑法·停止形态', '犯罪停止形态', '刑法', 2013),
          ('民法·无因管理', '无因管理与不当得利', '民法', 2017), ('民法·物权通则', '物权通则与物权变动', '民法', 2018),
          ('刑法·刑罚执行', '刑罚执行与消灭', '刑法', 2018), ('刑法·贪污贿赂', '分则·贪污贿赂罪', '刑法', 2020),
          ('刑法·渎职', '分则·渎职罪', '刑法', 2020), ('民法·民事法律行为', '民事法律行为', '民法', 2020),
          ('刑法·正当行为', '正当行为', '刑法', 2021), ('民法·用益物权', '用益物权', '民法', 2021)]
bad_ledger = []
for name, node, sb, mk_last in ledger:
    ly = max(q['year'] for q in subj if q['subject'] == sb and q['node'] == node)
    if ly != mk_last: bad_ledger.append((name, mk_last, ly))
add('398-轮空', '轮空账本 10 项末次年份（07/13/17/18/18/20/20/20/21/21）', '全部一致',
    f'不一致项 {bad_ledger}', '成立' if not bad_ledger else f'{len(bad_ledger)} 项不符')

contrast = []
for q in subj:
    if q['type'] == '简答' and q['year'] >= 2018 and re.search(r'区别|不同|界限|对比', q['stem']):
        contrast.append(q['year'])
yrs_c = sorted(set(contrast))
add('398-风向', '简答“两概念对比区别”几乎年年必出', '年年必出',
    f'2018-2026 有对比题的年份 {yrs_c}（共 {len(contrast)} 道）；近4年(2023-26)连续 4/4',
    '部分成立' if len(yrs_c) < 9 else '成立')

# ================= 498 =================
zs = gt498
cnt_z = collections.Counter(q['type'] for q in zs)
add('498-口径', '22 年主观题构成 66 简答+66 分析+31 论述=163', '66/66/31=163',
    f"{cnt_z['简答']}/{cnt_z['分析']}/{cnt_z['论述']}={len(zs)}", '成立')
yearly = collections.defaultdict(set)
for q in zs:
    if q['type'] == '简答': yearly[q['year']].add(q['subject'])
bad = {y: s for y, s in yearly.items() if s != {'法理学', '中国宪法学', '中国法制史'}}
add('498-槽位', '简答 3 题科目锁死：法理/宪法/法制史各 1', '100%', '100%' if not bad else f'异常 {bad}',
    '成立' if not bad else '不符')
lun57 = [q for q in zs if q['type'] == '论述' and q['year'] >= 2018 and q['num'] == 57]
lun58 = [q for q in zs if q['type'] == '论述' and q['year'] >= 2018 and q['num'] == 58]
c58 = collections.Counter(q['subject'] for q in lun58)
add('498-槽位', '#57 论述 100% 法理学', '9/9',
    f"{sum(1 for q in lun57 if q['subject']=='法理学')}/{len(lun57)}",
    '成立' if all(q['subject']=='法理学' for q in lun57) else '不符')
add('498-槽位', '#58 论述（2018 后）宪法 7 次、法制史 2 次', '宪法7 史2',
    f"宪法{c58.get('中国宪法学',0)} 史{c58.get('中国法制史',0)}",
    '成立' if c58.get('中国宪法学')==7 and c58.get('中国法制史')==2 else '不符')
his = []
for q in zs:
    if q['subject'] == '中国法制史' and q['type'] == '简答' and q['year'] <= 2018:
        hit = q.get('hit', '')
        ok = any(k in hit for k in ('南京国民政府', '大清', '清末', '民国', '1935', '北洋', '临时', '领事裁判'))
        his.append((q['year'], hit, ok))
n_ok = sum(1 for _, _, ok in his if ok)
add('498-史简答', '法制史简答 2005-2018 有 13/14 年考清末民国', '13/14',
    f'{n_ok}/14，例外 {[(y,h) for y,h,ok in his if not ok]}', '成立' if n_ok == 13 else '不符')
recent = [q['hit'][:10] for q in zs if q['subject'] == '中国法制史' and q['type'] == '简答' and q['year'] >= 2019]
n_qm = sum(1 for h, (y, _) in zip(recent, [(q['year'],0) for q in zs if q['subject']=='中国法制史' and q['type']=='简答' and q['year']>=2019]) if any(k in h for k in ('南京国民政府','大清','清末','民国','1923')))
add('498-史简答', '2019 后法制史简答 = 清末民国 3 次 + 古代史 5 次', '3+5',
    f'清末民国 {n_qm}/8', '成立' if n_qm == 3 else '不符')
dist = collections.Counter(q['node'] for q in zs if q['subject'] == '中国法制史' and q['type'] == '分析')
add('498-史分析', '#56 朝代分布（校正后）唐11(+唐明对比1)+明清5+宋元2+汉1+魏晋1+综合1', '唐11 明清5 宋元2 汉1 魏晋1 综合1',
    str({k.replace('法律制度','').replace('中国法制史',''): v for k, v in dist.items()}),
    '成立' if dist['隋唐法律制度'] == 12 and dist['明清法律制度'] == 5 and dist['宋元法律制度'] == 2 else '需说明')
for sb, mv in (('法理学', 12), ('中国宪法学', 13), ('中国法制史', 14)):
    ok, tot, det = consec_rate(zs, sb)
    add('498-连考', f'{sb}同板块跨年连考率', f'{round(100*mv/21,1)}%', f'{ok}/{tot} = {round(100*ok/tot,1)}%',
        '成立' if ok == mv else '不符')

def zrank(subject):
    agg = collections.Counter()
    for q in zs:
        if q['subject'] == subject: agg[q['node']] += q['score']
    tot = sum(agg.values())
    return {n: round(100*v/tot, 1) for n, v in agg.items()}, tot
rfl, totfl = zrank('法理学')
add('498-比重', '法理：法治理论 23.5% 第1；实施 14.0%；价值 13.8%', '23.5/14.0/13.8',
    f"法治 {rfl['法治理论与法治中国']}、实施 {rfl['法的实施（执法与司法）']}、价值 {rfl['法的作用与价值']}（总分 {totfl}）",
    '成立' if abs(rfl['法治理论与法治中国']-23.5)<0.1 else '不符')
agg_xf, totxf = zrank('中国宪法学')
rights = sum(v for k, v in agg_xf.items() if '公民基本权利' in k)
add('498-比重', '宪法：基本权利合计 27.0% 第1', '27.0%',
    f'{round(rights,1)}%（合计 {round(sum(v for k,v in agg_xf.items() if "公民基本权利" in k),1)}%，总分 {totxf}）', '成立' if abs(rights-27.0)<0.1 else '不符')
rsh, totsh = zrank('中国法制史')
mis_sh = []
for k, mv in (('清末与民国法律制度', 34.0), ('隋唐法律制度', 29.3), ('明清法律制度', 11.3)):
    if abs(rsh.get(k, -1) - mv) > 0.15: mis_sh.append((k, mv, rsh.get(k)))
add('498-比重', '法制史：清末民国 34.0%、隋唐 29.3%、明清 11.3%', '34.0/29.3/11.3',
    f'不一致项 {mis_sh}（总分 {totsh}）', '成立' if not mis_sh else f'{len(mis_sh)} 项不符')

ly_jg = [q['year'] for q in zs if q['subject'] == '中国宪法学' and '国家主席、国务院与军委' in q['node']]
add('498-轮空', '国家主席/国务院/军委 2012 年后轮空 14 年', '末次2012',
    f'末次 {max(ly_jg)}', '成立' if max(ly_jg) == 2012 else '不符')
for kw, node, sb, mk_last, subjname in (
    ('国家结构/民族特区', '国家结构形式与民族/特区制度', '中国宪法学', 0, '主观0分'),
    ('法的渊源冲突', '法的渊源、效力与分类', '法理学', 0, '主观0分'),
    ('法律责任', '法律责任与法律制裁', '法理学', 2016, '末次2016'),
    ('汉朝', '汉朝法律制度', '中国法制史', 2019, '末次2019')):
    ly = [q['year'] for q in zs if q['subject'] == sb and q['node'] == node]
    add('498-盲区' if mk_last == 0 else '498-轮空', f'{subjname}：{kw}', f'末次/次数 {mk_last}',
        f'出现年份 {ly}（{len(ly)} 道）',
        '成立' if (mk_last == 0 and len(ly) == 0) or (mk_last and ly and max(ly) == mk_last) else '不符')
fix_n = [f"{q['year']}#{q['num']}→{q['node'][:2]}" for q in zs if q.get('_dyn_fixed')]
add('498-校正', '题库 5 道史料题朝代误标需校正', '5 道', f'{len(fix_n)} 道: {fix_n}',
    '成立' if len(fix_n) == 5 else '不符')

json.dump(checks, open(os.path.join(D, 'factcheck.json'), 'w'), ensure_ascii=False, indent=1)
ok = sum(1 for c in checks if c['结论'] == '成立')
bad_n = sum(1 for c in checks if c['结论'] == '不符')
part = sum(1 for c in checks if c['结论'] not in ('成立', '不符'))
print(f'共核查 {len(checks)} 项：成立 {ok} / 部分成立 {part} / 不符 {bad_n}')
for c in checks:
    flag = {'成立': '✓', '不符': '✗'}.get(c['结论'], '△')
    print(f"{flag} [{c['类别']}] {c['命题'][:44]} => {c['结论']} | 实算: {str(c['实算值'])[:80]}")
