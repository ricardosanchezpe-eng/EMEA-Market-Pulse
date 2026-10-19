import json,urllib.request,urllib.parse,urllib.error,time,math,datetime,pathlib
P=pathlib.Path('public/data/market-pulse.json')
UA={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-GitHubActions/2.13','Accept':'application/json'}
WB={'water_stress':'ER.H2O.FWST.ZS','water_access':'SH.H2O.SMDW.ZS','renewable_share':'EG.FEC.RNEW.ZS','renewable_power':'EG.ELC.RNEW.ZS','agri_growth':'NV.AGR.TOTL.KD.ZG','agri_share':'NV.AGR.TOTL.ZS','oil_rents':'NY.GDP.PETR.RT.ZS','gas_rents':'NY.GDP.NGAS.RT.ZS','mineral_rents':'NY.GDP.MINR.RT.ZS','resource_rents':'NY.GDP.TOTL.RT.ZS'}
EURO={'construction':'sts_copr_m','permits':'teiis550','rail':'rail_go_typepas','road':'road_go_ta_tott','maritime':'mar_go_qm','confidence':'ei_bsbu_m_r2'}
def get(url,tries=4):
 for n in range(tries):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120) as r:return json.load(r)
  except Exception:
   if n==tries-1:raise
   time.sleep(3*(n+1))
def euro(ds,geo):
 url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});return get(url),url
def decode(j,filters=None):
 ids=j.get('id',[]);sizes=j.get('size',[]);dims=j.get('dimension',{});cats=[]
 for x in ids:cats.append([k for k,v in sorted(dims[x]['category']['index'].items(),key=lambda z:z[1])])
 groups={}
 for k,v in j.get('value',{}).items():
  if not isinstance(v,(int,float)) or not math.isfinite(v):continue
  n=int(k);coords=[]
  for size in reversed(sizes):coords.append(n%size);n//=size
  coords=coords[::-1];codes={ids[i]:cats[i][coords[i]] for i in range(len(ids))}
  if filters and any(codes.get(a)!=b for a,b in filters.items()):continue
  key=tuple((a,codes[a]) for a in ids if a!='time');groups.setdefault(key,[]).append((codes.get('time'),v,codes))
 choices=[]
 for key,a in groups.items():
  a=sorted(a,key=lambda x:x[0]);
  if len(a)>=2:choices.append((key,a))
 return max(choices,key=lambda x:len(x[1])) if choices else (None,[])
def detail(a,monthly=False,confidence=False):
 if not a:return None
 vals=[x[1] for x in a];dates=[x[0] for x in a]
 if confidence:
  current=vals[-1];previous=vals[-2] if len(vals)>1 else None;growth=current-previous if previous is not None else None;score=round(max(0,min(100,50+current*2)))
 else:
  lag=12 if monthly and len(vals)>=13 else 1
  if len(vals)<=lag or vals[-lag-1] in (0,None):return None
  current,previous=vals[-1],vals[-lag-1];growth=(current/previous-1)*100
  if not math.isfinite(growth) or abs(growth)>150:return None
  score=round(max(0,min(100,50+growth*4)))
 return {'raw':current,'previous':previous,'growthPct':growth,'date':dates[-1],'score':score}
def wb(code,indicator):
 url=f'https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=70';j=get(url);rows=j[1] if isinstance(j,list) and len(j)>1 else [];a=[(x['date'],x['value'],{}) for x in reversed(rows) if isinstance(x.get('value'),(int,float))];return detail(a),url
def add(c,key,z,url,meta=None):
 if z:c['indicators'][key]={**z,'url':url,'status':'live','metadata':meta or {}}
def weighted(c,items,mincov=.15):
 live=[(c['indicators'][k]['score'],w) for k,w in items if k in c['indicators'] and c['indicators'][k].get('score') is not None];cov=sum(w for _,w in live);return (round(sum(s*w for s,w in live)/cov) if cov>=mincov else None,round(cov*100))
def main():
 d=json.loads(P.read_text());logs=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for c in d.get('europe',[])+d.get('emea',[]):
  c.setdefault('indicators',{});errs=[]
  # Eurostat direct adapters
  tests=[('construction',{'nace_r2':'F'},'construction_production',True,False),('construction',{'nace_r2':'F41'},'building_output',True,False),('construction',{'nace_r2':'F42'},'civil_output',True,False),('permits',None,'building_permits',True,False),('rail',None,'rail_freight',False,False),('road',None,'road_freight',False,False),('maritime',None,'port_freight',False,False),('confidence',None,'construction_confidence',True,True)]
  cache={}
  for source,filters,key,monthly,conf in tests:
   try:
    if source not in cache:cache[source]=euro(EURO[source],c['geo'])
    j,url=cache[source];series_key,a=decode(j,filters);add(c,key,detail(a,monthly,conf),url,dict(series_key or []))
   except Exception as e:errs.append(key+': '+repr(e))
  for key,ind in WB.items():
   try:z,url=wb(c.get('wb') or c.get('geo'),ind);add(c,key,z,url)
   except Exception as e:errs.append(key+': '+repr(e))
  models={'overall':[('construction_production',.25),('civil_output',.20),('building_permits',.15),('construction_confidence',.15),('building_output',.20)],'transport':[('civil_output',.25),('rail_freight',.15),('road_freight',.10),('port_freight',.10),('construction_confidence',.10)],'site':[('building_permits',.50),('building_output',.20),('construction_confidence',.10)],'water':[('water_stress',.15),('water_access',.15)],'oil':[('oil_rents',.20),('gas_rents',.15),('resource_rents',.10)],'mining':[('mineral_rents',.20),('resource_rents',.10)],'renewables':[('renewable_share',.20),('renewable_power',.15)],'agriculture':[('agri_growth',.20),('agri_share',.15),('water_stress',.10)]}
  c.setdefault('coverage',{});c.setdefault('confidence',{})
  for field,items in models.items():
   c[field],cov=weighted(c,items);c['coverage'][field]=cov;c['confidence'][field]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
  c['stale']=bool(errs);logs.append({'country':c['country'],'coverage':c['coverage'],'liveIndicators':sorted(c['indicators']),'errors':errs})
 d['generatedAt']=now;d['pipelineStatus']='Verified multi-source refresh: Eurostat construction, permits, rail, road, maritime and confidence plus World Bank sector indicators. Scores reweight validated available inputs; coverage and confidence expose remaining gaps.';d['diagnostics']=logs;P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/refresh-diagnostics.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
