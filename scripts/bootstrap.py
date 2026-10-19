import json,pathlib
from config import COUNTRIES,GDP_ORDER
p=pathlib.Path('public/data/market-pulse.json')
rows=[]
for n,g,w,i in COUNTRIES:rows.append({'country':n,'geo':g,'wb':w,'id':i,'gdpRank':GDP_ORDER[n],'overall':None,'transport':None,'site':None,'water':None,'oil':None,'mining':None,'renewables':None,'agriculture':None,'coverage':{},'confidence':{},'indicators':{},'stale':False})
d={'generatedAt':'Initial v2.8 package — run Weekly market data refresh once','pipelineStatus':'No live refresh has run yet.','europe':rows,'history':{},'diagnostics':[]}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
