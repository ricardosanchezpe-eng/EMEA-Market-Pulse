import json,pathlib,csv
D=json.load(open('public/data/market-pulse.json'));C=json.load(open('public/data/indicator-contracts.json'))
rows=[]
for universe in ('europe','emea'):
 for country in D.get(universe,[]):
  for vertical,items in C.items():
   for item in items:
    key=item['key'];z=country.get('indicators',{}).get(key);st=country.get('sourceStatus',{}).get(key,{})
    rows.append({'universe':universe,'country':country['country'],'vertical':vertical,'indicator':key,'weight':item['weight'],'adapter':item['adapter'],'retrieval':st.get('retrieval','pending'),'latest':z.get('raw') if z else None,'latestDate':z.get('date') if z else None,'previous':z.get('previous') if z else None,'previousDate':z.get('previousDate') if z else None,'score':z.get('score') if z else None})
pathlib.Path('public/data/coverage-matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
fields=['universe','country','vertical','indicator','weight','adapter','retrieval','latest','latestDate','previous','previousDate','score']
with open('public/data/coverage-matrix.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
summary={}
for r in rows:
 summary.setdefault(r['vertical'],{'contracts':0,'live':0,'countryRows':0});summary[r['vertical']]['countryRows']+=1;summary[r['vertical']]['live']+=r['retrieval']=='live'
for v in summary:summary[v]['contracts']=len(C[v]);summary[v]['liveRatePct']=round(100*summary[v]['live']/summary[v]['countryRows'],1) if summary[v]['countryRows'] else 0
pathlib.Path('public/data/coverage-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
