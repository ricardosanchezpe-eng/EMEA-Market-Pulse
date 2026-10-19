import json,urllib.request,urllib.parse,time,math,datetime,pathlib,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from source_registry import EUROSTAT,WORLD_BANK
P=pathlib.Path('public/data/market-pulse.json');C=pathlib.Path('public/data/indicator-contracts.json')
UA={'User-Agent':'EMEA-Market-Pulse/2.18','Accept':'application/json'};LOCK=threading.Lock()
FIELD={'Overall':'overall','Transportation':'transport','Site Development':'site','Waste & Water':'water','Oil & Gas':'oil','Mining':'mining','Renewables':'renewables','Agriculture':'agriculture'}
def log(x):
 with LOCK: print(x,flush=True)
def fetch(url,tries=2):
 last=None
 for n in range(tries):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=35) as r:return json.load(r)
  except Exception as e:last=e;time.sleep(1.5*(n+1))
 raise last
def euro(ds,geo):
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});return fetch(u),u
def unpack(j,filters=None):
 ids=j.get('id',[]);sizes=j.get('size',[]);dim=j.get('dimension',{});cats=[[k for k,v in sorted(dim[x]['category']['index'].items(),key=lambda q:q[1])] for x in ids];g={}
 for k,v in j.get('value',{}).items():
  if not isinstance(v,(int,float)) or not math.isfinite(v):continue
  n=int(k);co=[]
  for z in reversed(sizes):co.append(n%z);n//=z
  co=co[::-1];codes={ids[i]:cats[i][co[i]] for i in range(len(ids))}
  if filters and any(codes.get(a)!=b for a,b in filters.items()):continue
  key=tuple((a,codes[a]) for a in ids if a!='time');g.setdefault(key,[]).append((codes.get('time'),v))
 choices=[]
 for key,a in g.items():
  a=sorted(a)
  if len(a)>=2:choices.append((len(a),key,a))
 return max(choices,key=lambda x:x[0])[1:] if choices else (None,[])
def metric(a,freq):
 if len(a)<2:return None
 lag=12 if freq=='monthly' and len(a)>=13 else 1
 if len(a)<=lag:return None
 date,cur=a[-1];pdate,prev=a[-lag-1]
 if prev in (None,0):return None
 if freq=='monthly_balance':growth=cur-prev;score=round(max(0,min(100,50+cur*2)))
 else:
  growth=(cur/prev-1)*100
  if not math.isfinite(growth) or abs(growth)>200:return None
  score=round(max(0,min(100,50+growth*4)))
 return {'raw':cur,'date':date,'previous':prev,'previousDate':pdate,'growthPct':growth,'score':score}
def wb(code,ind):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{ind}?format=json&per_page=70';j=fetch(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];a=[(x['date'],x['value']) for x in reversed(rows) if isinstance(x.get('value'),(int,float))];return metric(a,'annual'),u
def add(c,key,z,url,state,meta=None):
 c['sourceStatus'][key]={'adapterState':state,'retrieval':'live' if z else 'no_usable_series'}
 if z:c['indicators'][key]={**z,'url':url,'status':'live','adapterState':state,'metadata':meta or {}}
def process(src,contracts):
 c=json.loads(json.dumps(src));c.setdefault('indicators',{});c['sourceStatus']={};errors=[];cache={}
 for key,conf in EUROSTAT.items():
  try:
   ds=conf['dataset']
   if ds not in cache:cache[ds]=euro(ds,c['geo'])
   j,u=cache[ds];meta,a=unpack(j,conf.get('filters'));add(c,key,metric(a,conf['frequency']),u,conf['status'],dict(meta or []))
  except Exception as e:c['sourceStatus'][key]={'adapterState':conf['status'],'retrieval':'error','error':type(e).__name__};errors.append(key+':'+type(e).__name__)
 for key,ind in WORLD_BANK.items():
  try:z,u=wb(c.get('wb') or c['geo'],ind);add(c,key,z,u,'connected')
  except Exception as e:c['sourceStatus'][key]={'adapterState':'connected','retrieval':'error','error':type(e).__name__};errors.append(key+':'+type(e).__name__)
 # Prefer Eurostat water stress where it works; otherwise retain World Bank key expected by contracts.
 if c['indicators'].get('water_stress_eu'):c['indicators']['water_stress']=c['indicators']['water_stress_eu'];c['sourceStatus']['water_stress']=c['sourceStatus']['water_stress_eu']
 c.setdefault('coverage',{});c.setdefault('confidence',{})
 for vertical,items in contracts.items():
  vals=[]
  for item in items:
   z=c['indicators'].get(item['key'])
   if z and z.get('score') is not None:vals.append((z['score'],item['weight']))
  cov=sum(w for _,w in vals);field=FIELD[vertical]
  c[field]=round(sum(s*w for s,w in vals)/cov) if cov>=15 else None;c['coverage'][field]=cov;c['confidence'][field]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
 c['stale']=bool(errors)
 return c,{'country':c['country'],'coverage':c['coverage'],'sourceStatus':c['sourceStatus'],'errors':errors}
def main():
 d=json.loads(P.read_text());contracts=json.loads(C.read_text());countries=d.get('europe',[])+d.get('emea',[]);out={};diag=[];log(f'[START] country-by-country audit: {len(countries)} countries, {sum(map(len,contracts.values()))} indicator contracts')
 with ThreadPoolExecutor(max_workers=8) as ex:
  fs={ex.submit(process,c,contracts):c['country'] for c in countries}
  for i,f in enumerate(as_completed(fs),1):
   name=fs[f]
   try:c,x=f.result();out[name]=c;diag.append(x);live=sum(v.get('retrieval')=='live' for v in x['sourceStatus'].values());log(f'[{i}/{len(countries)}] {name}: {live} live adapters, {len(x["errors"])} errors')
   except Exception as e:diag.append({'country':name,'errors':['fatal:'+repr(e)]});log(f'[{i}/{len(countries)}] {name}: fatal')
 for u in ('europe','emea'):d[u]=[out.get(c['country'],c) for c in d.get(u,[])]
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']='v2.18 contract-driven refresh: every country is audited against every indicator contract; values publish only from usable validated series.';d['diagnostics']=diag
 P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/coverage-audit.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2));log('[DONE]')
if __name__=='__main__':main()
