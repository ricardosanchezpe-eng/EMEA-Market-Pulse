#!/usr/bin/env python3
"""Apply every verified PASS observation to market-pulse.json and prove UI parity."""
import json,pathlib,time,sys
from update_data import FIELD
def norm(x):
    return max(0,min(100,round(50+float(x)*4))) if x is not None else None
ROOT=pathlib.Path(__file__).resolve().parents[1]
VERIFY=ROOT/'verification-output'/'all-country-source-verification.json'
DATA=ROOT/'public'/'data'/'market-pulse.json'
CONTRACTS=ROOT/'public'/'data'/'indicator-contracts.json'
METHOD=ROOT/'public'/'data'/'indicator-methodology.json'
if not VERIFY.exists(): raise SystemExit('Missing verification-output/all-country-source-verification.json')
report=json.loads(VERIFY.read_text());rows=report['results'];d=json.loads(DATA.read_text());contracts=json.loads(CONTRACTS.read_text());method=json.loads(METHOD.read_text())
method_keys={x['key'] for rr in method.values() for x in rr};contract_keys={x['key'] for rr in contracts.values() for x in rr}
country={(u,c['country']):c for u in ('europe','emea') for c in d.get(u,[])}

def output_key(r):
    # Europe: Eurostat WEI+ is the primary weighted water-stress observation;
    # World Bank water stress remains visible as supplemental context.
    if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress_eu': return 'water_stress'
    if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress': return 'water_stress_wb'
    return r['indicator']

applied=[];unrepresented=[];technical=[]
for r in rows:
    u='europe' if r['universe']=='Harmonised Europe' else 'emea';c=country.get((u,r['country']))
    if c is None: technical.append({'row':r,'reason':'country_missing'});continue
    key=output_key(r);c.setdefault('indicators',{});c.setdefault('sourceStatus',{})
    if r['status']=='PASS':
        if key not in method_keys:
            unrepresented.append({'country':r['country'],'sourceIndicator':r['indicator'],'mappedKey':key});continue
        change=r.get('change')
        z={'raw':r.get('latest'),'date':r.get('latestDate'),'previous':r.get('previous'),'previousDate':r.get('previousDate'),'growthPct':change,'score':norm(change) if change is not None else None,'comparison':r.get('comparison'),'source':r.get('sourceUrl'),'dataset':r.get('dataset'),'provider':r.get('provider'),'verified':True,'verifiedAt':report.get('summary',{}).get('generatedAt')}
        if r.get('selectedDimensions') is not None:z['selectedDimensions']=r['selectedDimensions']
        c['indicators'][key]=z;c['sourceStatus'][key]={'adapterState':'connected','retrieval':'live','provider':r.get('provider'),'dataset':r.get('dataset'),'sourceIndicator':r.get('indicator')};applied.append((u,r['country'],r['indicator'],key))
    else:
        existing=c['indicators'].get(key)
        c['sourceStatus'][key]={'adapterState':'connected','retrieval':'no_usable_series' if r['status']=='NO_USABLE_SERIES' else 'error','reason':r['status'],'error':r.get('error'),'datasetsTried':r.get('datasetsTried')}
        if existing: existing['stale']=True;existing['refreshStatus']=r['status']
# Recalculate composite fields from weighted contracts only.
for u in ('europe','emea'):
 for c in d.get(u,[]):
  c.setdefault('coverage',{});c.setdefault('confidence',{})
  for vertical,items in contracts.items():
   vals=[(c['indicators'][x['key']].get('score'),x['weight']) for x in items if c['indicators'].get(x['key'],{}).get('score') is not None and x['weight']>0]
   cov=sum(w for _,w in vals);field=FIELD[vertical]
   c[field]=round(sum(sc*w for sc,w in vals)/cov) if cov>=15 else None
   c['coverage'][field]=cov;c['confidence'][field]='High' if cov>=75 else 'Medium' if cov>=50 else 'Low' if cov>=15 else 'Insufficient'
d['lastRefresh']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());d['pipelineStatus']='v2.22 verified-source parity: every PASS observation is applied to a visible Indicator Intelligence key.'
DATA.write_text(json.dumps(d,ensure_ascii=False,indent=2))
# Exact parity test: every PASS must now be represented with the verified value/date.
post=json.loads(DATA.read_text());pc={(u,c['country']):c for u in ('europe','emea') for c in post.get(u,[])};mismatch=[]
for r in rows:
 if r['status']!='PASS':continue
 u='europe' if r['universe']=='Harmonised Europe' else 'emea';key=output_key(r);z=pc[(u,r['country'])].get('indicators',{}).get(key)
 if not z or z.get('raw')!=r.get('latest') or z.get('date')!=r.get('latestDate') or z.get('previous')!=r.get('previous') or z.get('previousDate')!=r.get('previousDate'):
  mismatch.append({'country':r['country'],'indicator':r['indicator'],'mappedKey':key})
summary={'verifiedPassRows':sum(r['status']=='PASS' for r in rows),'appliedPassRows':len(applied),'unrepresented':unrepresented,'mismatches':mismatch,'technical':technical,'visibleMethodologyKeys':len(method_keys),'weightedContractKeys':len(contract_keys)}
(ROOT/'public'/'data'/'verified-source-parity.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
if unrepresented or mismatch or technical or len(applied)!=summary['verifiedPassRows']:sys.exit(2)
