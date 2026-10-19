import json,urllib.request,urllib.parse,urllib.error,gzip,io,csv,datetime,pathlib,math,time
P=pathlib.Path('public/data/market-pulse.json');API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
def request(url,tries=4):
 for n in range(tries):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-GitHubActions/2.6','Accept':'application/json,text/plain,*/*'});return urllib.request.urlopen(req,timeout=120).read()
  except urllib.error.HTTPError as e:
   if e.code not in (403,429,500,502,503,504) or n==tries-1:raise
   time.sleep(4*(n+1))
def api(geo):
 u=API+'sts_copr_m?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'});return json.loads(request(u)),u
def decode(j,nace):
 ids=j['id'];sizes=j['size'];dims=j['dimension'];cats=[]
 for x in ids:cats.append([k for k,v in sorted(dims[x]['category']['index'].items(),key=lambda z:z[1])])
 groups={}
 for k,v in j.get('value',{}).items():
  n=int(k);coords=[]
  for s in reversed(sizes):coords.append(n%s);n//=s
  codes=[cats[i][coords[::-1][i]] for i in range(len(ids))]
  if 'nace_r2' in ids and codes[ids.index('nace_r2')]!=nace:continue
  key=tuple(codes[i] for i,x in enumerate(ids) if x!='time');groups.setdefault(key,[]).append((codes[ids.index('time')],v))
 usable=[]
 for a in groups.values():
  vals=[v for _,v in sorted(a) if isinstance(v,(int,float)) and math.isfinite(v)]
  if len(vals)>=13:usable.append(vals)
 return max(usable,key=len) if usable else []
def score(a):
 if len(a)<13 or not a[-13]:return None
 g=(a[-1]/a[-13]-1)*100
 return None if not math.isfinite(g) or abs(g)>80 else round(max(0,min(100,50+4*g)))
def main():
 d=json.loads(P.read_text());last={c['geo']:c.copy() for c in d['europe']};log=[]
 for c in d['europe']:
  try:
   j,url=api(c['geo']);f,f41,f42=score(decode(j,'F')),score(decode(j,'F41')),score(decode(j,'F42'));valid=[(f,.55),(f42,.25),(f41,.20)];have=[x for x in valid if x[0] is not None];cov=round(sum(w for _,w in have)*100);overall=round(sum(s*w for s,w in have)/sum(w for _,w in have)) if cov>=45 else None
   if overall is not None:c.update(overall=overall,transport=f42,site=f41,coverage=cov,confidence='High' if cov>=80 else 'Medium' if cov>=55 else 'Low',stale=False,sourceUrl=url);status='published'
   else:status='insufficient'
  except Exception as e:status='retained-last-good';c['stale']=True
  log.append({'country':c['country'],'status':status,'overall':c.get('overall'),'coverage':c.get('coverage',0)})
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']=f"Eurostat refresh completed: {sum(x['status']=='published' for x in log)} countries published; failed retrievals retained last validated data.";d['diagnostics']=log;P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
 pathlib.Path('public/data/refresh-diagnostics.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
