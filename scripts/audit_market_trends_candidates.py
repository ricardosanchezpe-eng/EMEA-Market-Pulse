#!/usr/bin/env python3
import csv,datetime as dt,json,math,pathlib,statistics,sys,time,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]; CFG=json.load(open(ROOT/'config/market-trends-candidates.json'))
OUT=ROOT/'market-trends-audit-output';OUT.mkdir(exist_ok=True)
COUNTRIES={'AT':'Austria','BE':'Belgium','BG':'Bulgaria','CH':'Switzerland','CY':'Cyprus','CZ':'Czechia','DE':'Germany','DK':'Denmark','EE':'Estonia','ES':'Spain','FI':'Finland','FR':'France','GR':'Greece','HR':'Croatia','HU':'Hungary','IE':'Ireland','IT':'Italy','LT':'Lithuania','LU':'Luxembourg','LV':'Latvia','MT':'Malta','NL':'Netherlands','NO':'Norway','PL':'Poland','PT':'Portugal','RO':'Romania','SE':'Sweden','SI':'Slovenia','SK':'Slovakia'}
BASE='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
def fetch(dataset,geo):
 u=BASE+dataset+'?'+urllib.parse.urlencode({'geo':geo,'lang':'en','lastTimePeriod':40})
 req=urllib.request.Request(u,headers={'User-Agent':'EMEA-Market-Pulse-Trends-Audit/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:return json.load(r),u
def inv(cat):return {int(v):k for k,v in (cat or {}).get('index',{}).items()}
def series(j,terms):
 dims=j['id'];sizes=j['size'];T=dims.index('time');times=inv(j['dimension']['time']['category']);vals=j.get('value',{})
 cats={d:inv(j['dimension'][d]['category']) for d in dims}
 def decode(flat):
  coords=[]
  for sz in reversed(sizes):coords.append(flat%sz);flat//=sz
  return list(reversed(coords))
 groups={}
 for k,v in vals.items():
  try:v=float(v)
  except:continue
  c=decode(int(k)); meta=[]
  labels=[]
  for i,d in enumerate(dims):
   if d=='time':continue
   code=cats[d].get(c[i],str(c[i]));lab=j['dimension'][d]['category'].get('label',{}).get(code,code)
   meta.append((d,code,lab));labels.append(str(lab).lower())
  score=sum(any(t.lower() in lab for lab in labels) for t in terms)
  key=tuple((d,code) for d,code,_ in meta)
  groups.setdefault(key,{'score':score,'meta':meta,'obs':[]})['obs'].append((times.get(c[T],str(c[T])),v))
 if not groups:return None
 g=max(groups.values(),key=lambda x:(x['score'],len(x['obs']),max([d for d,_ in x['obs']] or [''])))
 g['obs']=sorted(g['obs'])
 return g
def period_ord(p):
 if '-Q' in p:return int(p[:4])*4+int(p[-1])
 if len(p)>=7 and p[4]=='-':return int(p[:4])*12+int(p[5:7])
 return int(p[:4])
def months_age(period):
 now=dt.date.today();y=int(period[:4]);m=int(period[5:7]) if len(period)>=7 and period[4]=='-' and 'Q' not in period else (int(period[-1])*3 if '-Q' in period else 12)
 return (now.year-y)*12+now.month-m
def expected_grid(obs,freq):
 if not obs:return []
 n=24 if freq=='monthly' else 8 if freq=='quarterly' else 6
 end=period_ord(obs[-1][0]);step=1
 vals={period_ord(d):{'period':d,'value':v} for d,v in obs}
 out=[]
 for x in range(end-n+1,end+1):out.append(vals.get(x,{'period':None,'value':None}))
 return out
def yoy(obs,freq):
 lag=12 if freq=='monthly' else 4 if freq=='quarterly' else 1
 if len(obs)<=lag:return None
 cur=obs[-1][1];prev=obs[-1-lag][1]
 return None if prev==0 else (cur/prev-1)*100
def matched_ytd(obs,freq):
 if freq not in ('monthly','quarterly'):return None,0,0
 vals={period_ord(d):v for d,v in obs};latest=period_ord(obs[-1][0]);lag=12 if freq=='monthly' else 4
 y=latest//lag;pos=latest%lag
 pairs=[(vals.get(y*lag+i),vals.get((y-1)*lag+i)) for i in range(pos+1)]
 pairs=[p for p in pairs if p[0] is not None and p[1] is not None]
 if not pairs:return None,0,pos+1
 a=sum(x for x,_ in pairs);b=sum(y for _,y in pairs)
 return (None if b==0 else (a/b-1)*100),len(pairs),pos+1
rows=[]
for c in CFG['candidates']:
 for geo,name in COUNTRIES.items():
  datasets=[c['dataset']]+([c['fallback']] if c.get('fallback') else [])
  result=None;errors=[]
  for ds in datasets:
   try:
    j,url=fetch(ds,geo);g=series(j,c.get('match',[]))
    if g and len(g['obs'])>=2:result=(ds,j,url,g);break
   except Exception as e:errors.append(f'{ds}:{type(e).__name__}:{e}')
   time.sleep(.05)
  r={'indicator':c['key'],'name':c['name'],'verticals':'; '.join(c['verticals']),'country':name,'geo':geo,'preferredFrequency':c['frequency'],'decisionSeed':c['decisionSeed'],'status':'NO_USABLE_SERIES','errors':' | '.join(errors)}
  if result:
   ds,j,url,g=result;obs=g['obs'];freq='monthly' if ds.endswith('_m') or ds.endswith('pem') or ds.endswith('gasm') or ds.endswith('oilm') else 'quarterly' if ds.endswith('_q') or ds.endswith('inq') or ds.endswith('outq') else 'annual'
   grid=expected_grid(obs,freq);yv=yoy(obs,freq);ytd,nmatch,nexpect=matched_ytd(obs,freq)
   missing=sum(x['value'] is None for x in grid);fresh=months_age(obs[-1][0])
   r.update(status='PASS',dataset=ds,actualFrequency=freq,latestPeriod=obs[-1][0],latestValue=obs[-1][1],ageMonths=fresh,historyCount=len(obs),windowPeriods=len(grid),missingPeriods=missing,yoyPct=yv,ytdPct=ytd,ytdMatched=f'{nmatch}/{nexpect}',selectedDimensions=json.dumps({d:code for d,code,_ in g['meta']},sort_keys=True),selectedLabels=' | '.join(l for _,_,l in g['meta']),sourceUrl=url)
  rows.append(r);print(c['key'],geo,r['status'],r.get('dataset'),r.get('latestPeriod'))
# summaries
summary=[]
for c in CFG['candidates']:
 rr=[r for r in rows if r['indicator']==c['key']];p=[r for r in rr if r['status']=='PASS']
 cov=len(p)/len(rr)*100;latest=max([r.get('latestPeriod','') for r in p] or ['']);medage=statistics.median([r['ageMonths'] for r in p]) if p else None
 recent=sum(r.get('ageMonths',999)<=6 for r in p);deep=sum((r.get('historyCount',0)>=24 if r.get('actualFrequency')=='monthly' else r.get('historyCount',0)>=8 if r.get('actualFrequency')=='quarterly' else r.get('historyCount',0)>=5) for r in p)
 decision=c['decisionSeed']
 if c['frequency'] in ('monthly','quarterly'):
  if cov>=70 and recent/max(1,len(p))>=.7 and deep/max(1,len(p))>=.7:decision='INCLUDE '+('M' if c['frequency']=='monthly' else 'Q')
  elif cov>=40:decision='CANDIDATE'
  else:decision='EXCLUDE'
 else:decision='ANNUAL'
 summary.append({'indicator':c['key'],'name':c['name'],'verticals':'; '.join(c['verticals']),'preferredFrequency':c['frequency'],'passCountries':len(p),'coveragePct':round(cov,1),'recentCountries':recent,'deepHistoryCountries':deep,'latestPeriod':latest,'medianAgeMonths':medage,'decision':decision})
json.dump({'generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'rules':CFG['rules'],'summary':summary,'results':rows},open(OUT/'market-trends-audit.json','w'),indent=2)
with open(OUT/'market-trends-audit.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in rows))));w.writeheader();w.writerows(rows)
with open(OUT/'market-trends-registry-review.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=summary[0].keys());w.writeheader();w.writerows(summary)
with open(OUT/'market-trends-audit.md','w') as f:
 f.write('# Harmonised Europe Market Trends exhaustive audit\n\n')
 f.write('| Indicator | Vertical | Frequency | Coverage | Recent | History | Latest | Decision |\n|---|---|---:|---:|---:|---:|---:|---|\n')
 for x in summary:f.write(f"| {x['name']} | {x['verticals']} | {x['preferredFrequency']} | {x['passCountries']}/29 ({x['coveragePct']}%) | {x['recentCountries']} | {x['deepHistoryCountries']} | {x['latestPeriod']} | **{x['decision']}** |\n")
 f.write('\n## Landfill note\nThe audit tests the official annual Eurostat municipal-waste landfill series (`env_wasmun`) and total-waste treatment by landfill (`env_wastrt`). No harmonised monthly Eurostat landfill deposition series is assumed. Annual landfill tonnage/rate remains in the separate Annual & Structural section unless a new official high-frequency source is validated.\n')
print('AUDIT_COMPLETE',len(rows),'country-candidate tests')
