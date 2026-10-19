import json, urllib.parse, urllib.request, urllib.error, datetime, pathlib, math, time
P=pathlib.Path('public/data/market-pulse.json')
API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
HEADERS={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse/2.2','Accept':'application/json'}
def fetch(dataset,params):
 url=API+dataset+'?'+urllib.parse.urlencode({'format':'JSON','lang':'EN','lastTimePeriod':'25',**params})
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=90) as r:return json.load(r),url
def vals(j):
 v=j.get('value',{});return [x for _,x in sorted((int(k),x) for k,x in v.items()) if isinstance(x,(int,float)) and math.isfinite(x)]
def yoy_score(a):
 if len(a)<13:return None
 previous=a[-13]
 if previous in (0,None):return None
 g=(a[-1]/previous-1)*100
 if not math.isfinite(g) or abs(g)>80:return None
 return round(max(0,min(100,50+g*4)))
def latest_score(a,neutral=0,scale=2):
 if not a:return None
 x=a[-1]
 if not math.isfinite(x):return None
 return round(max(0,min(100,50+(x-neutral)*scale)))
def series(dataset,geo,**dims):
 try:
  j,u=fetch(dataset,{'geo':geo,**dims});return vals(j),u
 except Exception as e:
  print(dataset,geo,type(e).__name__,e);return [],None
def weighted(parts,minimum=.45):
 valid=[(s,w) for s,w in parts if s is not None]
 coverage=sum(w for _,w in valid)
 if coverage<minimum:return None,round(coverage*100)
 return round(sum(s*w for s,w in valid)/coverage),round(coverage*100)
def main():
 d=json.loads(P.read_text(encoding='utf-8'));success=0;urls=set()
 for r in d['europe']:
  geo=r['geo'];
  con,u=series('sts_copr_m',geo,freq='M',indic_bt='PRD',nace_r2='F',s_adj='SCA',unit='I21'); urls.add(u) if u else None
  civ,u=series('sts_copr_m',geo,freq='M',indic_bt='PRD',nace_r2='F42',s_adj='SCA',unit='I21'); urls.add(u) if u else None
  bld,u=series('sts_copr_m',geo,freq='M',indic_bt='PRD',nace_r2='F41',s_adj='SCA',unit='I21'); urls.add(u) if u else None
  conf,u=series('ei_bsbu_m_r2',geo,freq='M'); urls.add(u) if u else None
  permit,u=series('teiis550',geo); urls.add(u) if u else None
  s_con,s_civ,s_bld,s_conf,s_perm=yoy_score(con),yoy_score(civ),yoy_score(bld),latest_score(conf),yoy_score(permit)
  overall,cov=weighted([(s_con,.35),(s_civ,.20),(s_bld,.15),(s_conf,.15),(s_perm,.15)])
  transport,tcov=weighted([(s_civ,.80),(s_conf,.20)],.60)
  site,scov=weighted([(s_bld,.50),(s_perm,.35),(s_conf,.15)],.50)
  r['overall']=overall;r['transport']=transport;r['site']=site;r['coverage']=cov
  r['confidence']='High' if cov>=80 else 'Medium' if cov>=55 else 'Low' if overall is not None else 'Insufficient'
  r['sourceStatus']={'construction':s_con,'civilEngineering':s_civ,'buildings':s_bld,'confidence':s_conf,'permits':s_perm}
  if overall is not None:success+=1
  time.sleep(.15)
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 d['pipelineStatus']=f'Validated public-source scores refreshed for {success} European countries. Overall, Transportation and Site Development use live Eurostat series; other verticals remain insufficient until their official adapters are connected.'
 d['sourceUrls']=[u for u in urls if u]
 P.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 print(d['pipelineStatus'])
if __name__=='__main__':main()
