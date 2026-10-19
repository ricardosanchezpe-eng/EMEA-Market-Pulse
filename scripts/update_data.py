import json,urllib.parse,urllib.request,datetime,pathlib
BASE='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_copr_m'
PATH=pathlib.Path('public/data/market-pulse.json')
CODES={'Spain':'ES','France':'FR','Italy':'IT','Portugal':'PT','Germany':'DE','Poland':'PL'}
def fetch(geo):
 q={'format':'JSON','lang':'EN','geo':geo,'lastTimePeriod':'13'}
 url=BASE+'?'+urllib.parse.urlencode(q)
 with urllib.request.urlopen(url,timeout=60) as r:return json.load(r)
def values(js):
 vals=js.get('value',{});return [v for _,v in sorted(((int(k),v) for k,v in vals.items())) if isinstance(v,(int,float))]
def score(series):
 if len(series)<2:return None
 prev=sum(series[-4:-1])/max(1,len(series[-4:-1]));growth=(series[-1]/prev-1)*100 if prev else 0
 return max(0,min(100,round(50+growth*5)))
def main():
 d=json.load(open(PATH,encoding='utf-8'));ok=0
 for row in d['europe']:
  try:
   s=score(values(fetch(CODES[row['country']])))
   if s is not None:row['overall']=s;ok+=1
  except Exception as e:print(row['country'],e)
 d['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 d['pipelineStatus']=f'Eurostat overall construction refreshed for {ok} countries; vertical adapters retain last validated values.'
 json.dump(d,open(PATH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
if __name__=='__main__':main()
