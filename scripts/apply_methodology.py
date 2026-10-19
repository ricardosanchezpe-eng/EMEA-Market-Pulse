import json,pathlib
p=pathlib.Path('public/data/market-pulse.json');m=pathlib.Path('public/data/indicator-methodology.json')
d=json.loads(p.read_text(encoding='utf-8'));x=json.loads(m.read_text(encoding='utf-8'))
for k,v in x.items():
 if sum(i['weight'] for i in v)!=100:raise ValueError(k)
d['indicators']=x;d['methodologyVersion']='2.7-full-51-indicator-model';d['pipelineStatus']='Full 51-indicator methodology active. Scores publish only when minimum weighted coverage is met.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('Merged',sum(map(len,x.values())),'indicator definitions while preserving country data.')
