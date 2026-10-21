#!/usr/bin/env python3
import datetime as dt,json,math,pathlib,statistics,time,urllib.parse,urllib.request
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
 return {**r,'sourceUrl':url,'series':series,'yoySeries':yoySeries,'currentYear':current,'priorYear':prior,'latestPeriod':plabel(end,f),'latestValue':latest,'yoyPct':yp,'ytdPct':ytd,'ytdMatched':f'{len(pairs)}/{pos+1}','ageMonths':age(plabel(end,f),f),'missingPeriods':sum(x['value'] is None for x in series)}
records=[];errors=[]
for i,r in enumerate(PASS,1):
 try:j,u=fetch(r);obs=parse(j);records.append(enrich(r,obs,u) if obs else {**r,'status':'NO_USABLE_SERIES','series':[]})
 except Exception as e:errors.append({'country':r['country'],'indicator':r['indicator'],'error':f'{type(e).__name__}: {e}'})
 if i%25==0:print('progress',i,'/',len(PASS),flush=True)
 time.sleep(.03)
# Regional indicator aggregate = average country YoY by period; vertical headline averages indicator YoY.
def avg(xs):
 xs=[x for x in xs if isinstance(x,(int,float)) and math.isfinite(x)];return sum(xs)/len(xs) if xs else None
indicators={}
for r in records:
 indicators.setdefault(r['indicator'],[]).append(r)
regional=[]
for key,rr in indicators.items():
 periods=sorted(set(x['period'] for r in rr for x in r.get('yoySeries',[])))[-12:]
 trend=[{'period':p,'value':avg(next((x['value'] for x in r.get('yoySeries',[]) if x['period']==p),None) for r in rr)} for p in periods]
 regional.append({'indicator':key,'name':rr[0]['name'],'verticals':rr[0]['verticals'],'frequencyMix':dict((f,sum(r.get('actualFrequency')==f for r in rr)) for f in ('monthly','quarterly','annual')),'avgYoY':avg(r.get('yoyPct') for r in rr),'avgYTD':avg(r.get('ytdPct') for r in rr),'countries':len({r['country'] for r in rr}),'trend':trend})
verticals={}
for r in regional:
 for v in r['verticals'].split('; '):verticals.setdefault(v,[]).append(r)
for v,rr in verticals.items():verticals[v]={'avgYoY':avg(x['avgYoY'] for x in rr),'avgYTD':avg(x['avgYTD'] for x in rr),'indicators':rr}
out={'schemaVersion':'2.29','generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'rules':SRC['rules'],'records':records,'regionalIndicators':regional,'verticals':verticals,'errors':errors}
OUT.write_text(json.dumps(out,indent=2)+'\n');print('MARKET_TRENDS_REFRESH_OK',len(records),'records',len(errors),'errors')
