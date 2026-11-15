# -*- coding: utf-8 -*-
"""《立法位阶 · 批准 · 备案 · 审查》讲义页面。

版式约定：A4，左右边距 42pt，页脚基线 26pt，可用内容区 y ∈ [58, 798]。
每个 page_* 函数只负责画一页，返回内容底部 y（用于检查是否溢出版心）。
"""

from guide_base import (PW, PH, M, CW, INK, INK2, INK3, NAVY, RED, GOLD,
                        PAPER, PAPER2, LINE, GREEN, WHITE, T_CONST, T_LAW,
                        T_ADMIN, T_LOCAL, T_RULE, F_REG, F_MED, F_BOLD,
                        text, para, rrect, poly, line, hline, arrow_head,
                        header, footer, page_bg, sec_title, mix, table,
                        callout, pill, dotted, bottom_note, quiz_box, card,
                        sw, wrap_rich, draw_runs, numbox)

TOTAL = 15


def body_top(c, kicker=None, title=""):
    if title:
        header(c, title, kicker)
    return PH - 76


# ============================================================ 01 封面
def page_cover(c):
    page_bg(c, PAPER)
    # 右上角装饰金字塔
    cx = PW - 108
    top = PH - 58
    layers = [(T_CONST, "宪法"), (T_LAW, "法律"), (T_ADMIN, "行政法规"),
              (T_LOCAL, "地方性法规"), (T_RULE, "规章")]
    hh = 24.0
    for i, (col, name) in enumerate(layers):
        w = 92 + i * 32
        y = top - i * (hh + 2.6)
        poly(c, [(cx - w / 2, y), (cx + w / 2, y), (cx + w / 2 - 9, y - hh),
                 (cx - w / 2 + 9, y - hh)], fill=col)
        text(c, cx, y - hh + 7.6, name, 7.8, WHITE, F_MED, "c")

    y = PH - 262
    text(c, M, y, "法硕（非法学）· 宪法学 · 立法法", 9, GOLD, F_MED)
    y -= 34
    text(c, M, y, "立法位阶 · 批准", 26, NAVY, F_BOLD)
    y -= 31
    text(c, M, y, "备案 · 事后审查", 26, NAVY, F_BOLD)
    y -= 22
    text(c, M, y, "两页书　→　四张图　→　一条线", 10.6, INK2)
    y -= 14
    line(c, M, y, M + 130, y, GOLD, 1.8)

    y -= 32
    y = para(c, M, y, CW - 4,
             "这两页难的不是「记」，是「排」。**位阶、批准、备案、审查是四条独立的线**："
             "谁制定，管位阶；谁批准，管「批准当自己」；报谁备案，管「备案找上级」；谁来撤，管「22 / 11 / 21」。"
             "四条线各归各位，书上那 20 多个格子就不再是表格，而是同一套逻辑的四次追问。",
             9.8, 17.4, INK2)
    y -= 2
    y = para(c, M, y, CW - 4,
             "讲义按 5 步走：**① 分清两种「上下级」**（这是你没读懂那句话的根）→ **② 位阶金字塔**（部门规章为什么最小）"
             "→ **③ 批准** → **④ 备案** → **⑤ 事后审查**，最后是整表拆解、口诀与自测。",
             9.8, 17.4, INK2)

    y -= 16
    box_h = 92
    rrect(c, M, y - box_h, CW, box_h, fill=WHITE, stroke=LINE, r=6)
    rrect(c, M, y - box_h, 3.4, box_h, fill=RED, r=1.7)
    text(c, M + 15, y - 20, "先纠正一个方向性的误解：部门规章不是最大的", 9.8, RED, F_BOLD)
    para(c, M + 15, y - 37, CW - 32,
         "**部门规章是整个体系里最低的一档。** 法院审案对它只「参照」，不能作为裁判依据；"
         "它上面压着宪法、法律、行政法规、地方性法规四层。你觉得它「大」，是因为制定它的部委「级别高」——"
         "但位阶看的不是部门名气，而是**制定机关在国家权力结构中的位置**。",
         8.8, 14.6, INK2)

    y = y - box_h - 26
    items = [("位阶", "谁压着谁", T_CONST), ("批准", "批准当自己", T_LAW),
             ("备案", "备案找上级", T_ADMIN), ("审查", "22 / 11 / 21", T_LOCAL)]
    gap = 9
    bw = (CW - 3 * gap) / 4.0
    for i, (k, v, col) in enumerate(items):
        bx = M + i * (bw + gap)
        rrect(c, bx, y - 46, bw, 46, fill=WHITE, stroke=LINE, r=5)
        c.setFillColor(col)
        c.rect(bx, y - 46, bw, 2.4, stroke=0, fill=1)
        text(c, bx + 12, y - 24, k, 11.2, NAVY, F_BOLD)
        text(c, bx + 12, y - 37, v, 7.8, INK3)
    return y - 46


# ============================================================ 02 两种上下级
def page_two_lineages(c):
    page_bg(c)
    y = body_top(c, "看不懂那两页的真正原因", "① 先分清两种「上下级」")
    y = para(c, M, y, CW,
             "那两页反复出现「上级」「本级」「同级」，但它们**不是同一种上下级**——这是全部混乱的源头。"
             "同一个市政府，在「人大这条线」上被本级人大管，在「政府这条线」上被省政府管。搞混了，备案永远背不下来。",
             9.4, 15.8, INK2)
    y -= 8

    top = y
    colw = (CW - 16) / 2.0
    lineages = [
        ("第一条线：人大这条线", "权力机关 → 它的常委会 → 它产生的政府", T_CONST,
         [("县人民代表大会", "由选民选举产生，是当地的权力机关"),
          ("县人大常委会", "人大的常设机关，对人大负责"),
          ("县人民政府", "由县人大产生，对本级人大负责并报告工作")],
         "人大的「上级」＝**本级人大**；政府对它负责，常委会监督它。"),
        ("第二条线：政府这条线", "上级政府 → 下级政府", T_LOCAL,
         [("省政府", "省级国家行政机关，受国务院统一领导"),
          ("市政府", "受省政府领导，同时向本市人大负责"),
          ("县政府", "受市政府领导，同时向本县人大负责")],
         "政府的「上级」＝**上一级政府**；这条线是「领导」，不是「监督」。"),
    ]
    for i, (title, sub, col, rows, foot) in enumerate(lineages):
        x = M + i * (colw + 16)
        h = 244
        rrect(c, x, top - h, colw, h, fill=WHITE, stroke=LINE, r=6)
        c.setFillColor(col)
        c.rect(x, top - 3.4, colw, 3.4, stroke=0, fill=1)
        text(c, x + 14, top - 24, title, 10, col, F_BOLD)
        text(c, x + 14, top - 37, sub, 7.6, INK3)
        by = top - 52
        for k, (nm, desc) in enumerate(rows):
            bh = 50
            rrect(c, x + 14, by - bh, colw - 28, bh, fill=mix(col, WHITE, 0.91), stroke=None, r=4)
            text(c, x + 26, by - 18, nm, 9.2, INK, F_MED)
            para(c, x + 26, by - 31, colw - 54, desc, 7.4, 10.8, INK3)
            if k < len(rows) - 1:
                line(c, x + colw / 2.0, by - bh - 1, x + colw / 2.0, by - bh - 10, col, 1.1)
                arrow_head(c, x + colw / 2.0, by - bh - 11, 0, -1, col, 3.4)
            by -= bh + 12
        para(c, x + 14, top - h + 26, colw - 28, foot, 7.4, 11, INK3)

    y = top - 244 - 14
    y = callout(c, M, y, CW,
                "上面两张图合起来看：**县政府头上其实有两个「上级」**——本级人大（人大线）和市政府（政府线）。"
                "所以政府规章要报「本级人大常委会」，还要报「上一级政府」，两处备案并不重复，它们来自两条不同的线。",
                GREEN, 8.6, "两条线同时存在，才是备案「多处」的原因", leading=14.6)
    y -= 6

    text(c, M, y, "三种容易混的「上下」，一句话分清", 9.8, NAVY, F_BOLD)
    y -= 14
    rows = [
        ["领导关系", "国务院对全国各级行政机关；上级政府对下级政府",
         "可以**改变**，也可以**撤销**"],
        ["监督关系", "本级人大常委会对本级政府；上级人大对下级人大",
         "只能**撤销**，不能改变"],
        ["批准关系", "设区的市法规报省人大常委会批准；自治条例报批准后生效",
         "批准后**当作批准机关自己的立法**"],
    ]
    y = table(c, M, y, [58, 268, CW - 326],
              ["关系类型", "谁对谁", "能做什么"],
              rows, fs=7.9, pad=6, lh=1.5, align=["c", "l", "l"], first_col_font=F_BOLD)
    y -= 12
    y = callout(c, M, y, CW,
                "三种关系决定后文全部结论：**领导 = 可改可撤**；**监督 = 只撤不改**；**批准 = 批准机关背书**，"
                "所以能管它的是批准机关的上级。书上「批准当自己」讲的正是第三种。",
                NAVY, 8.6, "为什么必须先把这三种关系分开", leading=14.6)
    y -= 6
    y = quiz_box(c, y, [
        ("县人大常委会与县政府之间，是什么关系？",
         "**监督关系**。政府由人大产生、对人大负责，\n常委会监督它，只能撤销，不能改变。"),
        ("省政府与市政府之间，是什么关系？",
         "**领导关系**。上级政府领导下级政府，\n所以可以改变，也可以撤销。"),
        ("县政府头上到底有几个「上级」？",
         "**两个**：本级人大（人大线）和市政府（政府线）。\n备案的「多处」就来自这两条线。"),
    ])
    y -= 4
    bottom_note(c, "人大的「上级」是本级人大；政府的「上级」是上一级政府。两条线并行，所以一个法可能有多处备案。")
    footer(c, 2, TOTAL)
    return y


# ============================================================ 03 位阶金字塔
LAW_RANKS = [
    ("宪法", "全国人民代表大会", "一切法律、法规、规章都不得同宪法相抵触", T_CONST),
    ("法律", "全国人大及其常委会", "高于行政法规、地方性法规、规章", T_LAW),
    ("行政法规", "国务院", "高于地方性法规、规章", T_ADMIN),
    ("地方性法规", "省级、设区的市级人大及其常委会", "高于本级和下级地方政府规章", T_LOCAL),
    ("规章", "部门规章：国务院各部委等｜地方政府规章：省级、设区的市政府", "最低一档，法院只「参照」", T_RULE),
]


def page_pyramid(c):
    page_bg(c)
    y = body_top(c, "《立法法》第 98–101 条", "② 位阶金字塔：谁压着谁")
    y = para(c, M, y, CW,
             "效力位阶只有 5 层。判断标准不是「谁更有权」，而是**制定机关在国家权力结构中的位置**："
             "全国人大 → 全国人大常委会 → 国务院 → 省级人大 → 市级人大；越靠下，越是「执行性」的规范。",
             9.4, 15.8, INK2)
    y -= 12

    apex_y = y
    layer_h = 54
    gap = 5
    max_w = 300
    min_w = 90
    cx = M + 6 + max_w / 2.0
    for i, (name, organ, desc, col) in enumerate(LAW_RANKS):
        t0, t1 = i / 5.0, (i + 1) / 5.0
        w_top = min_w + (max_w - min_w) * t0
        w_bot = min_w + (max_w - min_w) * t1
        ty = apex_y - i * (layer_h + gap)
        by = ty - layer_h
        poly(c, [(cx - w_top / 2, ty), (cx + w_top / 2, ty),
                 (cx + w_bot / 2, by), (cx - w_bot / 2, by)], fill=col)
        nbx = cx - w_bot / 2 + 21
        c.setFillColor(mix(col, INK, 0.25))
        c.circle(nbx, by + layer_h / 2.0, 8.4, stroke=0, fill=1)
        text(c, nbx, by + layer_h / 2.0 - 3.0, str(i + 1), 7.8, WHITE, F_BOLD, "c")
        text(c, cx + 8, by + layer_h - 21, name, 11.2, WHITE, F_BOLD, "c")
        for k, ln in enumerate(str(organ).replace("\\n", "\n").split("\n")):
            text(c, cx + 8, by + layer_h - 34 - k * 9.2, ln, 7,
                 mix(col, WHITE, 0.8), F_REG, "c")
    base_y = apex_y - 5 * (layer_h + gap) + gap + 2
    line(c, cx - max_w / 2 - 8, base_y, cx + max_w / 2 + 8, base_y, INK, 1.5)
    text(c, cx, base_y - 13, "效力：上 ＞ 下　｜　适用范围：下 ＞ 上（越往下管得越细）", 7.4, INK3, F_REG, "c")

    # 右侧卡片
    col_x = M + 6 + max_w + 22
    col_w = PW - M - col_x
    yy = apex_y
    yy = card(c, col_x, yy, col_w,
              "宪法 ＞ 法律 ＞ 行政法规 ＞ 地方性法规 ＞ 规章\n箭头方向是**效力**：下位法不得与上位法抵触，抵触部分无效。",
              "一句总纲", color=GOLD, size=7.4, title_size=8.4)
    yy -= 8
    yy = card(c, col_x, yy, col_w,
              "只能在执行法律、行政法规、地方性法规的范围内制定；无上位法依据，不得减损公民权利、增加义务。",
              "为什么规章排最后", color=T_RULE, size=7.4, title_size=8.4)
    yy -= 8
    yy = card(c, col_x, yy, col_w,
              "法院审案**可以参照规章**，但裁判依据只能是法律、法规。规章连「依据」都算不上。",
              "「参照」是什么意思", color=RED, size=7.4, title_size=8.4)

    y = min(base_y - 26, yy - 4)

    # 各层身份表
    text(c, M, y, "每层的「身份证」", 9.8, NAVY, F_BOLD)
    y -= 14
    rows = [[n, o, d] for (n, o, d, col) in LAW_RANKS]
    y = table(c, M, y, [62, 196, CW - 258],
              ["层级", "谁制定", "一句话效力"], rows, fs=7.5, pad=5.4, lh=1.48,
              align=["c", "l", "l"], first_col_font=F_BOLD)
    y -= 10
    # 四个错觉
    text(c, M, y, "四个常考「错觉」", 9.8, NAVY, F_BOLD)
    y -= 14
    errs = [("①", "部门规章 ≠ 大", "部委级别高，规章位阶却最低；法院只「参照」"),
            ("②", "行政法规也怕法律", "行政法规低于法律，且不得与宪法、法律抵触"),
            ("③", "地方性法规 ＞ 本级政府规章", "注意是「本级和下级」，不是只管下级"),
            ("④", "自治条例是「变通」", "可对上位法作变通，但不得违背基本原则")]
    bw = (CW - 3 * 8) / 4.0
    for i, (n, t, sub) in enumerate(errs):
        bx = M + i * (bw + 8)
        bh = 60
        rrect(c, bx, y - bh, bw, bh, fill=WHITE, stroke=LINE, r=4)
        text(c, bx + 9, y - 14, n, 8.8, RED, F_BOLD)
        para(c, bx + 21, y - 14, bw - 26, t, 7.6, 10.8, INK, F_BOLD)
        para(c, bx + 9, y - 38, bw - 18, sub, 6.9, 10, INK3)
    y -= bh + 12
    y = callout(c, M, y, CW,
                "**为什么国务院的部门规章，会被一个市的地方性法规压住？** 地方性法规出自「人大系统」，位阶高于同级政府规章；"
                "而部门规章与地方政府规章**同等效力**。层级看的是**机关的性质**，不是「中央／地方」四个字。",
                T_CONST, 8.6, "把最反直觉的一点讲透", leading=14.8)
    footer(c, 3, TOTAL)
    return y


# ============================================================ 04 同名不同命
def page_same_name(c):
    page_bg(c)
    y = body_top(c, "为什么「地方性法规」有两级、规章有两条", "②-b　同名不同命：每层再拆开")
    y = para(c, M, y, CW,
             "金字塔每一层内部还有「大小」。考试最爱的陷阱就藏在这里：**省级法规 ＞ 设区的市级法规**，"
             "**省级政府规章 ＞ 设区的市政府规章**，**部门规章 ＝ 地方政府规章**。同名不同命，全看制定者是谁。",
             9.4, 15.8, INK2)
    y -= 12

    left_w = CW * 0.47
    right_x = M + left_w + 18
    right_w = CW - left_w - 18
    text(c, M, y, "地方性法规：两级", 9.4, NAVY, F_BOLD)
    text(c, right_x, y, "规章：两条支流", 9.4, NAVY, F_BOLD)
    y -= 14
    top = y

    yy = top
    left_items = [
        ("省级地方性法规", "省、自治区、直辖市人大及其常委会", T_LOCAL,
         "报全国人大常委会和国务院**备案**；全国人大常委会有权撤销"),
        ("设区的市地方性法规", "设区的市、自治州人大及其常委会", mix(T_LOCAL, WHITE, 0.35),
         "报省人大常委会**批准**（4 个月内）→ 由省人大常委会报全国人大常委会和国务院备案"),
    ]
    for name, organ, col, note in left_items:
        h = 78
        rrect(c, M, yy - h, left_w, h, fill=WHITE, stroke=LINE, r=5)
        c.setFillColor(col)
        c.rect(M, yy - h, 3, h, stroke=0, fill=1)
        text(c, M + 14, yy - 19, name, 9.2, col, F_BOLD)
        text(c, M + 14, yy - 32, organ, 7.2, INK3)
        para(c, M + 14, yy - 45, left_w - 26, note, 7.3, 11, INK2)
        yy -= h + 10

    ry = top
    right_items = [
        ("部门规章", "国务院各部、委员会、中国人民银行、审计署、具有行政管理职能的直属机构",
         "报**国务院**备案；国务院有权改变或撤销", T_RULE),
        ("地方政府规章（省级）", "省、自治区、直辖市人民政府",
         "报**国务院**备案，同时报**本级人大常委会**备案", mix(T_RULE, WHITE, 0.22)),
        ("地方政府规章（市级）", "设区的市、自治州人民政府",
         "报**国务院**、**省人大常委会**、**省人民政府**、**本级人大常委会**备案",
         mix(T_RULE, WHITE, 0.42)),
    ]
    for name, organ, note, col in right_items:
        h = 56
        rrect(c, right_x, ry - h, right_w, h, fill=WHITE, stroke=LINE, r=5)
        c.setFillColor(col)
        c.rect(right_x, ry - h, 3, h, stroke=0, fill=1)
        text(c, right_x + 14, ry - 17, name, 8.8, col, F_BOLD)
        para(c, right_x + 14, ry - 29, right_w - 26, organ, 6.8, 9.8, INK3)
        para(c, right_x + 14, ry - 41, right_w - 26, note, 7.2, 10.4, INK2)
        ry -= h + 8
    y = min(yy, ry) - 8

    y = callout(c, M, y, CW,
                "**批准是「生效要件」，备案是「事后告知」。** 不批准，法规压根不生效（设区的市法规、自治条例、单行条例）；"
                "备案只是已经生效之后报上去让人家看着（其余全部）。所以只有批准能「当自己」，备案只能「被撤销」。",
                GOLD, 8.6, "批准 ≠ 备案：全章最容易糊的一处", leading=14.6)
    y -= 6

    text(c, M, y, "只有三类要「批准」", 9.8, NAVY, F_BOLD)
    y -= 14
    rows = [
        ["设区的市的地方性法规", "省、自治区人大常委会", "4 个月内；审查**合法性**", "不可变通"],
        ["自治区的自治条例、单行条例", "全国人大常委会", "批准后生效", "**可作变通规定**"],
        ["自治州、自治县的自治条例、单行条例", "省、自治区、直辖市人大常委会", "批准后生效", "**可作变通规定**"],
    ]
    y = table(c, M, y, [156, 148, 118, CW - 422],
              ["报批对象", "批准机关", "关键点", "能否变通"], rows, fs=7.5, pad=5.6, lh=1.5,
              align=["l", "l", "l", "l"], first_col_font=F_BOLD)
    y -= 10
    y = quiz_box(c, y, [
        ("广州市人大制定的地方性法规，报谁批准？",
         "**省人大常委会**。设区的市法规由省级人大常委会批准，\n4 个月内审查合法性。"),
        ("广州市人大常委会的法规，与广州市政府的规章比，谁大？",
         "**法规大**。地方性法规的效力高于**本级**和下级\n地方政府规章。"),
        ("自治州的自治条例，能对法律作变通规定吗？",
         "**能**。但不得违背法律、行政法规的基本原则，\n也不得变通宪法和民族区域自治法的规定。"),
    ])
    y -= 8
    text(c, M, y, "最容易混的三组数字，配对记", 9.6, NAVY, F_BOLD)
    y -= 14
    pairs = [("省级法规 vs 市级法规", "上位法 vs 下位法", "省级法规效力更高，市级法规不得与其抵触", T_LOCAL),
             ("省级政府规章 vs 市级政府规章", "上位规章 vs 下位规章", "省级政府规章效力更高（第 101 条）", T_RULE),
             ("部门规章 vs 地方政府规章", "同级，同等效力", "各自权限内施行，冲突由国务院裁决", T_ADMIN)]
    gap = 9
    bw = (CW - 2 * gap) / 3.0
    hs = 0
    top2 = y
    for i, (a, b, c_, col) in enumerate(pairs):
        bx = M + i * (bw + gap)
        h = 66
        rrect(c, bx, top2 - h, bw, h, fill=WHITE, stroke=LINE, r=4)
        c.setFillColor(col)
        c.rect(bx, top2 - h, bw, 2.6, stroke=0, fill=1)
        text(c, bx + 11, top2 - 16, a, 8.2, INK, F_BOLD)
        text(c, bx + 11, top2 - 29, b, 7.4, col, F_MED)
        para(c, bx + 11, top2 - 42, bw - 22, c_, 7, 10, INK3)
    y = top2 - 66 - 8
    bottom_note(c, "同名不同命：看制定者。省级法规 ＞ 市级法规；省级政府规章 ＞ 市级政府规章；部门规章 ＝ 地方政府规章。")
    footer(c, 4, TOTAL)
    return y


# ============================================================ 05 批准
def page_approval(c):
    page_bg(c)
    y = body_top(c, "《立法法》第 82、85 条", "③ 批准：批准当自己")
    y = para(c, M, y, CW,
             "「批准当自己」这五个字是整章最省力的口诀：**经批准生效的法规，视为批准机关自己的立法**。"
             "既然等于它自己制定的，那出了问题就由**批准机关自己的上级**来管，而不是由制定者所在地的同级机关来管。",
             9.4, 15.8, INK2)
    y -= 12

    # 三段流程图
    top = y
    bw1, bw2, bw3 = 130.0, 152.0, 130.0
    gap = (CW - bw1 - bw2 - bw3) / 4.0
    x1 = M + gap
    xa = x1 + bw1 + gap
    x2 = xa + bw2 + gap
    bh = 64
    rrect(c, x1, top - bh, bw1, bh, fill=WHITE, stroke=T_LOCAL, r=5)
    text(c, x1 + bw1 / 2, top - 20, "晋城市人大", 9, INK, F_BOLD, "c")
    text(c, x1 + bw1 / 2, top - 34, "制定地方性法规", 7.2, INK3, F_REG, "c")
    text(c, x1 + bw1 / 2, top - 46, "（设区的市）", 7, INK3, F_REG, "c")
    text(c, x1 + bw1 / 2, top - 58, "—— 制定者", 6.8, T_LOCAL, F_MED, "c")

    rrect(c, xa, top - bh, bw2, bh, fill=mix(T_LAW, WHITE, 0.9), stroke=T_LAW, r=5)
    text(c, xa + bw2 / 2, top - 18, "山西省人大常委会", 8.8, T_LAW, F_BOLD, "c")
    text(c, xa + bw2 / 2, top - 31, "批准（4 个月内）", 7.2, INK2, F_REG, "c")
    text(c, xa + bw2 / 2, top - 43, "只审查「合法性」", 7, INK3, F_REG, "c")
    text(c, xa + bw2 / 2, top - 56, "＝视为它自己的立法", 7, T_LAW, F_MED, "c")

    rrect(c, x2, top - bh, bw3, bh, fill=WHITE, stroke=T_CONST, r=5)
    text(c, x2 + bw3 / 2, top - 20, "谁管得着", 9, T_CONST, F_BOLD, "c")
    text(c, x2 + bw3 / 2, top - 34, "省人大常委会可以", 7.2, INK3, F_REG, "c")
    text(c, x2 + bw3 / 2, top - 46, "改变、撤销它", 7.6, T_CONST, F_MED, "c")
    text(c, x2 + bw3 / 2, top - 58, "（不是全国人大）", 6.8, INK3, F_REG, "c")

    for x_from, x_to, lab in ((x1 + bw1, xa, "报批"), (xa + bw2, x2, "背书")):
        line(c, x_from + 3, top - bh / 2.0, x_to - 6, top - bh / 2.0, INK3, 1.1)
        arrow_head(c, x_to - 4, top - bh / 2.0, 1, 0, INK3, 4)
        text(c, (x_from + x_to) / 2.0, top - bh / 2.0 + 5, lab, 6.8, INK3, F_REG, "c")
    y = top - bh - 16

    y = callout(c, M, y, CW,
                "书上那句拗口的「**晋城市人大的地方性法规，当作山西省人大常委会的立法来处理**」就是这个意思："
                "一旦批准，它不再是「晋城市的法」，而是「省人大常委会背过书的法」；所以管它的是省人大常委会，"
                "而不是全国人大（全国人大管的是它常委会的立法）。",
                T_LAW, 8.6, "把书上那句话翻译成人话", leading=14.6)
    y -= 6

    text(c, M, y, "批准的三种情形（只有三种）", 9.8, NAVY, F_BOLD)
    y -= 14
    rows = [
        ["设区的市的地方性法规", "省、自治区人大常委会", "4 个月", "合法性", "不可变通"],
        ["自治区的自治条例、单行条例", "全国人大常委会", "—", "合法性", "可变通"],
        ["自治州、自治县的自治条例、单行条例", "省、自治区、直辖市人大常委会", "—", "合法性", "可变通"],
    ]
    y = table(c, M, y, [158, 146, 50, 62, CW - 416],
              ["报批对象", "批准机关", "期限", "审查什么", "能否变通"],
              rows, fs=7.5, pad=5.6, lh=1.5, align=["l", "l", "c", "l", "l"],
              first_col_font=F_BOLD)
    y -= 10
    y = para(c, M, y, CW,
             "三个「不」：**批准不是备案**（是生效要件）；**批准不是制定**（制定者仍是原机关，只是效力被背书）；"
             "**政府规章不需要批准**（备案即可）。", 8.7, 14.2, INK2)
    y -= 8
    y = quiz_box(c, y, [
        ("晋城市人大制定的法规，批准后谁有权撤销？",
         "**山西省人大常委会**。批准后视为省人大常委会的\n立法，撤销权在它自己手里。"),
        ("自治县的自治条例，报谁批准？",
         "**省、自治区、直辖市人大常委会**。\n「区州市提一级」，自治州、自治县都到省级。"),
        ("国务院部门规章需要报批准吗？",
         "**不需要**。规章只需备案，不设批准程序；\n批准只适用于法规、自治条例、单行条例。"),
    ])
    y -= 8
    text(c, M, y, "批准前后，到底变了什么", 9.6, NAVY, F_BOLD)
    y -= 14
    rows2 = [
        ["效力来源", "自己制定、自己生效（需报上级批准才生效）", "视为**批准机关**的立法，效力被「抬高」一级"],
        ["谁监督它", "制定者的同级机关", "**批准机关的上级**（如自治区 → 全国人大）"],
        ["能不能变通", "设区的市法规**不可**变通", "自治条例、单行条例**可以**变通（不违背基本原则）"],
    ]
    y = table(c, M, y, [72, 200, CW - 272],
              ["对比项", "批准前", "批准后"], rows2, fs=7.6, pad=5.4, lh=1.5,
              align=["l", "l", "l"], first_col_font=F_BOLD)
    y -= 6
    bottom_note(c, "批准 = 生效要件 ＋ 效力背书。批准之后「你的法」变成「我的法」，所以管我的上级才管得着你。")
    footer(c, 5, TOTAL)
    return y


# ============================================================ 06 备案总表
def page_filing(c):
    page_bg(c)
    y = body_top(c, "《立法法》第 109 条", "④ 备案：备案找上级")
    y = para(c, M, y, CW,
             "备案只有一句话：**谁对你说了算，你就报谁备案**。它的本质是**事后告知**——法规已经生效，报上去让人家知道，"
             "顺便留一个将来撤销的把柄。所以「备案机关」和「有权撤销的机关」大体上是同一批人。",
             9.4, 15.8, INK2)
    y -= 10

    rows = [
        ("法律", "不备案", "全国人大及其常委会制定，没有更高机关可报", T_LAW, "—"),
        ("行政法规", "全国人大常委会", "国务院制定，报全国人大常委会", T_ADMIN, "1 处"),
        ("省级地方性法规", "全国人大常委会 ＋ 国务院", "两个上级，两边都要报", T_LOCAL, "2 处"),
        ("设区的市地方性法规", "由省人大常委会 → 报全国人大常委会和国务院", "由省里**转报**，市里不直接报", mix(T_LOCAL, WHITE, 0.35), "2 处"),
        ("自治州、自治县自治条例、单行条例", "由省级人大常委会 → 报全国人大常委会和国务院", "同样由省里转报，并说明**变通情况**", mix(T_LOCAL, WHITE, 0.55), "2 处"),
        ("部门规章", "国务院", "只有国务院一个备案机关", T_RULE, "1 处"),
        ("省级政府规章", "国务院 ＋ 本级人大常委会", "政府线、人大线各报一处", mix(T_RULE, WHITE, 0.22), "2 处"),
        ("设区的市政府规章", "国务院、省人大常委会、省人民政府、本级人大常委会", "四个口都在「备案」，撤销权见下一节", mix(T_RULE, WHITE, 0.42), "4 处"),
    ]
    top = y
    cnt_h = len(rows) * 34 + 4 * (len(rows) - 1) + 16
    for name, target, note, col, cnt in rows:
        h = 34
        rrect(c, M, top - h, CW, h, fill=WHITE, stroke=LINE, r=4)
        c.setFillColor(col)
        c.rect(M, top - h, 3, h, stroke=0, fill=1)
        text(c, M + 12, top - 14, name, 8, INK, F_BOLD)
        text(c, M + 12, top - 26, note, 6.8, INK3)
        text(c, M + 168, top - 20, target, 8, col, F_MED)
        text(c, PW - M - 12, top - 20, cnt, 7.2, INK3, F_REG, "r")
        top -= h + 4
    y = top - 6

    y = callout(c, M, y, CW,
                "**三条铁律：**① **人大不备案**——法律由全国人大自己制定，没有上级可报；② **规章只到国务院**——"
                "部门规章只报国务院，不报全国人大常委会；③ **市政府规章报四个口**：国务院、省人大常委会、省政府、本级人大常委会。",
                NAVY, 8.6, "背这三条就够做题了", leading=14.6)
    y -= 4
    y = callout(c, M, y, CW,
                "**为什么法规常常「两处」、规章常常「一处」？** 法规出自人大系统，要报人大的上级（全国人大常委会），"
                "同时政府系统也要知道（国务院）；规章只出自政府系统，所以只往政府线上报，外加本级人大这一处监督。",
                GREEN, 8.6, "理解「多处」的由来，就不用死记", leading=14.6)
    y -= 4
    y = quiz_box(c, y, [
        ("国务院的行政法规要报备案吗？",
         "**要**，报全国人大常委会。\n只有「法律」不备案。"),
        ("部门规章要报全国人大常委会吗？",
         "**不要**。规章只到国务院这一级。"),
        ("设区的市政府规章要报几个地方？",
         "**四个**：国务院、省人大常委会、\n省政府、本级人大常委会。"),
    ])
    y -= 4
    bottom_note(c, "备案 ＝ 事后告知。「谁管你，你就报谁」：法律没人管 → 不备案；规章归国务院 → 只到国务院；地方的另加本级人大。")
    footer(c, 6, TOTAL)
    return y


# ============================================================ 07 备案三个反直觉
def page_filing_traps(c):
    page_bg(c)
    y = body_top(c, "为什么北京市政府规章不报全国人大", "④-b　备案的三个「反直觉」")
    y = para(c, M, y, CW,
             "书上那张「备案总结」表看着像乱码，其实是三个反直觉规则同时起作用。拆成三句话就通了。",
             9.4, 15.8, INK2)
    y -= 12

    cards = [
        ("① 人大不备案", "法律不备案", T_LAW,
         "法律由**全国人大及其常委会**制定。全国人大是最高国家权力机关，头顶上没有机关，所以法律**不备案**，"
         "也没有任何机关能撤销它（只受合宪性审查的约束）。"),
        ("② 规章只到国务院", "部门规章 → 国务院", T_RULE,
         "部门规章只报**国务院**备案，**不报全国人大常委会**。部委是国务院的组成部分，管它的是国务院；"
         "全国人大常委会管的是「法规」那一层，不直接管部门规章。"),
        ("③ 市政府规章报四个口", "国务院／省人大常委会／省政府／本级人大常委会", T_LOCAL,
         "设区的市政府规章最麻烦：**国务院**（政府线最高）、**省人大常委会**（省人大线）、**省政府**（直接上级政府）、"
         "**本级人大常委会**（本级人大线）。**但绝不报全国人大、全国人大常委会**。"),
    ]
    bw = (CW - 2 * 12) / 3.0
    top = y
    hs = 0
    for i, (title, sub, col, body) in enumerate(cards):
        bx = M + i * (bw + 12)
        b = card(c, bx, top, bw, body, title, sub, col, size=7.9, title_size=9.2)
        hs = max(hs, top - b)
    y = top - hs - 16

    text(c, M, y, "用书上两个例子验算", 9.8, NAVY, F_BOLD)
    y -= 14
    rows = [
        ["北京市政府的规章", "报**国务院** ＋ **北京市人大常委会**；\n不报全国人大、全国人大常委会",
         "排除法：它是「规章」，规章只到国务院那一级；但它是「地方」的，本级人大也要报"],
        ["晋城市人大的地方性法规", "报**国务院** ＋ **全国人大常委会**（由山西省人大常委会转报）",
         "已被省人大常委会**批准**，视同省级立法，走「省级法规」的备案路径"],
    ]
    y = table(c, M, y, [142, 208, CW - 350],
              ["对象", "报谁备案", "为什么"], rows, fs=7.8, pad=6.2, lh=1.5,
              align=["l", "l", "l"], first_col_font=F_BOLD)
    y -= 12
    y = callout(c, M, y, CW,
                "**排除法最好用：**先看它是「法规」还是「规章」。是法规、自治条例 → 全国人大常委会那个方向可能要报；"
                "是规章 → 全国人大常委会**一定不报**，只往国务院和本级／上级人大走。",
                GOLD, 8.6, "做题时最快的判断路径", leading=14.6)
    y -= 8
    text(c, M, y, "备案思维导图（背这一张）", 9.8, NAVY, F_BOLD)
    y -= 10
    y = filing_mindmap(c, y, CW, 150)
    footer(c, 7, TOTAL)
    return y


def filing_mindmap(c, y, width, height):
    top = y
    cy = top - height / 2.0
    root_w, root_h = 72, 38
    rx = M + 2
    rrect(c, rx, cy - root_h / 2, root_w, root_h, fill=NAVY, r=6)
    text(c, rx + root_w / 2, cy + 2, "备案", 10, WHITE, F_BOLD, "c")
    text(c, rx + root_w / 2, cy - 10, "报给谁", 6.8, mix(NAVY, WHITE, 0.7), F_REG, "c")

    branches = [
        ("法律", "不备案", "全国人大制定，无上级可报", T_LAW),
        ("行政法规", "全国人大常委会", "只报这一处", T_ADMIN),
        ("地方性法规", "全国人大常委会 ＋ 国务院", "设区的市由省人大常委会转报", T_LOCAL),
        ("规章", "国务院（＋本级人大常委会）", "市政府规章报四个口", T_RULE),
    ]
    bx = rx + root_w + 44
    bw = width - (bx - M) - 2
    bh = (height - 5 * (len(branches) - 1)) / len(branches)
    for i, (name, target, note, col) in enumerate(branches):
        by = top - i * (bh + 5) - bh
        c.setStrokeColor(col)
        c.setLineWidth(1.05)
        c.setDash([], 0)
        p0x, p0y = rx + root_w, cy
        mid_y = by + bh / 2
        c.line(p0x, p0y, p0x + 20, p0y)
        c.line(p0x + 20, p0y, p0x + 20, mid_y)
        c.line(p0x + 20, mid_y, bx - 12, mid_y)
        arrow_head(c, bx - 4, mid_y, 1, 0, col, 3.8)
        rrect(c, bx, by, bw, bh, fill=mix(col, WHITE, 0.92), stroke=None, r=4)
        c.setFillColor(col)
        c.rect(bx, by, 2.6, bh, stroke=0, fill=1)
        text(c, bx + 12, by + bh - 15, name, 8.4, col, F_BOLD)
        text(c, bx + 12 + sw(name, F_BOLD, 8.4) + 10, by + bh - 15, target, 8.2, INK, F_MED)
        text(c, bx + 12, by + bh - 27, note, 6.9, INK3)
    return y - height - 4


# ============================================================ 08 审查：22/11/21
def page_review_rules(c):
    page_bg(c)
    y = body_top(c, "《立法法》第 107–108 条", "⑤ 事后审查：三个数字 22 / 11 / 21")
    y = para(c, M, y, CW,
             "书上的「**22 / 11 / 21**」不是密码，是**三组审查关系的数量**。每组拆成「谁 + 对谁 + 能做什么 + 审查什么」，"
             "再也不会混。先看总表，再逐个解释。",
             9.4, 15.8, INK2)
    y -= 10

    rows = [
        ["领导 22", "上级政府 → 下级政府；上级政府部门 → 下级政府部门",
         "**改变**、**撤销**", "适当性", "有名分，所以能改"],
        ["监督 11", "本级人大常委会 → 本级政府；上级人大常委会 → 下一级人大",
         "只能**撤销**", "适当性", "监督不是领导，不能改"],
        ["批准 21", "批准机关 → 被批准机关（自治区、自治州、自治县）",
         "只能**撤销**", "合法性", "自治条例是变通，只问合不合法"],
    ]
    y = table(c, M, y, [58, 246, 76, 52, CW - 432],
              ["关系", "谁对谁", "能做什么", "审查什么", "为什么"],
              rows, fs=7.8, pad=5.8, lh=1.5, align=["c", "l", "c", "c", "l"],
              first_col_font=F_BOLD)
    y -= 16

    text(c, M, y, "三个数字站在哪条线上", 9.8, NAVY, F_BOLD)
    y -= 12
    top = y
    colw = (CW - 2 * 10) / 3.0
    data = [("22", "领导关系", "可改可撤", "适当性", GREEN,
             "政府系统：国务院 → 各部委；省政府 → 市政府；市政府 → 县政府"),
            ("11", "监督关系", "只撤不改", "适当性", NAVY,
             "人大系统：本级人大常委会 → 本级政府；上级人大常委会 → 下一级人大"),
            ("21", "批准关系", "只撤不改", "合法性", T_CONST,
             "民族自治：自治区 → 全国人大常委会；自治州、自治县 → 省级人大常委会")]
    for i, (num, name, power, std, col, desc) in enumerate(data):
        bx = M + i * (colw + 10)
        bh = 94
        rrect(c, bx, top - bh, colw, bh, fill=WHITE, stroke=LINE, r=5)
        c.setFillColor(col)
        c.rect(bx, top - bh, colw, 3, stroke=0, fill=1)
        text(c, bx + 14, top - 33, num, 25, col, F_BOLD)
        text(c, bx + 16 + sw(num, F_BOLD, 25) + 6, top - 21, name, 8.8, col, F_BOLD)
        text(c, bx + 14, top - 48, power, 8.2, INK, F_MED)
        text(c, bx + 14 + sw(power, F_MED, 8.2) + 7, top - 48, "｜ 审查 " + std, 7.8, INK3)
        para(c, bx + 14, top - 62, colw - 26, desc, 7, 10.2, INK3)
    y = top - 94 - 14

    y = callout(c, M, y, CW,
                "**为什么「改」和「撤」不一样：**能「改」说明有领导名分（政府线）；只能「撤」说明只是监督（人大线）。"
                "领导可以代替你做决定，监督只能否掉你的决定。",
                RED, 8.6, "一个字区别：改 vs 撤", leading=14.6)
    y -= 4
    y = callout(c, M, y, CW,
                "**要单独记的例外（书上的「例外①」）：**地方人大常委会对本级政府和下一级人大及其常委会，是监督关系、只能撤，"
                "**但审查的是「适当性」（合法＋合理）**，不只看合法性。这是「11 + 适当性」的特殊组合，考试最爱在这里设陷阱。",
                GOLD, 8.6, "监督关系却审「适当性」", leading=14.6)
    y -= 4
    y = quiz_box(c, y, [
        ("上级政府能改变下级政府规章吗？",
         "**能**。领导关系可改可撤，\n审查的是适当性。"),
        ("全国人大常委会能改变行政法规吗？",
         "**不能改，只能撤销**。对行政法规，常委会只有\n撤销权（第 108 条）；「改变」权在国务院。"),
        ("省级人大常委会批准的自治州条例，谁撤销？",
         "**全国人大常委会**。批准在省里，\n撤销在全国人大常委会。"),
    ])
    y -= 4
    bottom_note(c, "22 能改（领导），11 只撤（监督），21 只撤（批准）。判卷只看两个词：改得动吗？审的是合法性还是适当性？")
    footer(c, 8, TOTAL)
    return y


# ============================================================ 09 三个例外
def page_exceptions(c):
    page_bg(c)
    y = body_top(c, "《立法法》第 108 条", "⑤-b　书上「三个例外」逐条翻译")
    y = para(c, M, y, CW,
             "那栏「三个例外」写得极简，其实是三个不同的坑。每一条都能用两条线（人大线／政府线）＋「批准当自己」推出来，"
             "真正需要单记的只有第二条。",
             9.4, 15.8, INK2)
    y -= 10

    items = [
        ("例外 ①", "地方人大常委会管本级政府和下一级人大，只能撤，却审「适当性」", NAVY,
         "地方人大常委会对**本级人民政府**、以及**下一级人大及其常委会**，是**监督关系**，所以**只能撤销**。"
         "但它审查的标准是**适当性（合法性＋合理性）**，不只看合不合法。这是全章唯一「监督关系 ＋ 适当性」的组合。",
         "对比：上级政府对下级政府也审适当性，但那是**领导**关系，所以**能改**。"),
        ("例外 ②", "全国人大对「人大常委会批准的自治区自治条例」只能撤销", T_CONST,
         "自治区自治条例由**自治区人大**制定，报**全国人大常委会批准**后生效。因为「**批准当自己**」，它视为全国人大常委会的立法，"
         "撤销权便落在常委会的**上级——全国人大**。",
         "这就是书上表里「自治区的自治条例」那一行审查主体写「**全国人大**」而不是「全国人大常委会」的原因。"),
        ("例外 ③", "自治州、自治县的自治条例，只由全国人大常委会审查，排除省人大", T_LOCAL,
         "自治州、自治县的自治条例由**自治州、自治县人大**制定，报**省级人大常委会批准**后生效。"
         "撤销权被立法法明确交给**全国人大常委会**，**排除省人大**（省人大只能改变或撤销其常委会制定的地方性法规）。",
         "一句话：**批准在省里，撤销在全国人大常委会。**"),
    ]
    top = y
    for tag, title, col, body, note in items:
        bl = wrap_rich(body, 8.2, CW - 132)
        nl = wrap_rich(note, 7.4, CW - 132)
        h = 20 + len(bl) * 13.2 + len(nl) * 11.4 + 14
        rrect(c, M, top - h, CW, h, fill=WHITE, stroke=LINE, r=5)
        c.setFillColor(col)
        c.rect(M, top - h, 3, h, stroke=0, fill=1)
        text(c, M + 14, top - 16, tag, 7.8, col, F_BOLD)
        para(c, M + 52, top - 16, CW - 68, title, 8.6, 12.4, INK, F_BOLD)
        yy = top - 32
        for k, ln in enumerate(bl):
            draw_runs(c, M + 52, yy - k * 13.2, ln, 8.2, INK2)
        yy = yy - len(bl) * 13.2 - 2
        for k, ln in enumerate(nl):
            draw_runs(c, M + 52, yy - k * 11.4, ln, 7.4, INK3)
        top -= h + 8
    y = top - 2

    y = callout(c, M, y, CW,
                "**三条例外一条骨架：**人大线是「监督」，只能撤；政府线是「领导」，可以改。凡经**批准**的，撤销权归**批准机关的上级**"
                "（自治区 → 全国人大；自治州、自治县 → 全国人大常委会）。",
                GREEN, 8.6, "串成一句", leading=14.6)
    y -= 4
    y = quiz_box(c, y, [
        ("全国人大能改变自治区自治条例吗？",
         "**不能改，只能撤**。对**自治区人大**制定、常委会批准的\n自治条例，全国人大只有撤销权（第 108 条）。"),
        ("省人大能撤销省人大常委会批准的自治州条例吗？",
         "**不能**。撤销权归全国人大常委会，\n立法法明确排除省人大。"),
        ("地方人大常委会审本级政府规章，看合法性还是适当性？",
         "**适当性（合法＋合理）**。这是\n「监督关系 ＋ 适当性」的唯一组合。"),
    ])
    y -= 8
    text(c, M, y, "三条例外放在一起看", 9.6, NAVY, F_BOLD)
    y -= 14
    rows3 = [
        ["例外 ①", "地方人大常委会 → 本级政府／下一级人大", "只能撤", "**适当性**", "监督关系里唯一审适当性的"],
        ["例外 ②", "全国人大 → 常委会批准的自治区自治条例", "只能撤", "合法性", "「批准当自己」推到顶"],
        ["例外 ③", "全国人大常委会 → 自治州、自治县自治条例", "只能撤", "合法性", "排除省人大，单记"],
    ]
    y = table(c, M, y, [58, 210, 62, 56, CW - 386],
              ["例外", "谁对谁", "能做什么", "审查什么", "特别之处"], rows3, fs=7.5, pad=5.4, lh=1.5,
              align=["c", "l", "c", "c", "l"], first_col_font=F_BOLD)
    y -= 6
    bottom_note(c, "例外只有两条逻辑：① 人大线只能撤（但可能审适当性）；② 谁批准，谁就背书，撤销权往上找一级。")
    footer(c, 9, TOTAL)
    return y


# ============================================================ 10 整表拆解（对应书上大表）
TABLE_ROWS = [
    ("法律", "全国人大及其常委会", "—", "全国人大\n（改、撤）", "适当性", T_LAW),
    ("行政法规", "国务院", "全国人大常委会", "全国人大常委会\n（撤）", "合法性", T_ADMIN),
    ("省级地方性法规", "省级人大及其常委会", "全国人大常委会 ＋ 国务院", "全国人大常委会（撤）\n省级人大（改、撤）", "合法性／适当性", T_LOCAL),
    ("设区的市地方性法规", "设区的市人大及其常委会", "全国人大常委会 ＋ 国务院（省人大常委会转报）", "全国人大常委会（撤）\n省级人大（改、撤）", "合法性／适当性", mix(T_LOCAL, WHITE, 0.3)),
    ("自治区自治条例、单行条例", "自治区人大", "—", "全国人大（撤）", "合法性", T_CONST),
    ("自治州、自治县自治条例、单行条例", "自治州、自治县人大", "全国人大常委会 ＋ 国务院（省人大常委会转报）", "全国人大常委会（撤）", "合法性", mix(T_CONST, WHITE, 0.28)),
    ("部门规章", "国务院部委、行署等", "国务院", "国务院（改、撤）", "适当性", T_RULE),
    ("省级政府规章", "省政府", "国务院 ＋ 本级人大常委会", "国务院（改、撤）\n本级人大常委会（撤）", "适当性", mix(T_RULE, WHITE, 0.22)),
    ("设区的市政府规章", "设区的市政府", "国务院、省人大常委会、省政府、本级人大常委会", "国务院（改、撤）\n省政府（改、撤）\n本级人大常委会（撤）", "适当性", mix(T_RULE, WHITE, 0.4)),
]


def page_master_table(c):
    page_bg(c)
    y = body_top(c, "书上那张表，一行不落地拆开", "⑥ 整表拆解：把表格变成 4 列逻辑")
    y = para(c, M, y, CW,
             "书上那张大表有 5 列：**审查对象、制定主体、备案、审查主体和方式、审查内容**。其实它只是把四个问题并排放在一行："
             "**谁定的 → 报谁备案 → 谁能动它 → 动的时候看什么**。下面每一行都按这个顺序读。",
             9.3, 15.6, INK2)
    y -= 10

    rows = []
    for name, organ, filing, review, std, col in TABLE_ROWS:
        rows.append([name, organ, filing, review, std])
    tints = [mix(c[5], WHITE, 0.9) for c in TABLE_ROWS]
    y = table(c, M, y, [104, 104, 122, 128, CW - 458],
              ["审查对象", "制定主体", "报谁备案", "谁能动它", "审查内容"],
              rows, fs=7.1, pad=4.8, lh=1.44, row_tints=tints,
              align=["l", "l", "l", "l", "l"], first_col_font=F_BOLD, zebra=False)
    y -= 10
    y = callout(c, M, y, CW,
                "**读表的顺序就是答题的顺序：**① 看它是「法」还是「规章」；② 是「法」→ 全国人大常委会那条线可能有份；"
                "③ 是「规章」→ 全国人大常委会一定没份，只在国务院 ＋ 本级／上级人大里找；④ 再问一句「能不能改」，"
                "能改的是领导关系（政府线），只能撤的是监督或批准关系。",
                NAVY, 8.4, "四步读表法", leading=14.2)
    y -= 4
    y = callout(c, M, y, CW,
                "**书上「批准当自己」在表里的体现：**设区的市法规、自治区／州／县自治条例这三行，"
                "「审查主体」写的都是**批准机关的上级**（省级法规 → 全国人大常委会），而不是制定者所在地的同级机关。",
                GOLD, 8.4, "这张表里最深的一处", leading=14.2)
    footer(c, 10, TOTAL)
    return y


# ============================================================ 11 总思维导图
def page_overview_map(c):
    page_bg(c)
    y = body_top(c, "一页装下全部知识点", "⑧ 总思维导图")
    y = para(c, M, y, CW,
             "考前只看这一页。从左到右四层：**位阶 → 批准 → 备案 → 审查**，每一层都挂在同一句口诀上。",
             9.3, 15.6, INK2)
    y -= 10
    top = y

    # 四个主分支横排
    colw = (CW - 3 * 9) / 4.0
    branches = [
        ("位阶", T_CONST, ["宪法＞法律＞行政法规＞地方性法规＞规章",
                           "同级：部门规章 ＝ 地方政府规章",
                           "省级政府规章 ＞ 市级政府规章",
                           "规章在法院只作「参照」",
                           "下位法不得与上位法抵触"]),
        ("批准", T_LAW, ["只有三类：设区的市法规、", "自治区条例、州／县条例",
                         "区州市提一级", "批准＝生效要件", "批准后视为批准机关自己的立法"]),
        ("备案", T_ADMIN, ["法律不备案", "规章只到国务院", "法规常报两处（人大会＋国务院）",
                           "市级政府规章报四个口", "备案＝事后告知"]),
        ("审查", T_LOCAL, ["22 领导：可改可撤、适当性", "11 监督：只撤、适当性",
                           "21 批准：只撤、合法性", "例外①监督却审适当性", "全国人大只撤自治区条例"]),
    ]
    for i, (name, col, items) in enumerate(branches):
        bx = M + i * (colw + 9)
        # 顶部标签
        rrect(c, bx, top - 26, colw, 26, fill=col, r=4)
        text(c, bx + colw / 2, top - 18, name, 10.2, WHITE, F_BOLD, "c")
        # 条目
        yy = top - 34
        for it in items:
            ls = wrap_rich(it, 7.2, colw - 20)
            h = len(ls) * 10.4 + 9
            rrect(c, bx, yy - h, colw, h, fill=mix(col, WHITE, 0.93), stroke=None, r=3)
            c.setFillColor(col)
            c.circle(bx + 7, yy - h / 2.0, 2.1, stroke=0, fill=1)
            for k, ln in enumerate(ls):
                draw_runs(c, bx + 14, yy - 10.5 - k * 10.4, ln, 7.2, INK2)
            yy -= h + 3.5
    y = min(top - 26 - 5 * 30, min(top - 34 - 5 * 31 - 6, top)) - 14

    # 中间：口诀卡
    text(c, M, y, "四句口诀（背下来就能做题）", 9.6, NAVY, F_BOLD)
    y -= 14
    jingles = [
        ("位阶", "宪法法律政法规，地方规章在末尾；部门规章别嫌小，法院只能作参照。"),
        ("批准", "区州市提一级，批准当自己；批准是生效，备案是告知。"),
        ("备案", "人大不备案，规章到国务院；法规常报两处，市政府规章报四口。"),
        ("审查", "领导二二能改撤，监督一一只能撤；批准二一只撤销，例外适当性。"),
    ]
    gap2 = 8
    bw2 = (CW - 3 * gap2) / 4.0
    hs = 0
    for i, (k, v) in enumerate(jingles):
        bx = M + i * (bw2 + gap2)
        b = card(c, bx, y, bw2, v, k, color=[T_CONST, T_LAW, T_ADMIN, T_LOCAL][i],
                 size=7.4, title_size=9)
        hs = max(hs, y - b)
    y = y - hs - 16

    # 底部：三条主线
    text(c, M, y, "三条底层逻辑（全部表格都由它推出来）", 9.6, NAVY, F_BOLD)
    y -= 14
    logic = [
        ("逻辑一：两条线", "人大线（监督，只撤）｜政府线（领导，可改）。任何「谁能动它」的问题，先问它在哪条线上。", NAVY),
        ("逻辑二：批准当自己", "经批准的法规视为批准机关的立法，所以撤销权在批准机关的上级，不在制定者的同级。", RED),
        ("逻辑三：备案看上级", "谁管你，你就报谁。法律没人管→不备案；规章归国务院→只报国务院；地方的另加本级人大线。", GREEN),
    ]
    for t, s, col in logic:
        ls = wrap_rich(s, 8.2, CW - 152)
        h = max(30, len(ls) * 12.4 + 14)
        rrect(c, M, y - h, CW, h, fill=WHITE, stroke=LINE, r=4)
        c.setFillColor(col)
        c.rect(M, y - h, 3, h, stroke=0, fill=1)
        text(c, M + 14, y - h / 2.0 - 3, t, 8.8, col, F_BOLD)
        for k, ln in enumerate(ls):
            draw_runs(c, M + 136, y - 16 - k * 12.4, ln, 8.2, INK2)
        y -= h + 6

    # 考前 5 分钟速查
    y -= 6
    text(c, M, y, "考前 5 分钟速查（只看这一块）", 9.6, NAVY, F_BOLD)
    y -= 14
    quick = [
        ("位阶", "宪＞法＞行＞地＞规；规章垫底，法院只参照", T_CONST),
        ("批准", "区州市提一级；批准当自己；批准＝生效要件", T_LAW),
        ("备案", "人大不备案；规章到国务院；市政府规章报四口", T_ADMIN),
        ("审查", "22 能改能撤；11 只撤；21 只撤；例外①审适当性", T_LOCAL),
        ("答案方向", "问「谁大」→ 查位阶；问「谁能撤」→ 查两条线＋批准", NAVY),
    ]
    for t, s_, col in quick:
        ls = wrap_rich(s_, 8.4, CW - 96)
        h = max(22, len(ls) * 12.6 + 8)
        rrect(c, M, y - h, CW, h, fill=WHITE, stroke=LINE, r=3)
        c.setFillColor(col)
        c.rect(M, y - h, 2.6, h, stroke=0, fill=1)
        text(c, M + 12, y - h + 7.5, t, 8.2, col, F_BOLD)
        for k, ln in enumerate(ls):
            draw_runs(c, M + 84, y - h + 7.5 + (len(ls) - 1 - k) * 12.6, ln, 8.4, INK2)
        y -= h + 4
    footer(c, 12, TOTAL)
    return y


# ============================================================ 12 关系 × 位阶 矩阵 + 常见设问
def page_matrix(c):
    page_bg(c)
    y = body_top(c, "把四个问题放进一张网格", "⑦ 关系 × 位阶 对照矩阵")
    y = para(c, M, y, CW,
             "考试很少直接问「位阶是什么」，而是把它塞进一个具体情境。下面这张网格把**审查对象**和**三条关系**交叉起来，"
             "横着读是「这个法归谁管」，竖着读是「这类机关能管什么」。",
             9.3, 15.6, INK2)
    y -= 10

    rows = [
        ["法律", "—", "全国人大（改／撤）", "—"],
        ["行政法规", "—", "全国人大常委会（撤）", "—"],
        ["省级地方性法规", "省级人大（改／撤）", "全国人大常委会（撤）", "—"],
        ["设区的市地方性法规", "省级人大（改／撤）", "全国人大常委会（撤）", "省级人大常委会批准"],
        ["自治区自治条例", "—", "全国人大（撤）", "全国人大常委会批准"],
        ["自治州、自治县自治条例", "—", "全国人大常委会（撤）", "省级人大常委会批准"],
        ["部门规章", "国务院（改／撤）", "—", "—"],
        ["省级政府规章", "国务院（改／撤）", "本级人大常委会（撤）", "—"],
        ["设区的市政府规章", "国务院、省政府（改／撤）", "本级人大常委会（撤）", "—"],
    ]
    y = table(c, M, y, [126, 132, 150, CW - 408],
              ["审查对象", "领导线：能改能撤", "监督线：只能撤", "批准：谁批的"],
              rows, fs=7.3, pad=5, lh=1.45, align=["l", "l", "l", "l"],
              first_col_font=F_BOLD)
    y -= 12
    y = callout(c, M, y, CW,
                "**注意「备案多处」不等于「撤销权多处」：**设区的市政府规章要向四个机关备案，但有权撤销它的只有**国务院、省政府**"
                "（可改可撤）和**本级人大常委会**（只能撤）；**省人大常委会只是接收备案**，并不撤销。",
                RED, 8.5, "最容易记串的一处", leading=14.4)
    y -= 6
    y = callout(c, M, y, CW,
                "**竖着读的规律：**同一列里，「领导线」出现的一定是政府（国务院／省政府），因为它有领导名分；"
                "「监督线」出现的一定是人大常委会，因为它只能撤；「批准」列只出现三类民族自治／设区的市的对象。",
                NAVY, 8.5, "这张网格的读法", leading=14.4)
    y -= 6

    text(c, M, y, "四道最像真题的设问", 9.6, NAVY, F_BOLD)
    y -= 14
    qa = [
        ("①「某设区的市的地方性法规，与本市政府的规章冲突，谁优先？」",
         "**地方性法规优先**。地方性法规的效力高于本级和下级地方政府规章（第 100 条）。"),
        ("②「国务院部门规章与某省政府规章冲突，怎么处理？」",
         "**同等效力**，各自权限内施行；不能确定如何适用时，由**国务院裁决**。"),
        ("③「某自治县自治条例的规定与法律不一致，是否一律无效？」",
         "**不一定**。自治条例可依法作**变通规定**，只要不违背法律、行政法规的基本原则即有效。"),
        ("④「全国人大常委会能否撤销省政府规章？」",
         "**不能**。省政府规章由**国务院**改变或撤销，本级人大常委会只能撤销；全国人大常委会管的是法规层级。"),
    ]
    for q, a in qa:
        ql = wrap_rich(q, 8.3, CW - 24)
        al = wrap_rich(a, 7.8, CW - 36)
        h = len(ql) * 12.6 + len(al) * 11.8 + 14
        rrect(c, M, y - h, CW, h, fill=WHITE, stroke=LINE, r=4)
        c.setFillColor(NAVY)
        c.rect(M, y - h, 2.6, h, stroke=0, fill=1)
        for k, ln in enumerate(ql):
            draw_runs(c, M + 12, y - 13 - k * 12.6, ln, 8.3, INK)
        yy = y - 13 - len(ql) * 12.6 - 2
        for k, ln in enumerate(al):
            draw_runs(c, M + 20, yy - k * 11.8, ln, 7.8, INK2)
        y -= h + 6
    footer(c, 11, TOTAL)
    return y
