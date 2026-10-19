import json,urllib.parse,urllib.request,datetime,pathlib
P=pathlib.Path('public/data/market-pulse.json');C={'Spain':'ES','France':'FR','Italy':'IT','Portugal':'PT','Germany':'DE','Poland':'PL'};BASE='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_copr_m'
def main():
 d=json.loads(P.read_text());ok=0
 for r in d['europe']:
  try:
   u=BASE+'?'+urllib.parse.urlencode({'format':'JSON','lang':'EN','geo':C[r['country']],'lastTimePeriod':'13'});j=json.load(urllib.request.urlopen(u,timeout=60));vals=[v for _,v in sorted((int(k),v) for k,v in j.get('value',{}).items()) if isinstance(v,(int,float))]
   if len(vals)>1:
    prev=sum(vals[-4:-1])/len(vals[-4:-1]);r['overall']=max(0,min(100,round(50+(vals[-1]/prev-1)*500))) if prev else r['overall'];ok+=1
  except Exception as e: print(r['country'],e)
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['pipelineStatus']=f'Eurostat construction refreshed for {ok} Harmonised Europe markets; vertical adapters retain last validated observations.';P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
