import json,pathlib
from source_registry import EUROSTAT,WORLD_BANK
D=json.load(open('public/data/market-pulse.json'));countries=D.get('europe',[])+D.get('emea',[])
expected_eu=set(EUROSTAT)|set(WORLD_BANK);expected_em=set(WORLD_BANK)
issues=[]
for c in D.get('europe',[]):
 status=c.get('sourceStatus',{})
 missing=sorted(expected_eu-set(status))
 if missing:issues.append({'country':c['country'],'missingTerminalStatus':missing})
for c in D.get('emea',[]):
 status=c.get('sourceStatus',{})
 missing=sorted(expected_em-set(status))
 if missing:issues.append({'country':c['country'],'missingTerminalStatus':missing})
report={'countries':len(countries),'europe':len(D.get('europe',[])),'emea':len(D.get('emea',[])),'configuredEurostatAdapters':len(EUROSTAT),'configuredWorldBankAdapters':len(WORLD_BANK),'issues':issues}
pathlib.Path('public/data/full-coverage-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));raise SystemExit(2 if issues else 0)
