# study

法硕（非法学）**专业基础课（398）** 与 **专业综合课（498）** 真题研究与刷题仓库（2005–2026 共 22 年全真题）；另收录考研英语一 2010–2026 年 17 套整卷及阅读分析。

## 👉 开始刷题

- **网站在线入口**：打开 `index.html`（或 GitHub Pages 首页 **<https://flypig1225.github.io/study/>**）将直接进入 **全科合一版（`quiz_all.html`）**。
- **全科合一版（398 + 498）**：合并全部 5 门学科共 **2,369 道客观题**、69 个章节单元、215 条权威法条典章卡片 → `quiz_all.html`（[⬇︎ 下载全科合一刷题页](https://github.com/Flypig1225/study/raw/main/quiz_all.html)）。首次打开会自动从浏览器中已有的旧版 `fsjc_v1` / `fszh_v1` 进度迁移合并，同步导出支持 `FSALL1:` 也向下兼容导入单科 `FSJC1:` / `FSZH1:`。
- **单科离线文件（仅留在仓库中，网站首页不单独展示）**：
  - `quiz.html`（398 基础课 · 刑法 / 民法，1,099 道客观题，36 个章节单元）
  - `quiz_zonghe.html`（498 综合课 · 法理学 / 宪法学 / 法制史，1,270 道客观题，33 个章节单元）
- 三份 HTML 默认均按 **2027 考研（2026-12）预测考频权重** 排序（可一键切换「22 年历史均分」），并在**错题集**（按章节分组）与**刷题页顶部**均为每个章节提供独立的「重刷本节错题 / 重刷全章 / 清空错题」操作；支持离线双击打开、错题按天复习、GitHub Gist 云同步与进度码互传。

下载 → 双击 → 浏览器打开即可。做题进度默认存在浏览器本地；如需电脑与手机同步，可在页面底部「跨设备同步」配置 GitHub Gist 云同步或使用同步码/文件互传合并。

### 方式二：在线直接刷（需在仓库设置里开一次 GitHub Pages）

1. 打开仓库 **Settings → Pages**
2. Source 选 **Deploy from a branch**，Branch 选 **`main`**，目录选 **`/ (root)`**，Save
3. 等 1 分钟，电脑与手机浏览器直接访问 **<https://flypig1225.github.io/study/>**

### 方式三：第三方直链渲染（不想开 Pages 时）

- <https://raw.githack.com/Flypig1225/study/main/quiz_all.html>
- <https://htmlpreview.github.io/?https://github.com/Flypig1225/study/blob/main/quiz_all.html>

## 做了什么

把 2005–2026 年 **22 套**真题（1302 道题、合计 3300 分）全部结构化、打标，产出：

- **板块分值比重表**（刑法 19 个板块 / 民法 18 个板块，按 5 个时期对比）
- **主观题 22 年考点全表**（每年简答、法条分析、案例、辨析考了什么）
- **2027 押题**（考试日 2026-12-19），含打分模型、S/A/B 分档、回避清单、5 周冲刺排期
- **章节比重拆分**（客观题 / 主观题分开排序）+ 考点复现率检验（"考过还会不会再考"）
- **单文件刷题页**（`刷题/法硕基础课-真题刷题.html`）：1100 道客观题按刑法/民法章节分组，章节进度、顺序/随机、判分、错题本按天复习、重置、历史统计，纯本地无联网
- **考研英语一素材**：2010–2026 年 17 套整卷 PDF；阅读题源、题型、跨年复现、同期热点对照与 2027 研判见 [`materials/考研英语一/`](materials/考研英语一/) 和 [`分析报告`](分析/考研英语一阅读真题题型、出处与2027押题研判.md)。

## 目录

```
materials/
  法硕非法学-基础课/     22 套真题 PDF（2005–2026，统一命名）
  考研英语一/真题/       17 套整卷 PDF（2010–2026）
  考研英语一/INDEX.md    英语一试卷索引
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
  考研英语一阅读真题题型、出处与2027押题研判.md

tools/
  extract_text.py        PDF→文本（文字层优先，缺字/扫描件走 OCR）
  parse_exam.py          按年份卷面结构表结构化题目
  classify.py            板块打标 + 统计
  recurrence.py          考点复现率检验（考点 × 年份矩阵）
  parse_answers.py       解析 PDF → data/answers.json（多版式正则 + 人工补录合并）
  build_quiz.py          tagged.json + answers_remake.json → quiz.html（398 单科）
  zh_build_quiz.py       data/zonghe/* → quiz_zonghe.html（498 单科）
  predict_2027.py        69 单元 2027 考研预测权重与热点标注模型（近5年+近9年+全期+修法/轮空信号）
  build_all_quiz.py      合并 398 + 498 为单文件全科刷题页 → quiz_all.html
刷题/
  _shell.html            398 单科刷题页模板
  _shell_zonghe.html     498 单科刷题页模板
  _shell_all.html        398 + 498 全科合一刷题页模板
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
