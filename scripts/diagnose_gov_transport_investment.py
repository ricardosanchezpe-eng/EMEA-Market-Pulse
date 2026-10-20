#!/usr/bin/env python3
import json, urllib.request, urllib.parse, pathlib, time, itertools
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'transport-gov-diagnostic-output'; OUT.mkdir(exist_ok=True)
API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10a_exp'
UA='EMEA-Market-Pulse-Gov-Transport-Diagnostic/1.0'
data=json.load(open(ROOT/'public/data/market-pulse.json'))
countries=data['europe']

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=40) as r:return json.loads(r.read().decode())

def codes(p,dim):
 cat=p.get('dimension',{}).get(dim,{}).get('category',{}); idx=cat.get('index',{}); lab=cat.get('label',{})
 order=idx if isinstance(idx,list) else sorted(idx,key=idx.get) if isinstance(idx,dict) else []
 return [{'code':c,'label':lab.get(c,c)} for c in order]

def find(p,dim,words):
 for x in codes(p,dim):
  if all(w.lower() in x['label'].lower() for w in words): return x['code']
 return None

def count_values(p): return len(p.get('value',{}) or {})
results=[]
for i,c in enumerate(countries,1):
 geo=c['geo']; name=c['country']; base=API+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':8})
 row={'country':name,'geo':geo,'status':'UNKNOWN','baseUrl':base}
 try:
  p=get(base); ids=p.get('id',[]); row['dimensions']=ids; row['baseObservations']=count_values(p)
  row['dimensionCodes']={d:codes(p,d) for d in ids if d in ('unit','sector','cofog99','na_item','freq')}
  filters={}
  if 'freq' in ids: filters['freq']=find(p,'freq',['annual']) or 'A'
  if 'unit' in ids: filters['unit']=find(p,'unit',['million','euro']) or 'MIO_EUR'
  if 'sector' in ids: filters['sector']=find(p,'sector',['general government']) or 'S13'
  if 'cofog99' in ids: filters['cofog99']=find(p,'cofog99',['transport']) or 'GF04'
  if 'na_item' in ids:
   # Test both capital formation family and total expenditure because dimensions differ by release.
   filters['na_item']=find(p,'na_item',['gross','capital','formation']) or find(p,'na_item',['capital','formation']) or 'P5'
  row['resolvedFilters']=filters
  q={'lang':'EN','geo':geo,'lastTimePeriod':8,**filters}; url=API+'?'+urllib.parse.urlencode(q); row['filteredUrl']=url
  fp=get(url); row['filteredObservations']=count_values(fp); row['filteredDimensions']=fp.get('id',[])
  row['status']='PASS' if row['filteredObservations']>=2 else 'NO_COMPARABLE_SERIES'
 except Exception as e:
  row['status']='ERROR'; row['error']=repr(e)
 print(f"[{i:02d}/{len(countries)}] {name}: {row['status']} base={row.get('baseObservations',0)} filtered={row.get('filteredObservations',0)} {row.get('error','')}",flush=True)
 results.append(row)
summary={'PASS':sum(r['status']=='PASS' for r in results),'NO_COMPARABLE_SERIES':sum(r['status']=='NO_COMPARABLE_SERIES' for r in results),'ERROR':sum(r['status']=='ERROR' for r in results)}
out={'generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'dataset':'gov_10a_exp','target':'Government transport investment diagnostic','summary':summary,'results':results}
json.dump(out,open(OUT/'government-transport-investment-diagnostic.json','w'),indent=2)
with open(OUT/'government-transport-investment-diagnostic.md','w') as f:
 f.write('# Government transport investment diagnostic\n\n')
 f.write(f"PASS: {summary['PASS']}  |  NO COMPARABLE: {summary['NO_COMPARABLE_SERIES']}  |  ERRORS: {summary['ERROR']}\n\n")
 f.write('| Country | Status | Base obs | Filtered obs | Error |\n|---|---|---:|---:|---|\n')
 for r in results:f.write(f"| {r['country']} | {r['status']} | {r.get('baseObservations',0)} | {r.get('filteredObservations',0)} | {str(r.get('error','')).replace('|','/')} |\n")
print(json.dumps(summary,indent=2))
# Diagnostic is successful even if some country requests fail; artifact is the result.
