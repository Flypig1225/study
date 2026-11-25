from pathlib import Path
import re, html
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
base=Path(__file__).parent
styles={
 'title':ParagraphStyle('title',fontName='STSong-Light',fontSize=17,leading=25,alignment=TA_CENTER,spaceAfter=12,textColor=colors.HexColor('#173c59'),wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='STSong-Light',fontSize=13,leading=19,spaceBefore=9,spaceAfter=6,textColor=colors.HexColor('#173c59'),wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='STSong-Light',fontSize=11,leading=17,spaceBefore=7,spaceAfter=4,textColor=colors.HexColor('#174c58'),wordWrap='CJK'),
 'body':ParagraphStyle('body',fontName='STSong-Light',fontSize=9.5,leading=16,spaceAfter=5,wordWrap='CJK',splitLongWords=True),
 'row':ParagraphStyle('row',fontName='STSong-Light',fontSize=9,leading=15,spaceAfter=5,leftIndent=5,wordWrap='CJK',splitLongWords=True),
}
def markup(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#005b88">\1</link>',s)
 s=s.replace('**','').replace('`','')
 return s
for name in ['2027押题与回测报告','市场押题调研与补充练习']:
 md=(base/(name+'.md')).read_text()
 story=[]
 for line in md.splitlines():
  s=line.strip()
  if not s: continue
  if s.startswith('|---'): continue
  typ='body'
  if s.startswith('# '): typ='title';s=s[2:]
  elif s.startswith('## '): typ='h2';s=s[3:]
  elif s.startswith('### '): typ='h3';s=s[4:]
  elif s.startswith('|'): typ='row'; s='  ｜  '.join(x.strip() for x in s.strip('|').split('|'))
  story.append(Paragraph(markup(s),styles[typ]))
 def footer(canvas,doc):
  canvas.setFont('STSong-Light',8);canvas.setFillColor(colors.grey);canvas.drawRightString(195*mm,12*mm,str(doc.page))
 SimpleDocTemplate(str(base/(name+'.pdf')),pagesize=(210*mm,297*mm),leftMargin=19*mm,rightMargin=19*mm,topMargin=17*mm,bottomMargin=18*mm,title=name).build(story,onFirstPage=footer,onLaterPages=footer)
