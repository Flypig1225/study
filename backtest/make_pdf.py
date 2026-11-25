# -*- coding: utf-8 -*-
import re, html as H, pymupdf

def md_to_html(md):
    lines = md.split('\n')
    out = []
    in_table = False
    def close_table():
        nonlocal in_table
        if in_table:
            out.append('</table>')
            in_table = False
    for ln in lines:
        s = ln.rstrip()
        if s.startswith('|') and s.endswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                continue
            if not in_table:
                out.append('<table>')
                in_table = True
            tag = 'td'
            row = '<tr>' + ''.join(f'<{tag}>{H.escape(c)}</{tag}>' for c in cells) + '</tr>'
            out.append(row)
            continue
        close_table()
        if not s.strip():
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', s)
        if m:
            lv = len(m.group(1))
            out.append(f'<h{lv}>{inline(m.group(2))}</h{lv}>')
            continue
        if s.startswith('> '):
            out.append(f'<blockquote>{inline(s[2:])}</blockquote>')
            continue
        if re.match(r'^\s*[-*]\s+', s):
            t = re.sub(r'^\s*[-*]\s+', '', s)
            out.append('<li>' + inline(t) + '</li>')
            continue
        if re.match(r'^\s*\d+\.\s+', s):
            t = re.sub(r'^\s*\d+\.\s+', '', s)
            out.append('<li>' + inline(t) + '</li>')
            continue
        out.append(f'<p>{inline(s)}</p>')
    close_table()
    return '\n'.join(out)

def inline(s):
    s = H.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s

md = open('分析/法硕大题押题回测与2027预测报告.md', encoding='utf-8').read()
body = md_to_html(md)
css = """
body{font-family:sans-serif;font-size:10.5pt;line-height:1.65;color:#1a1a1a;}
h1{font-size:20pt;text-align:center;margin:0 0 12pt 0;}
h2{font-size:15pt;border-bottom:2px solid #333;padding-bottom:3pt;margin-top:18pt;}
h3{font-size:12.5pt;margin-top:12pt;}
h4{font-size:11pt;margin-top:10pt;}
table{border-collapse:collapse;width:100%;margin:8pt 0;font-size:9.5pt;}
th,td{border:1px solid #888;padding:4pt 6pt;text-align:left;vertical-align:top;}
th{background:#eee;}
blockquote{color:#444;border-left:3px solid #aaa;margin:6pt 0;padding-left:10pt;}
li{margin:3pt 0;}
p{margin:5pt 0;}
"""
story = pymupdf.Story(html=f'<html><head><style>{css}</style></head><body>{body}</body></html>')
writer = pymupdf.DocumentWriter('分析/法硕大题押题回测与2027预测报告.pdf')
mediabox = pymupdf.paper_rect('a4')
where = mediabox + (40, 40, -40, -40)
more = True
while more:
    dev = writer.begin_page(mediabox)
    more, _ = story.place(where)
    story.draw(dev)
    writer.end_page()
writer.close()
d = pymupdf.open('分析/法硕大题押题回测与2027预测报告.pdf')
print('PDF pages:', len(d))
print(d[0].get_text()[:100])
