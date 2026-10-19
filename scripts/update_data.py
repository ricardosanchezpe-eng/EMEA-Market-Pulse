import json,urllib.request,urllib.parse,time,math,datetime,pathlib,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
P=pathlib.Path('public/data/market-pulse.json');LOCK=threading.Lock()
UA={'User-Agent':'EMEA-Market-Pulse/2.16','Accept':'application/json'}
EU={'construction':'sts_copr_m','permits':'teiis550','rail':'rail_go_typepas','road':'road_go_ta_tott','maritime':'mar_go_qm','confidence':'ei_bsbu_m_r2'}
WB={'water_stress':'ER.H2O.FWST.ZS','water_access':'SH.H2O.SMDW.ZS','renewable_share':'EG.FEC.RNEW.ZS','renewable_power':'EG.ELC.RNEW.ZS','agri_growth':'NV.AGR.TOTL.KD.ZG','agri_share':'NV.AGR.TOTL.ZS','oil_rents':'NY.GDP.PETR.RT.ZS','gas_rents':'NY.GDP.NGAS.RT.ZS','mineral_rents':'NY.GDP.MINR.RT.ZS','resource_rents':'NY.GDP.TOTL.RT.ZS'}
def say(x):
 with LOCK: print(x,flush=True)
def fetch(url):
 err=None
 for attempt in range(2):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30) as r:return json.load(r)
  except Exception as e:
   err=e
   if attempt==0:time.sleep(1.5)
 raise err
def euro(ds,geo):
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});return fetch(u),u
def series(j,filters=None):
 ids=j.get('id',[]);sizes=j.get('size',[]);dims=j.get('dimension',{});cats=[[k for k,v in sorted(dims[x]['category']['index'].items(),key=lambda q:q[1])] for x in ids];g={}
 for k,v in j.get('value',{}).items():
  if not isinstance(v,(int,float)) or not math.isfinite(v):continue
  n=int(k);co=[]
  for z in reversed(sizes):co.append(n%z);n//=z
  co=co[::-1];codes={ids[i]:cats[i][co[i]] for i in range(len(ids))}
  if filters and any(codes.get(a)!=b for a,b in filters.items()):continue
  key=tuple((a,codes[a]) for a in ids if a!='time');g.setdefault(key,[]).append((codes.get('time'),v))
 a=[sorted(x) for x in g.values() if len(x)>=2];return max(a,key=len) if a else []
def metric(a,monthly=False,confidence=False):
 if not a:return None
 lag=1 if confidence else (12 if monthly and len(a)>=13 else 1)
 if len(a)<=lag:return None
 date,cur=a[-1];pdate,prev=a[-lag-1]
 if confidence:chg=cur-prev;score=round(max(0,min(100,50+cur*2)))
 else:
  if prev==0:return None
  chg=(cur/prev-1)*100
  if not math.isfinite(chg) or abs(chg)>150:return None
  score=round(max(0,min(100,50+chg*4)))
 return {'raw':cur,'date':date,'previous':prev,'previousDate':pdate,'growthPct':chg,'score':score}
def wb(code,indicator):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=70';j=fetch(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];a=[(x['date'],x['value']) for x in reversed(rows) if isinstance(x.get('value'),(int,float))];return metric(a),u
def add(c,k,z,u):
 if z:c['indicators'][k]={**z,'url':u,'status':'live'}
def calc(c,items):
 a=[(c['indicators'][k]['score'],w) for k,w in items if c['indicators'].get(k,{}).get('score') is not None];cov=sum(w for _,w in a);return (round(sum(s*w for s,w in a)/cov) if cov>=.15 else None,round(cov*100))
def country(src):
 c=json.loads(json.dumps(src));c.setdefault('indicators',{});errors=[];checks=[];cache={}
 tests=[('construction',{'nace_r2':'F'},'construction_production',1,0),('construction',{'nace_r2':'F41'},'building_output',1,0),('construction',{'nace_r2':'F42'},'civil_output',1,0),('permits',None,'building_permits',1,0),('rail',None,'rail_freight',0,0),('road',None,'road_freight',0,0),('maritime',None,'port_freight',0,0),('confidence',None,'construction_confidence',1,1)]
 for srcname,flt,key,monthly,conf in tests:
  try:
   if srcname not in cache:cache[srcname]=euro(EU[srcname],c['geo'])
   j,u=cache[srcname];z=metric(series(j,flt),monthly,conf);add(c,key,z,u);checks.append(key)
  except Exception as e:errors.append(key+':'+type(e).__name__)
 for key,ind in WB.items():
  try:z,u=wb(c.get('wb') or c['geo'],ind);add(c,key,z,u);checks.append(key)
  except Exception as e:errors.append(key+':'+type(e).__name__)
 models={'overall':[('construction_production',.25),('civil_output',.20),('building_permits',.15),('construction_confidence',.15),('building_output',.20)],'transport':[('civil_output',.25),('rail_freight',.15),('road_freight',.10),('port_freight',.10),('construction_confidence',.10)],'site':[('building_permits',.50),('building_output',.20),('construction_confidence',.10)],'water':[('water_stress',.15),('water_access',.15)],'oil':[('oil_rents',.20),('gas_rents',.15),('resource_rents',.10)],'mining':[('mineral_rents',.20),('resource_rents',.10)],'renewables':[('renewable_share',.20),('renewable_power',.15)],'agriculture':[('agri_growth',.20),('agri_share',.15),('water_stress',.10)]}
 c.setdefault('coverage',{});c.setdefault('confidence',{})
 for f,it in models.items():
  c[f],cv=calc(c,it);c['coverage'][f]=cv;c['confidence'][f]='High' if cv>=75 else 'Medium' if cv>=50 else 'Low' if cv>=15 else 'Insufficient'
 c['stale']=bool(errors);return c,{'country':c['country'],'successfulChecks':checks,'errors':errors,'coverage':c['coverage']}
def main():
 d=json.loads(P.read_text());allc=d.get('europe',[])+d.get('emea',[]);say(f'[START] {len(allc)} countries; all 6 Eurostat and {len(WB)} World Bank sources retained')
 out={};diag=[]
 with ThreadPoolExecutor(max_workers=10) as ex:
  fs={ex.submit(country,c):c['country'] for c in allc}
  for i,f in enumerate(as_completed(fs),1):
   n=fs[f]
   try:c,x=f.result();out[n]=c;diag.append(x);say(f'[{i}/{len(allc)}] {n}: {len(x["successfulChecks"])} checked, {len(x["errors"])} errors')
   except Exception as e:diag.append({'country':n,'successfulChecks':[],'errors':['fatal:'+repr(e)]});say(f'[{i}/{len(allc)}] {n}: fatal')
 for u in ('europe','emea'):d[u]=[out.get(c['country'],c) for c in d.get(u,[])]
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']='Optimized parallel refresh; all configured sources retained, with bounded retries, progress logging and last-valid-data fallback.';d['diagnostics']=diag
 P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/refresh-diagnostics.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2));say('[DONE]')
if __name__=='__main__':main()
