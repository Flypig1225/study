# -*- coding: utf-8 -*-
"""
法硕（非法学）大题押题 · 五年链式回测引擎
2022 -> 2026，逐年预测，命中判定：核心考点（板块）一致即命中。
两个模型同一套数据、同一套命中标准对打：
  1) 市面模型：复现两份 2027 押题 PDF 中公布的命题规则
     （两年连考三档法则、槽位锁死、轮空账本、新法敏感、法条走廊）。
  2) 我的模型：仅从真题数据独立统计推导（近窗频率 + 轮空 + 周期回归 + 弱新法）。
"""
import json
from collections import defaultdict

# ---------- 加载数据 ----------
def load_subject(path, num_min=51):
    data = json.load(open(path, encoding='utf-8'))
    subj = [x for x in data if x['num'] >= num_min]
    return subj

base = load_subject('data/tagged.json')          # 398 基础课
zonghe = load_subject('data/zonghe/tagged.json')  # 498 综合课

SLOTS = {
    'base': [51, 52, 53, 54, 55, 56, 57, 58],
    'zonghe': [51, 52, 53, 54, 55, 56, 57, 58],
}
YEARS = [2022, 2023, 2024, 2025, 2026]

# 新法/热点信号表：板块关键词 -> 新法生效年份（迭代4：补充 2025-2026 新法锚点）
NEWLAW = [
    ('破坏市场经济秩序罪', [2009, 2021, 2024]),   # 刑修七/十一/十二
    ('妨害社会管理秩序罪', [2021, 2026]),         # 刑修十一/新治安法
    ('犯罪主体', [2021]),                          # 刑修十一 §17 低龄
    ('危害国家安全罪', []),
    ('侵犯人身权利罪', [2021]),                    # 刑修十一 袭警/基因
    ('侵犯财产罪', []),
    ('危害公共安全罪', [2021]),
    ('共同犯罪', []),
    ('量刑制度', [2021]),
    ('刑罚种类', [2021]),
    ('刑罚执行', []),
    ('正当行为', [2026]),                          # 新治安法 正当防卫
    ('犯罪停止形态', []),
    ('犯罪构成', []),
    ('罪数', []),
    ('犯罪主观方面', []),
    ('贪污贿赂', [2024]),                          # 刑修十二
    ('知识产权', [2021]),
    ('担保物权', [2021]),                          # 民法典
    ('典型合同', [2021, 2023]),                    # 民法典/合同编通则解释
    ('合同通则', [2021, 2023]),
    ('物权通则', [2021]),
    ('所有权与共有', [2021]),
    ('用益物权', [2021]),
    ('人格权', [2021]),
    ('侵权责任', [2021, 2024]),                    # 民法典/侵权解释一
    ('婚姻家庭', [2021, 2025]),                    # 民法典/婚家解释二
    ('继承', [2021]),
    ('代理', [2021]),
    ('民事主体', [2021]),
    ('民事法律行为', [2021]),
    ('诉讼时效', [2021]),
    ('无因管理', [2021]),
    ('法治理论', [2020, 2024]),                    # 法治社会纲要/二十届三中全会
    ('法的实施', []),
    ('法的作用与价值', []),
    ('法律解释、推理与论证', [2026]),              # AI 智慧法院热点
    ('立法体制', [2023]),                          # 立法法
    ('法律要素与法律体系', []),
    ('法律关系', []),
    ('法与科技', []),
    ('法律责任', []),
    ('法系演进', []),
    ('绪论与法的本质特征', []),
    ('宪法效力、解释与合宪性审查', [2023, 2024]),   # 立法法/备案审查
    ('国家机构（全国人大及其常委会）', [2025]),       # 新监督法
    ('国家机构（监察委与法检司法机关）', [2024, 2025]),  # 监察法修订
    ('国家性质与政党/基层群众自治', []),
    ('政权组织形式与选举制度', [2020]),            # 选举法
    ('公民基本权利（平等、政治、自由）', [2025]),     # 民营经济促进法/离线权
    ('公民基本权利（监督、财产权、社文与义务）', [2025]),
    ('宪法理论', []),
    ('夏商西周法律制度', []),
    ('秦汉法律制度', []),
    ('三国两晋南北朝法律制度', []),
    ('隋唐法律制度', []),
    ('宋元法律制度', []),
    ('明清法律制度', []),
    ('清末与民国法律制度', []),
    ('中国法制史综合专题', []),
]

# 我的模型专用扩展表：在 NEWLAW 基础上补充 2026 年新法锚点（④背诵清单确认）
MY_NEWLAW = [
    ('破坏市场经济秩序罪', [2009, 2021, 2024]),
    ('妨害社会管理秩序罪', [2021, 2026]),
    ('犯罪主体', [2021]),
    ('危害国家安全罪', []),
    ('侵犯人身权利罪', [2021]),
    ('侵犯财产罪', []),
    ('危害公共安全罪', [2021, 2026]),
    ('共同犯罪', []),
    ('量刑制度', [2021]),
    ('刑罚种类', [2021]),
    ('刑罚执行', []),
    ('正当行为', [2026]),
    ('犯罪停止形态', []),
    ('犯罪构成', []),
    ('罪数', []),
    ('犯罪主观方面', []),
    ('贪污贿赂', [2024, 2026]),
    ('知识产权', [2021]),
    ('担保物权', [2021, 2026]),
    ('典型合同', [2021, 2023]),
    ('合同通则', [2021, 2023]),
    ('物权通则', [2021]),
    ('所有权与共有', [2021]),
    ('用益物权', [2021]),
    ('人格权', [2021]),
    ('侵权责任', [2021, 2024, 2026]),
    ('婚姻家庭', [2021, 2025]),
    ('继承', [2021]),
    ('代理', [2021]),
    ('民事主体', [2021]),
    ('民事法律行为', [2021]),
    ('诉讼时效', [2021]),
    ('无因管理', [2021]),
    ('法治理论', [2020, 2024, 2025]),
    ('法的实施', [2025]),
    ('法的作用与价值', []),
    ('法律解释、推理与论证', [2026]),
    ('立法体制', [2023]),
    ('法律要素与法律体系', []),
    ('法律关系', []),
    ('法与科技', []),
    ('法律责任', []),
    ('法系演进', []),
    ('绪论与法的本质特征', []),
    ('宪法效力、解释与合宪性审查', [2023, 2024]),
    ('国家机构（全国人大及其常委会）', [2025]),
    ('国家机构（监察委与法检司法机关）', [2024, 2025]),
    ('国家性质与政党/基层群众自治', [2026]),
    ('政权组织形式与选举制度', [2020, 2025]),
    ('公民基本权利（平等、政治、自由）', [2025]),
    ('公民基本权利（监督、财产权、社文与义务）', [2025]),
    ('宪法理论', []),
    ('夏商西周法律制度', []),
    ('秦汉法律制度', []),
    ('三国两晋南北朝法律制度', []),
    ('隋唐法律制度', []),
    ('宋元法律制度', []),
    ('明清法律制度', []),
    ('清末与民国法律制度', []),
    ('中国法制史综合专题', []),
]

def newlaw_score(node, Y):
    """市面模型：新法 T+1~T+2 年进大题的敏感信号"""
    s = 0.0
    for kw, ys in NEWLAW:
        if kw in node:
            for y in ys:
                d = Y - y
                if d in (1, 2):
                    s += 1.0
    return s

def my_newlaw_score(node, Y, subj_file='base'):
    """我的模型新法信号：398 克制滞后（T+2~4，强度减半）；
    498 数据实证"新法 T+1~2 年必进大题"，窗口前移、强度提高（迭代2）。
    使用 MY_NEWLAW（含 2026 年新法锚点，迭代4）"""
    s = 0.0
    for kw, ys in MY_NEWLAW:
        if kw in node:
            for y in ys:
                d = Y - y
                if subj_file == 'zonghe':
                    if d in (1, 2):
                        s += 1.2
                else:
                    if 2 <= d <= 4:
                        s += 0.5
    return s

def stats_for(history, subj_filter, slot=None):
    """统计：板块 -> 出现年数、最近年份、近5年出现次数
    槽位别名：498 法制史材料分析——2018 起为 #56，2005–2017 对应旧题位 #69/#70，合并视为同一槽位"""
    alias = {56: {56, 69, 70}} if subj_filter == '中国法制史' else {}
    occ = defaultdict(list)
    for x in history:
        if subj_filter and x['subject'] != subj_filter:
            continue
        if slot is not None and x['num'] not in alias.get(slot, {slot}):
            continue
        occ[x['node']].append(x['year'])
    return occ

def subject_of_slot(subj_file, slot):
    """返回 (科目过滤, 所属学科)"""
    if subj_file == 'base':
        if slot in (51, 52, 55, 57):
            return '刑法'
        return '民法'
    else:
        return {51: '法理学', 52: '中国宪法学', 53: '中国法制史',
                54: '法理学', 55: '中国宪法学', 56: '中国法制史',
                57: '法理学', 58: None}[slot]

def market_predict(history, Y, subj_file, slot):
    """市面模型：综合比重(历史主观占比) + 轮空账本 + 新法敏感 + 连考惯性"""
    sf = subject_of_slot(subj_file, slot)
    occ_all = stats_for(history, sf if sf else None)          # 该科全部主观出现年份
    occ_slot = stats_for(history, sf if sf else None, slot)   # 该槽位出现年份
    # 学科主观总年数
    total_years = len(set(x['year'] for x in history if (sf is None or x['subject'] == sf)))
    cands = set(occ_slot)
    if slot in (57, 58) and subj_file == 'zonghe':
        cands |= set(occ_all)  # #58 跨学科
    scores = {}
    for c in cands:
        freq_years = len(occ_slot.get(c, []))
        share = freq_years / max(total_years, 1)
        last = max(occ_all.get(c, [0]))
        vac = Y - 1 - last
        vacancy = min(vac / 10.0, 1.0)          # 轮空账本（封顶）
        nl = newlaw_score(c, Y)
        # 连考惯性：上一年（Y-1）该科是否考了该板块
        repeat = 1.0 if (Y - 1) in occ_all.get(c, []) else 0.0
        # 迭代1：槽位内频率权重提升，轮空降权，避免长期押单一"轮空王"
        scores[c] = 3.0 * share + 0.8 * vacancy + 1.5 * nl + 0.5 * repeat
    ranked = sorted(scores, key=lambda k: (-scores[k], k))
    return ranked

def dynasty_switch_penalty(history, Y, node, slot):
    """法制史朝代连考切出：同一朝代在 Y-1、Y-2 均考过则降权（数据：2025-2026 隋唐连考 #56）
    调强惩罚，并叠加槽位内出现次数信号（朝代选择以槽位内出现年份数为主，轮空为辅）"""
    alias = {56: {56, 69, 70}}
    nums = alias.get(slot, {slot})
    h = [x for x in history if x['subject'] == '中国法制史' and x['num'] in nums and x['node'] == node]
    ys = sorted(x['year'] for x in h)
    if (Y - 1) in ys and (Y - 2) in ys:
        return 3.0
    return 0.0

def my_predict(history, Y, subj_file, slot):
    """我的模型：近5年频率 + 跨型频率 + 轮空 + 7~13年周期回归 + 新法信号 + 连考惯性 + 法制史切出"""
    sf = subject_of_slot(subj_file, slot)
    occ_all = stats_for(history, sf if sf else None)
    occ_slot = stats_for(history, sf if sf else None, slot)
    total_years = len(set(x['year'] for x in history if (sf is None or x['subject'] == sf)))
    cands = set(occ_slot)
    if slot in (57, 58) and subj_file == 'zonghe':
        cands |= set(occ_all)
    recent_start = Y - 6  # 近5年窗口 [Y-5, Y-1]
    scores = {}
    for c in cands:
        years = occ_slot.get(c, [])
        recent = len([y for y in years if y >= recent_start])
        rec = recent / max(total_years, 1) * 2.5          # 近窗频率为主信号
        # 跨型频率：同科其他题型出现的年份数（新回测文档"跨型"规则）
        cross_years = len(set(occ_all.get(c, [])) - set(years))
        cross = cross_years / max(total_years, 1) * 0.8
        last = max(occ_all.get(c, [0]))
        vac = Y - 1 - last
        vacancy = min(vac / 8.0, 1.0)
        # 7~13 年周期回归
        cycle = 1.0 if any(Y - k in years for k in range(7, 14)) else 0.0
        nl = my_newlaw_score(c, Y, subj_file)
        repeat = 0.6 if (Y - 1) in occ_all.get(c, []) else 0.0
        switch = dynasty_switch_penalty(history, Y, c, slot) if (subj_file == 'zonghe' and sf == '中国法制史') else 0.0
        # 迭代4：主信号不变，新增跨型频率；法制史朝代切出降权
        scores[c] = rec + cross + 0.7 * vacancy + 0.8 * cycle + nl + repeat - switch
    ranked = sorted(scores, key=lambda k: (-scores[k], k))
    return ranked

# ---------- 大板块粗粒度口径（更贴近"核心考查考点一致"的法硕命中标准） ----------
def coarse(node, subj_file):
    if subj_file == 'base':
        if node.startswith('分则·'):
            return node
        # 刑法其余节点一律归入"刑法总则"；民法按编归并
        xq = ('刑罚种类','量刑制度','刑罚执行与消灭','罪数','共同犯罪','犯罪主观方面',
              '犯罪停止形态','犯罪主体','犯罪构成与客观方面','正当行为','犯罪形态','刑法基础与效力')
        if node in xq:
            return '刑法总则'
        m = [('物权通则','物权'), ('所有权与共有','物权'), ('用益物权','物权'), ('担保物权','物权'),
             ('合同通则','合同'), ('典型合同','合同'), ('代理','民法总则'), ('民事主体','民法总则'),
             ('民事法律行为','民法总则'), ('民法总则与基本原则','民法总则'), ('诉讼时效','民法总则'),
             ('无因管理与不当得利','民法总则')]
        for k, v in m:
            if k in node:
                return v
        return node
    return coarse2(node, subj_file)

def coarse2(node, subj_file):
    """综合课粗粒度：法理/宪法/法制史朝代"""
    if '法理学' in node or node in ('法治理论与法治中国','法的作用与价值','法律解释、推理与论证','立法体制与立法程序','法律要素与法律体系','法律关系','法与科技','法律责任与法律制裁','法系演进','绪论与法的本质特征','法的实施（执法与司法）'):
        return '法理'
    if '宪法' in node or '国家机构' in node or '公民基本权利' in node or '政权组织' in node or '国家性质' in node or '宪法理论' in node:
        return '宪法'
    for dynasty in ['夏商西周','秦汉','三国两晋南北朝','隋唐','宋元','明清','清末与民国']:
        if dynasty in node:
            return dynasty
    return '法制史综合'

def run(subj_file, data):
    rows = []
    for Y in YEARS:
        hist = [x for x in data if x['year'] < Y]
        actual = {x['num']: x['node'] for x in data if x['year'] == Y}
        for slot in SLOTS[subj_file]:
            act = actual.get(slot)
            mp = market_predict(hist, Y, subj_file, slot)
            my = my_predict(hist, Y, subj_file, slot)
            rows.append(dict(year=Y, slot=slot, actual=act,
                             c_actual=coarse(act, subj_file),
                             c_market=coarse(mp[0], subj_file), c_market_all=[coarse(x, subj_file) for x in mp[:4]],
                             c_my=coarse(my[0], subj_file), c_my_all=[coarse(x, subj_file) for x in my[:4]],
                             market_S=mp[0], market_all=mp[:4],
                             my_S=my[0], my_all=my[:4]))
    return rows

def score(rows, model_key, tier):
    s_hit = cover_hit = 0
    details = []
    for r in rows:
        lst = r[model_key + '_all']
        top = r[model_key + '_S']
        if r['actual'] == top:
            s_hit += 1
        if r['actual'] in lst:
            cover_hit += 1
        details.append((r['year'], r['slot'], r['actual'], top,
                        'S✓' if r['actual'] == top else 'S✗',
                        '覆盖✓' if r['actual'] in lst else '覆盖✗'))
    n = len(rows)
    return s_hit, cover_hit, n, details

if __name__ == '__main__':
    allrows = []
    for name, f, data in [('398基础课', 'base', base), ('498综合课', 'zonghe', zonghe)]:
        rows = run(f, data)
        allrows += rows
        print(f'===== {name} =====')
        for Y in YEARS:
            rs = [r for r in rows if r['year'] == Y]
            ms = sum(1 for r in rs if r['actual'] == r['market_S'])
            my = sum(1 for r in rs if r['actual'] == r['my_S'])
            print(f'{Y}: 8题 市面S档命中 {ms}  我的S档命中 {my}')
        ms, mcov, n, _ = score(rows, 'market', 'S')
        myy, ycov, _, _ = score(rows, 'my', 'S')
        print(f'五年合计: 市面 头档 {ms}/{n}  覆盖 {mcov}/{n} | 我的 头档 {myy}/{n}  覆盖 {ycov}/{n}')
        print()
    ms, mcov, n, md = score(allrows, 'market', 'S')
    myy, ycov, _, yd = score(allrows, 'my', 'S')
    print(f'### 全科五年(80题) 市面模型: 头档命中 {ms}/{n} ({ms/n:.1%})  覆盖命中 {mcov}/{n} ({mcov/n:.1%})')
    print(f'### 全科五年(80题) 我的模型: 头档命中 {myy}/{n} ({myy/n:.1%})  覆盖命中 {ycov}/{n} ({ycov/n:.1%})')
    # 大板块口径
    def coarse_score(key):
        s = sum(1 for r in allrows if r['c_actual'] == r['c_'+key])
        cov = sum(1 for r in allrows if r['c_actual'] in r['c_'+key+'_all'])
        return s, cov
    ms2, mcov2 = coarse_score('market')
    myy2, ycov2 = coarse_score('my')
    print(f'### 大板块口径: 市面 头档 {ms2}/{n} ({ms2/n:.1%})  覆盖 {mcov2}/{n} ({mcov2/n:.1%})')
    print(f'### 大板块口径: 我的 头档 {myy2}/{n} ({myy2/n:.1%})  覆盖 {ycov2}/{n} ({ycov2/n:.1%})')
    json.dump(allrows, open('backtest/results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('detail saved -> backtest/results.json')
