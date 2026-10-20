"""Offline regression checks. No internet required."""
import json
import update_data as u
from source_registry import EUROSTAT,WORLD_BANK
contracts=json.load(open('public/data/indicator-contracts.json'))
# Return a compact valid JSON-stat cube for any Eurostat dataset.
def fake_euro(ds,geo,gd='geo',filters=None):
    j={'id':['freq',gd,'time'],'size':[1,1,2],'dimension':{
      'freq':{'category':{'index':{'A':0}}},gd:{'category':{'index':{geo:0}}},
      'time':{'category':{'index':{'2024':0,'2025':1}}}},'value':{'0':100.0,'1':105.0}}
    return j,'https://example.test/eurostat/'+ds
# Return two valid annual observations for any World Bank indicator.
def fake_wb(code,indicator):
    return {'raw':2.0,'previous':1.0,'growthPct':100.0,'date':'2025','previousDate':'2024','score':100,'comparison':'previous'},'https://example.test/worldbank/'+indicator
u.euro=fake_euro;u.wb=fake_wb
D=json.load(open('public/data/market-pulse.json'))
assert len(D['europe'])==29 and len(D['emea'])==22
for c in D['europe']:
    out,diag=u.process(c,contracts,True)
    assert set(EUROSTAT).issubset(diag['sourceStatus'])
    assert set(WORLD_BANK).issubset(diag['sourceStatus'])
for c in D['emea']:
    out,diag=u.process(c,contracts,False)
    assert set(WORLD_BANK).issubset(diag['sourceStatus'])
print('OFFLINE_PIPELINE_REGRESSION_OK',len(D['europe']),len(D['emea']),len(EUROSTAT),len(WORLD_BANK))
