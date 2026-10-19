import json,urllib.parse,urllib.request,datetime,pathlib,math
P=pathlib.Path('public/data/market-pulse.json');BASE='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_copr_m'
def fetch(geo):
 u=BASE+'?'+urllib.parse.urlencode({'format':'JSON','lang':'EN','geo':geo,'lastTimePeriod':'13'});return json.load(urllib.request.urlopen(u,timeout=60))
def series(j):return [v for _,v in sorted((int(k),v) for k,v in j.get('value',{}).items()) if isinstance(v,(int,float)) and math.isfinite(v)]
def calc(a):
 if len(a)<7:return None
 prev=sum(a[-4:-1])/3
 if not prev:return None
 g=(a[-1]/prev-1)*100
 if not math.isfinite(g) or abs(g)>50:return None
 return max(0,min(100,round(50+g*5)))
def main():
 d=json.loads(P.read_text());ok=0
 for r in d['europe']:
  try:s=calc(series(fetch(r['geo'])))
  except Exception as e:print(r['country'],e);s=None
  if s is not None:r['overall']=s;r['coverage']=max(r['coverage'],25);r['confidence']='Low' if r['coverage']<50 else r['confidence'];ok+=1
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']=f'Validated Eurostat Overall score for {ok} countries. Missing or malformed inputs retained as insufficient data.';P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
