#!/usr/bin/env python3
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
V=ROOT/'verification-output'/'all-country-source-verification.json'
D=ROOT/'public'/'data'/'market-pulse.json'
O=ROOT/'public'/'data'/'history-parity.json'

def mapped_key(r):
    if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress_eu': return 'water_stress'
    if r['universe']=='Harmonised Europe' and r['indicator']=='water_stress': return 'water_stress_wb'
    return r['indicator']

def clean_history(h):
    return [{'date':str(x.get('date')),'value':x.get('value')} for x in (h or [])[-5:]]

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

v=json.load(open(V)); d=json.load(open(D))
idx={(('Harmonised Europe' if u=='europe' else 'Broader EMEA'),c['country']):c for u in ('europe','emea') for c in d[u]}
errors=[]; rows=[]
for r in v['results']:
    if r.get('status')!='PASS': continue
    c=idx.get((r['universe'],r['country'])); k=mapped_key(r)
    z=(c or {}).get('indicators',{}).get(k,{})
    expected=clean_history(r.get('history'))
    actual=clean_history(z.get('history'))
    if expected != actual:
        errors.append({'universe':r['universe'],'country':r['country'],'indicator':k,'issue':'history_mismatch','expected':expected,'actual':actual})
        continue
    if expected:
        latest=expected[-1]
        if z.get('raw')!=latest['value'] or str(z.get('date'))!=latest['date']:
            errors.append({'universe':r['universe'],'country':r['country'],'indicator':k,'issue':'latest_not_history_tail'})
        if len(expected)>=2:
            prev=expected[-2]
            if z.get('previous')!=prev['value'] or str(z.get('previousDate'))!=prev['date']:
                errors.append({'universe':r['universe'],'country':r['country'],'indicator':k,'issue':'previous_not_immediate_history'})
    rows.append({'universe':r['universe'],'country':r['country'],'indicator':k,'historyLength':len(expected),'historyHash':digest(expected)})
manifest={'schemaVersion':'2.27','verifiedPassRows':len(rows),'historyRows':sum(x['historyLength']>0 for x in rows),'fivePointRows':sum(x['historyLength']==5 for x in rows),'rows':rows,'errors':errors}
O.write_text(json.dumps(manifest,indent=2)+'\n')
print('HISTORY_PARITY_ROWS',len(rows))
print('HISTORY_ROWS',manifest['historyRows'])
print('FIVE_POINT_ROWS',manifest['fivePointRows'])
if errors:
    print(json.dumps(errors[:20],indent=2));sys.exit(2)
print('HISTORY_PARITY_OK')
