#!/usr/bin/env python3
import csv,json,pathlib,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
import update_data as u
from source_registry import EUROSTAT,WORLD_BANK
ROOT=pathlib.Path(__file__).resolve().parents[1];DATA=ROOT/'public'/'data';OUT=ROOT/'verification-output';OUT.mkdir(exist_ok=True)
market=json.loads((DATA/'market-pulse.json').read_text());contracts=json.loads((DATA/'indicator-contracts.json').read_text());method=json.loads((DATA/'indicator-methodology.json').read_text())
contract_keys={x['key'] for rows in contracts.values() for x in rows};method_keys={x['key'] for rows in method.values() for x in rows}
def eu(c,k,conf):
 r={'universe':'Harmonised Europe','country':c['country'],'geo':c['geo'],'provider':'Eurostat','indicator':k,'dataset':None,'status':'NO_USABLE_SERIES','latest':None,'latestDate':None,'previous':None,'previousDate':None,'change':None,'comparison':conf.get('comparison'),'datasetsTried':[],'selectedDimensions':None,'error':None,'sourceUrl':None}
 for ds in [conf['dataset']]+conf.get('fallbacks',[]):
  r['datasetsTried'].append(ds)
  try:
   j,url=u.euro(ds,c['geo'],conf.get('geo_dimension','geo'));meta,a=u.choose(j,conf);z=u.calc(a,conf)
   if z and z.get('raw') is not None:r.update(status='PASS',dataset=ds,latest=z.get('raw'),latestDate=z.get('date'),previous=z.get('previous'),previousDate=z.get('previousDate'),change=z.get('growthPct'),comparison=z.get('comparison') or conf.get('comparison'),selectedDimensions=dict(meta or []),sourceUrl=url);return r
  except Exception as e:r['error']=f'{type(e).__name__}: {e}';r['status']='HTTP_'+str(getattr(e,'code','ERROR')) if getattr(e,'code',None) else 'ERROR'
 return r
def wb(c,k,code,universe):
 r={'universe':universe,'country':c['country'],'geo':c.get('geo'),'provider':'World Bank','indicator':k,'dataset':code,'status':'NO_USABLE_SERIES','latest':None,'latestDate':None,'previous':None,'previousDate':None,'change':None,'comparison':'previous','datasetsTried':[code],'selectedDimensions':None,'error':None,'sourceUrl':None}
 try:
  z,url=u.wb(c.get('wb') or c['geo'],code)
  if z and z.get('raw') is not None:r.update(status='PASS',latest=z.get('raw'),latestDate=z.get('date'),previous=z.get('previous'),previousDate=z.get('previousDate'),change=z.get('growthPct'),comparison=z.get('comparison') or 'previous',sourceUrl=url)
 except Exception as e:r['error']=f'{type(e).__name__}: {e}';r['status']='HTTP_'+str(getattr(e,'code','ERROR')) if getattr(e,'code',None) else 'ERROR'
 return r
jobs=[]
for c in market['europe']:
 jobs += [('eu',c,k,v,'Harmonised Europe') for k,v in EUROSTAT.items()];jobs += [('wb',c,k,v,'Harmonised Europe') for k,v in WORLD_BANK.items()]
for c in market['emea']:jobs += [('wb',c,k,v,'Broader EMEA') for k,v in WORLD_BANK.items()]
rows=[]
with ThreadPoolExecutor(max_workers=10) as pool:
 futs=[pool.submit(eu,c,k,v) if typ=='eu' else pool.submit(wb,c,k,v,univ) for typ,c,k,v,univ in jobs]
 for i,f in enumerate(as_completed(futs),1):
  r=f.result();rows.append(r);print(f'[{i}/{len(futs)}] {r["country"]} | {r["provider"]} | {r["indicator"]} | {r["status"]}',flush=True)
rows.sort(key=lambda r:(r['universe'],r['country'],r['provider'],r['indicator']))
fields=list(rows[0])
with (OUT/'all-country-source-verification.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in rows:
  rr=r.copy();rr['datasetsTried']=json.dumps(rr['datasetsTried'],ensure_ascii=False);rr['selectedDimensions']=json.dumps(rr['selectedDimensions'],ensure_ascii=False);w.writerow(rr)
counts={};by={}
for r in rows:
 counts[r['status']]=counts.get(r['status'],0)+1
 x=by.setdefault(f'{r["provider"]}:{r["indicator"]}',{'PASS':0,'NO_USABLE_SERIES':0,'ERROR':0})
 if r['status']=='PASS':x['PASS']+=1
 elif r['status']=='NO_USABLE_SERIES':x['NO_USABLE_SERIES']+=1
 else:x['ERROR']+=1
summary={'generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'countries':{'europe':len(market['europe']),'emea':len(market['emea']),'total':len(market['europe'])+len(market['emea'])},'adapters':{'eurostat':len(EUROSTAT),'worldBank':len(WORLD_BANK)},'totalChecks':len(rows),'statusCounts':counts,'perIndicator':by,'contractIntegrity':{'contractKeys':len(contract_keys),'methodologyKeys':len(method_keys),'missingFromMethodology':sorted(contract_keys-method_keys),'missingFromContracts':sorted(method_keys-contract_keys)}}
(OUT/'all-country-source-verification.json').write_text(json.dumps({'summary':summary,'results':rows},indent=2,ensure_ascii=False))
md=['# All-country source verification','',f'- Total checks: {len(rows)}',f'- Countries: {summary["countries"]["total"]}',f'- Eurostat adapters: {len(EUROSTAT)}',f'- World Bank adapters: {len(WORLD_BANK)}','','## Results by indicator','','| Indicator | Pass | No usable series | Errors |','|---|---:|---:|---:|']
for k,v in sorted(by.items()):md.append(f'| {k} | {v["PASS"]} | {v["NO_USABLE_SERIES"]} | {v["ERROR"]} |')
(OUT/'all-country-source-verification.md').write_text('\n'.join(md)+'\n')
hard=[r for r in rows if r['status'] not in ('PASS','NO_USABLE_SERIES')];bad=summary['contractIntegrity']['missingFromMethodology'] or summary['contractIntegrity']['missingFromContracts']
print(json.dumps(summary,indent=2))
import os
strict=os.environ.get('VERIFICATION_STRICT','1')!='0'
sys.exit(2 if bad or (strict and hard) else 0)
