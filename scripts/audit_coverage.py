import json,pathlib,csv
D=json.load(open('public/data/market-pulse.json'));C=json.load(open('public/data/indicator-contracts.json'))
rows=[]
for universe in ('europe','emea'):
 for country in D.get(universe,[]):
  for vertical,items in C.items():
   for item in items:
    key=item['key'];z=country.get('indicators',{}).get(key);st=country.get('sourceStatus',{}).get(key,{})
    rows.append({'universe':universe,'country':country['country'],'vertical':vertical,'indicator':key,'weight':item['weight'],'adapter':item['adapter'],'retrieval':st.get('retrieval','pending'),'latest':z.get('raw') if z else None,'latestDate':z.get('date') if z else None,'previous':z.get('previous') if z else None,'previousDate':z.get('previousDate') if z else None,'growthPct':z.get('growthPct') if z else None,'comparison':z.get('comparison') if z else None,'score':z.get('score') if z else None})
fields=['universe','country','vertical','indicator','weight','adapter','retrieval','latest','latestDate','previous','previousDate','growthPct','comparison','score']
pathlib.Path('public/data').mkdir(parents=True,exist_ok=True)
pathlib.Path('public/data/coverage-matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with open('public/data/coverage-matrix.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
summary={}
for vertical,items in C.items():summary[vertical]={'contracts':len(items),'live':0,'countryRows':0,'liveRatePct':0}
for r in rows:
 x=summary[r['vertical']];x['countryRows']+=1;x['live']+=r['retrieval']=='live'
for x in summary.values():x['liveRatePct']=round(100*x['live']/x['countryRows'],1) if x['countryRows'] else 0
pathlib.Path('public/data/coverage-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'rows':len(rows),'countries':sum(len(D.get(u,[])) for u in ('europe','emea')),'summary':summary},indent=2))
