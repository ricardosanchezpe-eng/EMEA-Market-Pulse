import json,urllib.request,urllib.parse,urllib.error,time,math
UA={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-GitHubActions/2.8','Accept':'application/json'}
def read_json(url,tries=4):
 for n in range(tries):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120) as r:return json.load(r)
  except Exception:
   if n==tries-1:raise
   time.sleep(3*(n+1))
def eurostat_cube(geo):
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_copr_m?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});return read_json(u),u
def decode_nace(j,nace):
 ids=j['id'];sizes=j['size'];dims=j['dimension'];cats=[[k for k,v in sorted(dims[x]['category']['index'].items(),key=lambda z:z[1])] for x in ids];groups={}
 for k,v in j.get('value',{}).items():
  n=int(k);coords=[]
  for s in reversed(sizes):coords.append(n%s);n//=s
  codes=[cats[i][coords[::-1][i]] for i in range(len(ids))]
  if 'nace_r2' in ids and codes[ids.index('nace_r2')]!=nace:continue
  key=tuple(codes[i] for i,x in enumerate(ids) if x!='time');groups.setdefault(key,[]).append((codes[ids.index('time')],v))
 use=[]
 for x in groups.values():
  a=[v for _,v in sorted(x) if isinstance(v,(int,float)) and math.isfinite(v)]
  if len(a)>=13:use.append(a)
 return max(use,key=len) if use else []
def yoy_index(a):
 if len(a)<13 or not a[-13]:return None
 g=(a[-1]/a[-13]-1)*100
 return None if not math.isfinite(g) or abs(g)>80 else round(max(0,min(100,50+4*g)))
def wb_series(code,indicator):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=70'
 j=read_json(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];return [(x.get('date'),x.get('value')) for x in rows if isinstance(x.get('value'),(int,float))],u
def wb_change(rows,scale=3,level=False):
 if not rows:return None,None,None
 vals=[v for _,v in rows];latest=vals[0];date=rows[0][0]
 if level:return round(max(0,min(100,latest))),latest,date
 prior=next((v for v in vals[1:] if v is not None),None)
 if prior is None:return None,latest,date
 diff=latest-prior
 return round(max(0,min(100,50+scale*diff))),latest,date
