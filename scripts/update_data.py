import json,urllib.request,urllib.parse,urllib.error,time,math,datetime,pathlib
P=pathlib.Path('public/data/market-pulse.json')
UA={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-GitHubActions/2.11','Accept':'application/json'}
WB={'water_stress':'ER.H2O.FWST.ZS','water_access':'SH.H2O.SMDW.ZS','renewable_share':'EG.FEC.RNEW.ZS','renewable_power':'EG.ELC.RNEW.ZS','agri_growth':'NV.AGR.TOTL.KD.ZG','agri_share':'NV.AGR.TOTL.ZS','oil_rents':'NY.GDP.PETR.RT.ZS','gas_rents':'NY.GDP.NGAS.RT.ZS','mineral_rents':'NY.GDP.MINR.RT.ZS','resource_rents':'NY.GDP.TOTL.RT.ZS'}
VERT={'overall':'Overall','transport':'Transportation','site':'Site Development','water':'Waste & Water','oil':'Oil & Gas','mining':'Mining','renewables':'Renewables','agriculture':'Agriculture'}
def get(url,tries=4):
 for n in range(tries):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120) as r:return json.load(r)
  except Exception:
   if n==tries-1:raise
   time.sleep(3*(n+1))
def euro(ds,geo):return get('https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'}))
def cube_series(j,required=None):
 ids=j.get('id',[]);sizes=j.get('size',[]);dims=j.get('dimension',{});cats=[]
 for x in ids:cats.append([k for k,v in sorted(dims[x]['category']['index'].items(),key=lambda z:z[1])])
 groups={}
 for k,v in j.get('value',{}).items():
  if not isinstance(v,(int,float)) or not math.isfinite(v):continue
  n=int(k);coords=[]
  for size in reversed(sizes):coords.append(n%size);n//=size
  coords=coords[::-1];codes={ids[i]:cats[i][coords[i]] for i in range(len(ids))}
  if required and any(codes.get(a)!=b for a,b in required.items()):continue
  key=tuple((a,codes[a]) for a in ids if a!='time');groups.setdefault(key,[]).append((codes.get('time'),v))
 series=[]
 for a in groups.values():
  b=sorted(a);vals=[v for _,v in b];
  if len(vals)>=2:series.append((b,vals))
 return max(series,key=lambda x:len(x[1])) if series else ([],[])
def momentum(points,monthly=False):
 if not points:return None
 vals=[v for _,v in points];lag=12 if monthly and len(vals)>=13 else 1
 if len(vals)<=lag or vals[-lag-1] in (None,0):return None
 current,previous=vals[-1],vals[-lag-1];growth=(current/previous-1)*100
 if not math.isfinite(growth) or abs(growth)>100:return None
 return {'raw':current,'previous':previous,'growthPct':growth,'date':points[-1][0],'score':round(max(0,min(100,50+growth*4)))}
def wb(code,indicator):
 u=f'https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=70';j=get(u);rows=j[1] if isinstance(j,list) and len(j)>1 else [];pts=[(x['date'],x['value']) for x in reversed(rows) if isinstance(x.get('value'),(int,float))];return momentum(pts),u
def weighted(c,keys,minimum=.15):
 live=[]
 for key,w in keys:
  z=c['indicators'].get(key)
  if z and z.get('score') is not None:live.append((z['score'],w))
 cov=sum(w for _,w in live)
 return (round(sum(s*w for s,w in live)/cov) if cov>=minimum else None,round(cov*100))
def add(c,key,z,url,status='live'):
 if z:c['indicators'][key]={**z,'url':url,'status':status}
def main():
 d=json.loads(P.read_text());logs=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for c in d['europe']:
  c.setdefault('indicators',{});errs=[]
  try:
   j=euro('sts_copr_m',c['geo']);u='https://ec.europa.eu/eurostat/databrowser/view/sts_copr_m/default/table'
   for key,nace in [('construction_production','F'),('building_output','F41'),('civil_output','F42')]:
    pts,_=cube_series(j,{'nace_r2':nace});add(c,key,momentum(pts,True),u)
  except Exception as e:errs.append('construction '+repr(e))
  for key,ds in [('building_permits','teiis550'),('rail_freight','rail_go_typepas'),('road_freight','road_go_ta_tott'),('port_freight','mar_m_go_qm_cwhd')]:
   try:
    j=euro(ds,c['geo']);pts,_=cube_series(j);add(c,key,momentum(pts,False),'https://ec.europa.eu/eurostat/databrowser/view/'+ds+'/default/table')
   except Exception as e:errs.append(key+' '+repr(e))
  for key,ind in WB.items():
   try:z,u=wb(c.get('wb') or c.get('geo'),ind);add(c,key,z,u)
   except Exception as e:errs.append(key+' '+repr(e))
  models={
   'overall':[('construction_production',.25),('civil_output',.20),('building_permits',.15),('building_output',.20)],
   'transport':[('civil_output',.25),('rail_freight',.15),('road_freight',.10),('port_freight',.10)],
   'site':[('building_permits',.50),('building_output',.20)],
   'water':[('water_stress',.25),('water_access',.25)],
   'oil':[('oil_rents',.35),('gas_rents',.35),('resource_rents',.15)],
   'mining':[('mineral_rents',.50),('resource_rents',.20)],
   'renewables':[('renewable_share',.40),('renewable_power',.35)],
   'agriculture':[('agri_growth',.35),('agri_share',.25),('water_stress',.15)]}
  c.setdefault('coverage',{});c.setdefault('confidence',{})
  for field,keys in models.items():
   c[field],cov=weighted(c,keys);c['coverage'][field]=cov;c['confidence'][field]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
  c['stale']=bool(errs);logs.append({'country':c['country'],'coverage':c['coverage'],'errors':errs})
 d['generatedAt']=now;d['pipelineStatus']='Multi-source refresh complete. Scores use available validated indicators reweighted to observed coverage; confidence exposes remaining gaps.';d['diagnostics']=logs;P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/refresh-diagnostics.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
