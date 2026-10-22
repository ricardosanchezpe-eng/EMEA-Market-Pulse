#!/usr/bin/env python3
import datetime as dt,json,math,pathlib,statistics,time,urllib.parse,urllib.request
from gdp_weighting import fetch_gdp_weights,weighted_avg,represented_gdp_pct
ROOT=pathlib.Path(__file__).resolve().parents[1];AUD=ROOT/'public/data/market-trends-audit.json';OUT=ROOT/'public/data/market-trends.json'
SRC=json.load(open(AUD)); PASS=[r for r in SRC['results'] if r.get('status')=='PASS']; BASE='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
def fetch(r):
 q={'geo':r['geo'],'lang':'en','lastTimePeriod':48}
 try:q.update(json.loads(r.get('selectedDimensions') or '{}'))
 except:pass
 q['geo']=r['geo'];u=BASE+r['dataset']+'?'+urllib.parse.urlencode(q,doseq=True)
 req=urllib.request.Request(u,headers={'User-Agent':'EMEA-Market-Pulse-Trends/2.29'})
 with urllib.request.urlopen(req,timeout=90) as x:return json.load(x),u
def inv(cat):return {int(v):k for k,v in (cat or {}).get('index',{}).items()}
def parse(j):
 dims=j['id'];sizes=j['size'];T=dims.index('time');times=inv(j['dimension']['time']['category']);vals=j.get('value',{});out=[]
 def dec(n):
  c=[]
  for s in reversed(sizes):c.append(n%s);n//=s
  return list(reversed(c))
 for k,v in vals.items():
  try:v=float(v)
  except:continue
  c=dec(int(k));out.append((times.get(c[T],str(c[T])),v))
 return sorted(out)
def pord(p,f):
 if f=='monthly':return int(p[:4])*12+int(p[5:7])-1
 if f=='quarterly':return int(p[:4])*4+int(p[-1])-1
 return int(p[:4])
def plabel(o,f):
 if f=='monthly':return f'{o//12:04d}-{o%12+1:02d}'
 if f=='quarterly':return f'{o//4:04d}-Q{o%4+1}'
 return str(o)
def age(p,f):
 now=dt.date.today();o=pord(p,f)
 return (now.year*12+now.month-1-o) if f=='monthly' else ((now.year*4+(now.month-1)//3-o)*3 if f=='quarterly' else (now.year-o)*12)
def enrich(r,obs,url):
 f=r.get('actualFrequency') or r.get('preferredFrequency');step=12 if f=='monthly' else 4 if f=='quarterly' else 1;window=24 if f=='monthly' else 8 if f=='quarterly' else 6
 vals={pord(p,f):v for p,v in obs};end=max(vals);start=end-window+1;series=[{'period':plabel(o,f),'value':vals.get(o)} for o in range(start,end+1)]
 def yoy(o):
  a=vals.get(o);b=vals.get(o-step);return None if a is None or b in (None,0) else (a/b-1)*100
 yoySeries=[{'period':plabel(o,f),'value':yoy(o)} for o in range(start,end+1)]
 latest=vals[end];yp=yoy(end);pos=end%step;pairs=[(vals.get(end-pos+i),vals.get(end-pos-step+i)) for i in range(pos+1)];pairs=[x for x in pairs if x[0] is not None and x[1] is not None]
 ytd=None
 if pairs and sum(b for _,b in pairs)!=0:ytd=(sum(a for a,_ in pairs)/sum(b for _,b in pairs)-1)*100
 current=[{'slot':i+1,'period':plabel(end-pos+i,f),'value':vals.get(end-pos+i)} for i in range(pos+1)] if f!='annual' else series[-1:]
 prior=[{'slot':i+1,'period':plabel(end-pos-step+i,f),'value':vals.get(end-pos-step+i)} for i in range(pos+1)] if f!='annual' else series[-2:-1]
 role='leading_survey' if r['indicator']=='construction_confidence' else ('pressure' if r['indicator']=='construction_costs' else 'activity')
 eligible=(role=='activity' and f in ('monthly','quarterly'))
 return {**r,'sourceUrl':url,'series':series,'yoySeries':yoySeries,'currentYear':current,'priorYear':prior,'latestPeriod':plabel(end,f),'latestValue':latest,'yoyPct':yp,'ytdPct':ytd,'yoyPointChange':(latest-vals.get(end-lag)) if vals.get(end-lag) is not None else None,'indicatorRole':role,'includedInVerticalAverage':eligible,'ytdMatched':f'{len(pairs)}/{pos+1}','ageMonths':age(plabel(end,f),f),'missingPeriods':sum(x['value'] is None for x in series)}
records=[];errors=[]
for i,r in enumerate(PASS,1):
 try:j,u=fetch(r);obs=parse(j);records.append(enrich(r,obs,u) if obs else {**r,'status':'NO_USABLE_SERIES','series':[]})
 except Exception as e:errors.append({'country':r['country'],'indicator':r['indicator'],'error':f'{type(e).__name__}: {e}'})
 if i%25==0:print('progress',i,'/',len(PASS),flush=True)
 time.sleep(.03)
# GDP-weighted eligible activity aggregation; surveys/pressure/annual remain visible but excluded from vertical headline.
def avg(xs):
 xs=[x for x in xs if isinstance(x,(int,float)) and math.isfinite(x)];return sum(xs)/len(xs) if xs else None
ctg={r['country']:r.get('geo') for r in records if r.get('country') and r.get('geo')}
gdp,gdp_meta=fetch_gdp_weights(ctg)
inds={}
for r in records:inds.setdefault(r['indicator'],[]).append(r)
regional=[]
for key,rr in inds.items():
 role=rr[0].get('indicatorRole','activity');metric='yoyPointChange' if role=='leading_survey' else 'yoyPct';items=[(r['country'],r.get(metric)) for r in rr]
 regional.append({'indicator':key,'name':rr[0]['name'],'verticals':rr[0]['verticals'],'indicatorRole':role,'includedInVerticalAverage':any(r.get('includedInVerticalAverage') for r in rr),'displayChangeUnit':'points' if role=='leading_survey' else '%','latestPeriod':max((r.get('latestPeriod') for r in rr if r.get('latestPeriod')),default=None),'frequencyMix':dict((f,sum(r.get('actualFrequency')==f for r in rr)) for f in ('monthly','quarterly','annual')),'avgYoY':weighted_avg(items,gdp),'avgYTD':weighted_avg([(r['country'],r.get('ytdPct')) for r in rr],gdp),'countries':sum(1 for _,v in items if isinstance(v,(int,float))),'trend':[]})
verticals={}
for r in regional:
 for v in r['verticals'].split('; '):verticals.setdefault(v,[]).append(r)
for v,rr in verticals.items():
 inc=[x for x in rr if x['includedInVerticalAverage']];m=[x['latestPeriod'] for x in inc if x['latestPeriod'] and x['frequencyMix']['monthly']];q=[x['latestPeriod'] for x in inc if x['latestPeriod'] and x['frequencyMix']['quarterly']]
 verticals[v]={'avgYoY':avg(x['avgYoY'] for x in inc),'avgYTD':avg(x['avgYTD'] for x in inc),'latestPeriod':max((x['latestPeriod'] for x in inc if x['latestPeriod']),default=None),'latestMonthlyPeriod':max(m,default=None),'latestQuarterlyPeriod':max(q,default=None),'eligibleIndicatorCount':len(inc),'excludedIndicatorCount':len(rr)-len(inc),'indicators':rr}
out={'schemaVersion':'2.36','generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'rules':SRC['rules'],'aggregationMethod':{'countryWeighting':'GDP weighted','excludedRoles':['leading_survey','pressure','annual_or_structural'],'gdp':gdp_meta},'gdpWeights':gdp,'records':records,'regionalIndicators':regional,'verticals':verticals,'errors':errors}
OUT.write_text(json.dumps(out,indent=2)+'\n');print('MARKET_TRENDS_REFRESH_OK',len(records),'records',len(errors),'errors')
