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
def yoy_detail(a):
 if len(a)<13 or not a[-13]:return (None,None,None,None)
 latest=a[-1];previous=a[-13];growth=(latest/previous-1)*100
 if not math.isfinite(growth) or abs(growth)>80:return (None,latest,previous,growth)
 score=round(max(0,min(100,50+4*growth)))
 return (score,latest,previous,growth)
def yoy_index(a):
 return yoy_detail(a)[0]
def wb_series(code,indicator):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=70'
 j=read_json(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];return [(x.get('date'),x.get('value')) for x in rows if isinstance(x.get('value'),(int,float))],u
def wb_detail(rows,scale=3,level=False):
 if not rows:return None,None,None,None,None
 latest_date,latest=rows[0];previous_row=next(((d,v) for d,v in rows[1:] if v is not None),None)
 previous_date,previous=previous_row if previous_row else (None,None)
 change=(latest-previous) if previous is not None else None
 growth=((latest/previous)-1)*100 if previous not in (None,0) else None
 score=round(max(0,min(100,latest))) if level else (round(max(0,min(100,50+scale*change))) if change is not None else None)
 return score,latest,previous,growth,latest_date
def wb_change(rows,scale=3,level=False):
 score,latest,previous,growth,date=wb_detail(rows,scale,level);return score,latest,date
