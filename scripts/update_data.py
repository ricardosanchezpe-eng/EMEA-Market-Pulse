import json,urllib.parse,urllib.request,datetime,pathlib,math,itertools,time
P=pathlib.Path('public/data/market-pulse.json');API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
def get(ds,geo):
 q=urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});r=urllib.request.Request(API+ds+'?'+q,headers={'User-Agent':'EMEA-Market-Pulse/2.4','Accept':'application/json'});return json.load(urllib.request.urlopen(r,timeout=90))
def decode(j):
 ids=j['id'];sizes=j['size'];dims=j['dimension'];rev=[]
 for x in ids:
  idx=dims[x]['category']['index'];rev.append([k for k,v in sorted(idx.items(),key=lambda kv:kv[1])])
 out={}
 for k,v in j.get('value',{}).items():
  n=int(k);coords=[]
  for s in reversed(sizes):coords.append(n%s);n//=s
  codes=tuple(rev[i][coords[::-1][i]] for i in range(len(ids)));key=tuple(codes[i] for i,x in enumerate(ids) if x!='time');t=codes[ids.index('time')];out.setdefault(key,[]).append((t,v))
 return ids,out
def choose(j,nace):
 ids,groups=decode(j);ni=[i for i,x in enumerate(ids) if x!='time'].index('nace_r2') if 'nace_r2' in ids else None
 cand=[]
 for key,obs in groups.items():
  if ni is not None and key[ni]!=nace:continue
  vals=[v for _,v in sorted(obs) if isinstance(v,(int,float)) and math.isfinite(v)]
  if len(vals)>=13:cand.append(vals)
 return max(cand,key=len) if cand else []
def score(a):
 if len(a)<13 or not a[-13]:return None
 g=(a[-1]/a[-13]-1)*100
 return None if not math.isfinite(g) or abs(g)>80 else round(max(0,min(100,50+4*g)))
def main():
 d=json.loads(P.read_text());ok=0
 for c in d['europe']:
  try:j=get('sts_copr_m',c['geo'])
  except Exception as e:print(c['country'],e);continue
  allv,civ,bld=score(choose(j,'F')),score(choose(j,'F42')),score(choose(j,'F41'))
  parts=[(allv,.55),(civ,.25),(bld,.20)];valid=[x for x in parts if x[0] is not None];cov=round(sum(w for _,w in valid)*100);overall=round(sum(s*w for s,w in valid)/sum(w for _,w in valid)) if cov>=45 else None
  c.update(overall=overall,transport=civ,site=bld,coverage=cov,confidence='High' if cov>=80 else 'Medium' if cov>=55 else 'Low' if overall is not None else 'Insufficient')
  if overall is not None:ok+=1
  time.sleep(.15)
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']=f'Live Eurostat construction data validated for {ok} of {len(d["europe"])} countries. Other cells remain insufficient until their official adapters return observations.';P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
