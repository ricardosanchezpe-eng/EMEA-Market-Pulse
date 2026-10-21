#!/usr/bin/env python3
import json,pathlib,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]; V=ROOT/'verification-output'/'all-country-source-verification.json'; D=ROOT/'public'/'data'/'market-pulse.json'; C=ROOT/'public'/'data'/'indicator-contracts.json'; M=ROOT/'public'/'data'/'indicator-methodology.json'
FIELD={'Overall':'overall','Transportation':'transport','Site Development':'site','Waste & Water':'water','Oil & Gas':'oil','Mining':'mining','Renewables':'renewables','Agriculture':'agriculture'}
def norm(x):return max(0,min(100,round(50+float(x)*4))) if x is not None else None
def key(r):
 if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress_eu':return 'water_stress'
 if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress':return 'water_stress_wb'
 return r['indicator']
report=json.load(open(V)); data=json.load(open(D)); contracts=json.load(open(C)); method=json.load(open(M)); method_keys={x['key'] for rows in method.values() for x in rows}; idx={(u,c['country']):c for u in ('europe','emea') for c in data[u]}; applied=[]; missing=[]; technical=[]
for r in report['results']:
 u='europe' if r['universe']=='Harmonised Europe' else 'emea'; c=idx.get((u,r['country'])); k=key(r)
 if not c:technical.append([r['country'],'country_missing']);continue
 c.setdefault('indicators',{});c.setdefault('sourceStatus',{})
 if r['status']=='PASS':
  if k not in method_keys:missing.append([r['country'],r['indicator'],k]);continue
  history=[{'date':str(x.get('date')),'value':x.get('value')} for x in (r.get('history') or [])[-5:]]
  latest=history[-1] if history else {'date':r.get('latestDate'),'value':r.get('latest')}
  previous=history[-2] if len(history)>=2 else {'date':r.get('previousDate'),'value':r.get('previous')}
  change=None
  if len(history)>=2 and previous.get('value') is not None and latest.get('value') is not None:
   pv=float(previous['value']);lv=float(latest['value'])
   if r.get('frequency')=='monthly_balance':change=lv-pv
   elif pv!=0:change=(lv/pv-1)*100
  z={'raw':latest.get('value'),'date':latest.get('date'),'previous':previous.get('value'),'previousDate':previous.get('date'),'growthPct':change,'score':norm(change),'comparison':'previous_period','source':r.get('sourceUrl'),'dataset':r.get('dataset'),'provider':r.get('provider'),'verified':True,'history':history,'officialDatasetName':r.get('officialDatasetName'),'frequency':r.get('frequency'),'unit':r.get('unit'),'selectedDimensions':r.get('selectedDimensions') or {}}
  c['indicators'][k]=z;c['sourceStatus'][k]={'adapterState':'connected','retrieval':'live','provider':r.get('provider'),'dataset':r.get('dataset')};applied.append((u,r['country'],k))
 else:c['sourceStatus'][k]={'adapterState':'connected','retrieval':'no_usable_series' if r['status']=='NO_USABLE_SERIES' else 'error','reason':r['status'],'error':r.get('error'),'datasetsTried':r.get('datasetsTried')}
for u in ('europe','emea'):
 for c in data[u]:
  c.setdefault('coverage',{});c.setdefault('confidence',{})
  for vertical,items in contracts.items():
   vals=[(c['indicators'][x['key']].get('score'),x['weight']) for x in items if c['indicators'].get(x['key'],{}).get('score') is not None and x['weight']>0]; cov=sum(w for _,w in vals); f=FIELD[vertical]; c[f]=round(sum(sc*w for sc,w in vals)/cov) if cov>=15 else None;c['coverage'][f]=cov;c['confidence'][f]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
data['lastRefresh']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());data['pipelineStatus']='v2.24 UI on verified source-to-site parity architecture.';json.dump(data,open(D,'w'),ensure_ascii=False,indent=2)
summary={'verifiedPassRows':sum(r['status']=='PASS' for r in report['results']),'appliedPassRows':len(applied),'unrepresented':missing,'technical':technical};json.dump(summary,open(ROOT/'public'/'data'/'verified-source-parity.json','w'),indent=2);print(summary);sys.exit(2 if summary['verifiedPassRows']!=len(applied) or missing or technical else 0)
