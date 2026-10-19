import json,pathlib,datetime
P=pathlib.Path('public/data/market-pulse.json');M=pathlib.Path('public/data/vertical-methodology.json')
def main():
 d=json.loads(P.read_text(encoding='utf-8'));m=json.loads(M.read_text(encoding='utf-8'))
 d['verticalMethodology']=m
 for v,rows in m.items():
  if sum(x['weight'] for x in rows)!=100: raise ValueError(f'{v} weights do not sum to 100')
 d['methodologyUpdatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 P.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Validated methodology for',', '.join(m))
if __name__=='__main__':main()
