import json, pathlib, sys
from source_registry import EUROSTAT, WORLD_BANK
from update_data import euro, unpack, metric, wb
COUNTRIES=[
 {'country':'Germany','geo':'DE','wb':'DEU','universe':'Europe'},
 {'country':'Spain','geo':'ES','wb':'ESP','universe':'Europe'},
 {'country':'Poland','geo':'PL','wb':'POL','universe':'Europe'},
 {'country':'Saudi Arabia','geo':'SA','wb':'SAU','universe':'Broader EMEA'},
 {'country':'South Africa','geo':'ZA','wb':'ZAF','universe':'Broader EMEA'}]
CONTRACTS=json.load(open('public/data/indicator-contracts.json'))
rows=[]
for c in COUNTRIES:
 cache={}
 for key,conf in EUROSTAT.items():
  row={'universe':c['universe'],'country':c['country'],'source':'Eurostat','indicator':key,'dataset':conf['dataset'],'adapterState':conf['status']}
  try:
   if conf['dataset'] not in cache:cache[conf['dataset']]=euro(conf['dataset'],c['geo'])
   j,u=cache[conf['dataset']]; meta,a=unpack(j,conf.get('filters')); z=metric(a,conf['frequency']);row.update(status='PASS' if z else 'NO_COMPARABLE_SERIES',observations=len(a),latest=z.get('raw') if z else None,latestDate=z.get('date') if z else None,previous=z.get('previous') if z else None,previousDate=z.get('previousDate') if z else None,score=z.get('score') if z else None,selectedDimensions=dict(meta or []),url=u)
  except Exception as e:row.update(status='ERROR',error=repr(e),observations=0)
  rows.append(row)
 for key,indicator in WORLD_BANK.items():
  row={'universe':c['universe'],'country':c['country'],'source':'World Bank','indicator':key,'dataset':indicator,'adapterState':'connected'}
  try:z,u=wb(c['wb'],indicator);row.update(status='PASS' if z else 'NO_COMPARABLE_SERIES',observations=None,latest=z.get('raw') if z else None,latestDate=z.get('date') if z else None,previous=z.get('previous') if z else None,previousDate=z.get('previousDate') if z else None,score=z.get('score') if z else None,url=u)
  except Exception as e:row.update(status='ERROR',error=repr(e),observations=0)
  rows.append(row)
# Contract-to-adapter mapping and vertical coverage on test countries
registry=set(EUROSTAT)|set(WORLD_BANK)
contract_rows=[]
for vertical,items in CONTRACTS.items():
 for item in items:
  contract_rows.append({'vertical':vertical,'indicator':item['key'],'weight':item['weight'],'adapter':item['adapter'],'implemented':item['key'] in registry or item['adapter']=='pending'})
summary={}
for vertical,items in CONTRACTS.items():
 keys={x['key'] for x in items};rel=[r for r in rows if r['indicator'] in keys]
 summary[vertical]={'contracts':len(items),'implementedContracts':sum(1 for x in items if x['key'] in registry),'pendingContracts':sum(1 for x in items if x['adapter']=='pending'),'testRows':len(rel),'passes':sum(r['status']=='PASS' for r in rel),'noComparable':sum(r['status']=='NO_COMPARABLE_SERIES' for r in rel),'errors':sum(r['status']=='ERROR' for r in rel)}
out={'testCountries':COUNTRIES,'sourceResults':rows,'contractMapping':contract_rows,'verticalSummary':summary}
pathlib.Path('data-architecture-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
with open('data-architecture-verification.md','w',encoding='utf-8') as f:
 f.write('# Data architecture verification\n\n')
 f.write('## Vertical summary\n\n| Vertical | Contracts | Implemented | Pending | Passes | No comparable | Errors |\n|---|---:|---:|---:|---:|---:|---:|\n')
 for v,x in summary.items():f.write(f"| {v} | {x['contracts']} | {x['implementedContracts']} | {x['pendingContracts']} | {x['passes']} | {x['noComparable']} | {x['errors']} |\n")
 f.write('\n## Source tests\n\n| Universe | Country | Source | Indicator | Dataset | State | Result | Latest date | Previous date |\n|---|---|---|---|---|---|---|---|---|\n')
 for r in rows:f.write(f"| {r['universe']} | {r['country']} | {r['source']} | {r['indicator']} | {r['dataset']} | {r['adapterState']} | {r['status']} | {r.get('latestDate','')} | {r.get('previousDate','')} |\n")
print(json.dumps(summary,indent=2))
# Connected adapters must not error for all three European test countries.
fatal=[]
for key,conf in EUROSTAT.items():
 if conf['status']=='connected':
  eu=[r for r in rows if r['source']=='Eurostat' and r['indicator']==key and r['universe']=='Europe']
  if eu and all(r['status']!='PASS' for r in eu):fatal.append(key)
for key in WORLD_BANK:
 wbrows=[r for r in rows if r['source']=='World Bank' and r['indicator']==key]
 if wbrows and all(r['status']!='PASS' for r in wbrows):fatal.append(key)
if fatal:print('FAILED connected adapters:',fatal);sys.exit(2)
