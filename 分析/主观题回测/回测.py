#!/usr/bin/env python3
"""固定基准：以同科同题型此前五年主观题 node 的众数预测一个章节。
不读取选择题；全库标签为事后产生，仅用于回顾性章节覆盖实验。"""
import json, collections, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
files=['data/tagged.json','data/zonghe/tagged.json']
groups=[('刑法','简答'),('刑法','法条分析'),('刑法','案例分析'),('民法','简答'),('民法','法条分析'),('民法','案例分析')]+[(s,t) for t in ['简答','分析','论述'] for s in ['法理学','中国宪法学','中国法制史']]
D=[]
for f in files:
 for q in json.loads((ROOT/f).read_text(encoding='utf8')):
  if (q['subject'],q['type']) in groups: D.append(q)
def predict(y,group):
 h=[q for q in D if (q['subject'],q['type'])==group and y-5<=q['year']<y and q.get('node')]
 nodes=collections.Counter(q['node'] for q in h)
 if not nodes:return None,0,None
 last={n:max(q['year'] for q in h if q['node']==n) for n in nodes}
 n=sorted(nodes,key=lambda n:(-nodes[n],-last[n],n))[0]
 return n,nodes[n],last[n]
out=['# 2022—2026 逐年章节基准回测日志','', '这是事后执行的时间切分实验，并非当年封存的真实预测；输入为现有事后打标，已知包含误标，结果不等于具体考点命中。完整固定规则见主报告。','']
total=hits=0
for y in range(2022,2027):
 out += [f'## {y} 年（训练窗 {y-5}—{y-1}）','', '| 科目 / 题型 | 预测章节（训练频次、末次） | 真题题号与题库标签 | 章节覆盖 |','|---|---|---|---|']
 yh=yn=0
 for group in groups:
  p,n,last=predict(y,group); actual=[q for q in D if q['year']==y and (q['subject'],q['type'])==group]
  record=[]
  for q in actual:
   hit=bool(p and q.get('node')==p); yh+=hit; yn+=1
   record.append(f"{q['num']} {q.get('node','未标注')}" + (' ✓' if hit else ' ×'))
  out.append(f"| {group[0]} {group[1]} | {p or '无历史样本'}（{n}，{last or '—'}） | {'；'.join(record) if record else '当年无此科题型'} | {sum(bool(p and q.get('node')==p) for q in actual)}/{len(actual)} |")
 out += ['',f'该年：{yh}/{yn} = {yh/yn:.1%}；分母为该年各题型全部题目数，不是预测清单数。','']
 hits+=yh;total+=yn
out += [f'## 五年合计：{hits}/{total} = {hits/total:.1%}', '', '这是标签相等的机械结果，标签错误会导致误判。尤其 2022 综合56题实为清代材料，标签却写三国两晋南北朝；跨题型和考点的细分不足。不进行事后修正以维持脚本复现，但不能把此数解释为考点严格命中率。', '', '## 2027 按同一规则的章节清单', '', '| 科目/题型 | 预测章节（2022—2026 频次、末次） |','|---|---|']
for g in groups:
 p,n,last=predict(2027,g);out.append(f'| {g[0]} {g[1]} | {p or "无历史样本"}（{n}，{last or "—"}） |')
out.append('')
(ROOT/'分析/主观题回测/逐年回测日志.md').write_text('\n'.join(out),encoding='utf8')
print(f'{hits}/{total}={hits/total:.1%}')
