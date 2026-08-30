import json, pathlib, urllib.parse, urllib.request, re
ROOT=pathlib.Path(__file__).parent; W=ROOT/'work'; W.mkdir(exist_ok=True); (W/'images').mkdir(exist_ok=True)
item=json.loads((W/'selected.json').read_text(encoding='utf-8'))
q=urllib.parse.urlencode({'action':'query','generator':'search','gsrsearch':item['query'],'gsrnamespace':6,'gsrlimit':12,'prop':'imageinfo','iiprop':'url','iiurlwidth':1200,'format':'json'})
url='https://commons.wikimedia.org/w/api.php?'+q
req=urllib.request.Request(url,headers={'User-Agent':'ViralFactsShorts/2.0'})
try:
 data=json.load(urllib.request.urlopen(req,timeout=25)); pages=data.get('query',{}).get('pages',{})
 urls=[]
 for p in pages.values():
  info=(p.get('imageinfo') or [{}])[0]; u=info.get('thumburl') or info.get('url')
  if u and re.search(r'\.(jpg|jpeg|png|webp)(\?|$)',u,re.I): urls.append(u)
 for i,u in enumerate(urls[:7]):
  try: urllib.request.urlretrieve(u,W/'images'/f'{i:02d}.jpg')
  except Exception as e: print('image failed',e)
except Exception as e: print('visual lookup failed',e)
if not list((W/'images').glob('*.jpg')):
 (W/'fallback.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#35106b"/></linearGradient></defs><rect width="1080" height="1920" fill="url(#g)"/><circle cx="850" cy="350" r="250" fill="white" opacity=".08"/><circle cx="160" cy="1550" r="350" fill="white" opacity=".05"/></svg>')
