import json,urllib.request,urllib.parse,time,math,datetime,pathlib,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from source_registry import EUROSTAT,WORLD_BANK
P=pathlib.Path('public/data/market-pulse.json'); C=pathlib.Path('public/data/indicator-contracts.json'); UA={'User-Agent':'EMEA-Market-Pulse/2.21.1','Accept':'application/json'};LOCK=threading.Lock()
FIELD={'Overall':'overall','Transportation':'transport','Site Development':'site','Waste & Water':'water','Oil & Gas':'oil','Mining':'mining','Renewables':'renewables','Agriculture':'agriculture'}
def log(s):
 with LOCK:print(s,flush=True)
def fetch(url):
 last=None
 for i in range(2):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=35) as r:return json.load(r)
  except Exception as e:last=e;time.sleep(1.5*(i+1))
 raise last
def euro(ds,geo,gd='geo',filters=None):
 q={'lang':'EN',gd:geo,'lastTimePeriod':'25'}
 # Push known dimensions into the API request. This avoids downloading very large cubes
 # such as gov_10a_exp and prevents HTTP 413 while keeping local series validation.
 for k,v in (filters or {}).items():
  if v is not None:q[k]=v
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode(q);return fetch(u),u
def candidates(j,filters=None):
 ids=j.get('id',[]);sizes=j.get('size',[]);dim=j.get('dimension',{});cats=[[k for k,v in sorted(dim[x]['category']['index'].items(),key=lambda q:q[1])] for x in ids];g={}
 for k,v in j.get('value',{}).items():
  if not isinstance(v,(int,float)) or not math.isfinite(v):continue
  n=int(k);co=[]
  for z in reversed(sizes):co.append(n%z);n//=z
  co=co[::-1];codes={ids[i]:cats[i][co[i]] for i in range(len(ids))}
  if filters and any(codes.get(a)!=b for a,b in filters.items()):continue
  key=tuple((a,codes[a]) for a in ids if a!='time');g.setdefault(key,[]).append((codes.get('time'),v))
 out=[]
 for key,a in g.items():
  a=sorted(a)
  if len(a)>=2:out.append((key,a))
 return out
def choose(j,conf):
 cs=candidates(j,conf.get('filters'))
 if not cs:return None,[]
 cs.sort(key=lambda x:(x[1][-1][0] or '',len(x[1])),reverse=True);return cs[0]
def calc(a,conf):
 if len(a)<2:return None
 mode=conf.get('comparison','previous');freq=conf.get('frequency','annual');lag=1
 if mode=='yoy' and freq=='monthly' and len(a)>=13:lag=12
 elif mode=='yoy_if_possible' and freq=='quarterly' and len(a)>=5:lag=4
 if len(a)<=lag:return None
 date,cur=a[-1];pdate,prev=a[-lag-1]
 if prev in (None,0):return {'raw':cur,'date':date,'previous':None,'previousDate':None,'growthPct':None,'score':None,'comparison':mode,'signal':conf.get('signal','direct')}
 if freq=='monthly_balance':growth=cur-prev;score=round(max(0,min(100,50+cur*2)))
 else:
  growth=(cur/prev-1)*100
  if not math.isfinite(growth) or abs(growth)>250:return None
  score=round(max(0,min(100,50+growth*4)))
 return {'raw':cur,'date':date,'previous':prev,'previousDate':pdate,'growthPct':growth,'score':score,'comparison':mode,'signal':conf.get('signal','direct')}
def wb(code,ind):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{ind}?format=json&per_page=70';j=fetch(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];a=[(x['date'],x['value']) for x in reversed(rows) if isinstance(x.get('value'),(int,float))];return calc(a,{'comparison':'previous','frequency':'annual','signal':'context'}),u
def store(c,k,z,u,state,meta=None):
 c['sourceStatus'][k]={'adapterState':state,'retrieval':'live' if z and z.get('score') is not None else 'no_usable_series'}
 if z:c['indicators'][k]={**z,'url':u,'status':'live' if z.get('score') is not None else 'no_comparator','adapterState':state,'metadata':meta or {}}
def process(src,contracts,europe):
 c=json.loads(json.dumps(src));c.setdefault('indicators',{});c['sourceStatus']={};errors=[];cache={}
 if europe:
  for k,conf in EUROSTAT.items():
   attempts=[conf['dataset']]+conf.get('fallbacks',[]);chosen=None;last_error=None
   for ds in attempts:
    try:
     ck=(ds,conf.get('geo_dimension','geo'))
     if ck not in cache:cache[ck]=euro(ds,c['geo'],conf.get('geo_dimension','geo'),conf.get('filters'))
     j,u=cache[ck];meta,a=choose(j,conf);z=calc(a,conf)
     if z and z.get('raw') is not None:chosen=(z,u,meta,ds);break
    except Exception as e:last_error=e
   if chosen:
    z,u,meta,ds=chosen;z['dataset']=ds;store(c,k,z,u,conf['status'],dict(meta or []))
   else:
    reason='retrieval_error' if last_error else 'not_reported_or_no_comparable_series'
    c['sourceStatus'][k]={'adapterState':conf['status'],'retrieval':'no_usable_series','reason':reason,'datasetsTried':attempts}
    if last_error:errors.append(k+':'+type(last_error).__name__)
 # World Bank is queried for both universes. In Europe it is the fallback/context layer;
 # in Broader EMEA it is the primary harmonised international layer.
 for k,ind in WORLD_BANK.items():
  try:
   z,u=wb(c.get('wb') or c['geo'],ind)
   if z:store(c,k,z,u,'connected')
   else:c['sourceStatus'][k]={'adapterState':'connected','retrieval':'no_usable_series','reason':'not_reported_or_no_comparable_series','indicatorCode':ind}
  except Exception as e:
   c['sourceStatus'][k]={'adapterState':'connected','retrieval':'error','reason':'retrieval_error','error':type(e).__name__,'indicatorCode':ind};errors.append(k+':'+type(e).__name__)
 if c['indicators'].get('water_stress_eu'):
  c['indicators']['water_stress']=c['indicators']['water_stress_eu'];c['sourceStatus']['water_stress']=c['sourceStatus']['water_stress_eu']
 c.setdefault('coverage',{});c.setdefault('confidence',{})
 for vertical,items in contracts.items():
  vals=[(c['indicators'][x['key']]['score'],x['weight']) for x in items if c['indicators'].get(x['key'],{}).get('score') is not None];cov=sum(w for _,w in vals);field=FIELD[vertical];c[field]=round(sum(sc*w for sc,w in vals)/cov) if cov>=15 else None;c['coverage'][field]=cov;c['confidence'][field]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
 c['stale']=bool(errors);return c,{'country':c['country'],'universe':'Europe' if europe else 'Broader EMEA','coverage':c['coverage'],'sourceStatus':c['sourceStatus'],'errors':errors}

def main():
 import subprocess,sys
 subprocess.check_call([sys.executable,str(pathlib.Path(__file__).with_name('ensure_country_universe.py'))])
 d=json.loads(P.read_text());contracts=json.loads(C.read_text());jobs=[(c,True) for c in d.get('europe',[])]+[(c,False) for c in d.get('emea',[])];out={};diag=[];log(f'[START] {len(jobs)} countries')
 with ThreadPoolExecutor(max_workers=8) as ex:
  fs={ex.submit(process,c,contracts,eu):(c['country'],eu) for c,eu in jobs}
  for i,f in enumerate(as_completed(fs),1):
   name,eu=fs[f]
   try:c,x=f.result();out[(name,eu)]=c;diag.append(x);log(f'[{i}/{len(jobs)}] {name}: {sum(v.get("retrieval")=="live" for v in x["sourceStatus"].values())} live')
   except Exception as e:diag.append({'country':name,'errors':['fatal:'+repr(e)]});log(f'[{i}/{len(jobs)}] {name}: fatal')
 d['europe']=[out.get((c['country'],True),c) for c in d.get('europe',[])];d['emea']=[out.get((c['country'],False),c) for c in d.get('emea',[])];d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']='v2.21.1 verified all-country adapter refresh with Eurostat monthly/quarterly fallbacks and explicit missing-data reasons.';d['diagnostics']=diag;P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/coverage-audit.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2));log('[DONE]')
if __name__=='__main__':main()
