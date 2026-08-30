import json, pathlib, html
ROOT=pathlib.Path(__file__).parent; work=ROOT/'work'
item=json.loads((work/'selected.json').read_text(encoding='utf-8'))
scenes=[('YOU WON’T BELIEVE THIS','This sounds fake, but it is real.'),('THE FACT',item['fact']),('WHY?',item['detail']),('THE PAYOFF','Nature is more bizarre than fiction.'),('FOLLOW FOR MORE','Another fact tomorrow.')]
d=work/'scenes'; d.mkdir(parents=True,exist_ok=True)
def wrap(s,n=25):
 words=s.split(); lines=[]; line=''
 for w in words:
  if line and len(line)+1+len(w)>n: lines.append(line); line=w
  else: line=(line+' '+w).strip()
 if line: lines.append(line)
 return lines[:7]
for i,(title,text) in enumerate(scenes):
 spans=''.join(f'<tspan x="540" dy="72">{html.escape(x)}</tspan>' for x in wrap(text))
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#101827"/><stop offset="1" stop-color="#35136b"/></linearGradient></defs><rect width="1080" height="1920" fill="url(#g)"/><circle cx="850" cy="250" r="180" fill="white" opacity=".06"/><circle cx="160" cy="1640" r="260" fill="white" opacity=".05"/><text x="540" y="560" text-anchor="middle" fill="white" font-family="Arial" font-size="64" font-weight="700">{html.escape(title)}</text><text x="540" y="760" text-anchor="middle" fill="white" font-family="Arial" font-size="54" font-weight="700">{spans}</text><text x="540" y="1770" text-anchor="middle" fill="white" opacity=".7" font-family="Arial" font-size="32">VIRAL FACTS</text></svg>'''
 (d/f'scene_{i:02d}.svg').write_text(svg,encoding='utf-8')
