# study

法硕（非法学）专业基础课（代码 398）真题研究仓库。

## 👉 开始刷题

收录 2005–2026 共 **1099 道客观题**，36 个章节，判分 + 解析 + 错题本按天复习。

### 方式一：下载后双击（最稳，离线可用）

**[⬇︎ 下载刷题页 HTML](https://github.com/Flypig1225/study/raw/arena/59be2c94-study/%E5%88%B7%E9%A2%98/%E6%B3%95%E7%A1%95%E5%9F%BA%E7%A1%80%E8%AF%BE-%E7%9C%9F%E9%A2%98%E5%88%B7%E9%A2%98.html)**
（约 1.1 MB · 单文件 · 无外部依赖 · 手机电脑都能开）

下载 → 双击 → 浏览器打开即可。做题进度存在浏览器本地，不联网、不上传。

### 方式二：在线直接刷（需在仓库设置里开一次 GitHub Pages）

1. 打开仓库 **Settings → Pages**
2. Source 选 **Deploy from a branch**，Branch 选 `arena/59be2c94-study`，目录选 `/ (root)`，Save
3. 等 1 分钟，访问 **<https://flypig1225.github.io/study/>**

### 方式三：第三方直链渲染（不想开 Pages 时）

- <https://raw.githack.com/Flypig1225/study/arena/59be2c94-study/%E5%88%B7%E9%A2%98/%E6%B3%95%E7%A1%95%E5%9F%BA%E7%A1%80%E8%AF%BE-%E7%9C%9F%E9%A2%98%E5%88%B7%E9%A2%98.html>
- <https://htmlpreview.github.io/?https://github.com/Flypig1225/study/blob/arena/59be2c94-study/%E5%88%B7%E9%A2%98/%E6%B3%95%E7%A1%95%E5%9F%BA%E7%A1%80%E8%AF%BE-%E7%9C%9F%E9%A2%98%E5%88%B7%E9%A2%98.html>

## 做了什么

把 2005–2026 年 **22 套**真题（1302 道题、合计 3300 分）全部结构化、打标，产出：

- **板块分值比重表**（刑法 19 个板块 / 民法 18 个板块，按 5 个时期对比）
- **主观题 22 年考点全表**（每年简答、法条分析、案例、辨析考了什么）
- **2027 押题**（考试日 2026-12-19），含打分模型、S/A/B 分档、回避清单、5 周冲刺排期
- **章节比重拆分**（客观题 / 主观题分开排序）+ 考点复现率检验（"考过还会不会再考"）
- **单文件刷题页**（`刷题/法硕基础课-真题刷题.html`）：1100 道客观题按刑法/民法章节分组，章节进度、顺序/随机、判分、错题本按天复习、重置、历史统计，纯本地无联网

## 目录

```
materials/
  法硕非法学-基础课/     22 套真题 PDF（2005–2026，统一命名）
  text/                  每套纯文本（11 套经 OCR 重建，分栏已重排）
  answer_text/           22 套答案解析的纯文本（2005–2026）
  INDEX.md               素材索引 + 卷面结构
data/
  questions.json         1302 道结构化题目
  tagged.json            题目 + 知识板块标签
  node_overrides.json    人工校正标签
  answers.json           客观题答案 + 解析（由 22 套解析 PDF 自动抽取，1099 题）
  answers_manual.json    人工补录答案（2024 答案表、OCR 粘连行）
  exclude_questions.json 无官方答案、不进刷题页的题（2013-22）
  manual_questions.json  OCR 缺行的人工补齐题
  option_fixes.json      OCR 丢行的选项补录（1 题）
分析/
  法硕基础课-真题量化分析与2027押题.md   ← 主报告
  刑法民法-章节比重-客观题与主观题.md   ← 章节比重（客观/主观拆分）+ 复现率
  附录A-主观题22年考点全表.md
  附录B-板块分值比重表.md
tools/
  extract_text.py        PDF→文本（文字层优先，缺字/扫描件走 OCR）
  parse_exam.py          按年份卷面结构表结构化题目
  classify.py            板块打标 + 统计
  recurrence.py          考点复现率检验（考点 × 年份矩阵）
  parse_answers.py       解析 PDF → data/answers.json（多版式正则 + 人工补录合并）
  build_quiz.py          tagged.json + answers.json → 刷题/法硕基础课-真题刷题.html
刷题/
  _shell.html            刷题页外壳（模板骨架，含全部 JS/CSS，去掉科目专属数据）
  法硕基础课-真题刷题.html  构建产物（需 data/answers.json 才能生成）
```

## 一分钟上手

```bash
pip install --break-system-packages pypdf pymupdf rapidocr-onnxruntime opencv-python-headless
bash tools/run_extract.sh      # PDF → materials/text/（首次约 15 分钟，纯 OCR 部分）
python3 tools/parse_exam.py    # → data/questions.json
python3 tools/classify.py      # → data/tagged.json + 板块统计
python3 tools/parse_answers.py # → data/answers.json
python3 tools/build_quiz.py    # → 刷题/法硕基础课-真题刷题.html
```

## 数据说明

- 22 套试卷每年 150 分（刑法 75 + 民法 75），主观题恒定 90 分（60%）。
- 卷面结构三次变化：2005–2010（60 题、分科两块）、2011–2017（混编、仍含辨析）、2018–2025（取消辨析，简答每题 10 分）。
- 2026 年真题（2025-12 考）已入库；2027 版《考试大纲》逐条变化未核实，押题以此为限。
- 刷题页收录 **1099 道客观题**（2005–2026 全部年份）。2013 年第 22 题官方「无答案」，已排除。
  2023 只有答案速查表、2024 只有答案表，这两年的题有答案但无逐题解析。
