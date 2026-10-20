#!/usr/bin/env python3
import json,csv,urllib.request,urllib.parse,time,pathlib,math
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'transport-verification-output';OUT.mkdir(exist_ok=True)
API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
UA='EMEA-Market-Pulse-Transport-Infrastructure-Verification/1.0'
DATASETS=[
 ('road_infra_expenditure','road_ec_invest','Annual road infrastructure expenditure','investment'),
 ('rail_infra_expenditure','rail_ec_expend','Annual railway infrastructure expenditure','investment'),
 ('government_transport_investment','gov_10a_exp','Government transport gross capital formation','investment'),
 ('motorway_network','road_if_motorwa','Total motorway network length','structural'),
 ('rail_network','rail_if_line_tr','Total railway line length','structural'),
 ('inland_waterway_expenditure','iww_ec_invest','Inland-waterway infrastructure expenditure','investment'),
]

def get_json(url,retries=2):
    err=None
    for i in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=35) as r:return json.loads(r.read().decode())
        except Exception as e:
            err=repr(e);time.sleep(1.5*(i+1))
    raise RuntimeError(err)

def decode(payload):
    ids=payload.get('id',[]); sizes=payload.get('size',[]); vals=payload.get('value',{}) or {}
    dims=[]
    for dim in ids:
        cat=payload['dimension'][dim]['category']; idx=cat.get('index',{}); labels=cat.get('label',{})
        if isinstance(idx,list): codes=idx
        else: codes=sorted(idx,key=idx.get)
        dims.append([(c,labels.get(c,c)) for c in codes])
    import itertools
    rows=[]
    for pos,combo in enumerate(itertools.product(*dims)):
        v=vals.get(str(pos),vals.get(pos))
        if v is None:continue
        r={'value':v}
        for dim,(code,label) in zip(ids,combo):r[dim]=code;r[dim+'_label']=label
        rows.append(r)
    return rows,ids

def comparable(rows):
    if not rows:return None
    # group by all dimensions except time; pick the preferred/latest well-defined series supplied by selector.
    groups={}
    for r in rows:
        key=tuple((k,r[k]) for k in r if not k.endswith('_label') and k not in ('value','time'))
        groups.setdefault(key,[]).append(r)
    best=None
    for key,rr in groups.items():
        rr=sorted(rr,key=lambda x:x.get('time',''))
        if len(rr)<2:continue
        cand=(rr[-1].get('time',''),len(rr),rr,key)
        if best is None or cand[:2]>best[:2]:best=cand
    if not best:return None
    rr=best[2];a,b=rr[-2],rr[-1]
    prev=float(a['value']); latest=float(b['value']); change=None if prev==0 else (latest/prev-1)*100
    return {'previous':prev,'previousDate':a.get('time'),'latest':latest,'latestDate':b.get('time'),'change':change,'selectedDimensions':{k:v for k,v in best[3]}}

def find_code(payload,dim,needles):
    cat=payload.get('dimension',{}).get(dim,{}).get('category',{});labels=cat.get('label',{})
    for code,label in labels.items():
        norm=str(label).lower()
        if all(n.lower() in norm for n in needles):return code
    return None

def url(dataset,geo,filters=None,last=12):
    q={'lang':'EN','geo':geo,'lastTimePeriod':last};q.update(filters or {})
    return API+dataset+'?'+urllib.parse.urlencode(q)

def query_candidate(key,dataset,geo):
    # First fetch country cube, then resolve exact human-readable dimension labels where useful.
    raw_url=url(dataset,geo,last=12); p=get_json(raw_url); ids=p.get('id',[])
    filters={}
    if dataset in ('road_ec_invest','rail_ec_expend','iww_ec_invest'):
        if 'unit' in ids: filters['unit']=find_code(p,'unit',['million','euro']) or 'MIO_EUR'
        if 'expend' in ids:
            # Prefer infrastructure investment, otherwise infrastructure expenditure.
            filters['expend']=find_code(p,'expend',['investment','infrastructure']) or find_code(p,'expend',['expenditure','infrastructure']) or 'INF'
    elif dataset=='gov_10a_exp':
        if 'unit' in ids: filters['unit']=find_code(p,'unit',['million','euro']) or 'MIO_EUR'
        if 'sector' in ids: filters['sector']=find_code(p,'sector',['general government']) or 'S13'
        if 'cofog99' in ids: filters['cofog99']=find_code(p,'cofog99',['transport']) or 'GF045'
        if 'na_item' in ids: filters['na_item']=find_code(p,'na_item',['gross','capital','formation']) or 'P5'
    elif dataset=='road_if_motorwa':
        if 'unit' in ids: filters['unit']=find_code(p,'unit',['kilometre']) or 'KM'
        if 'tra_infr' in ids: filters['tra_infr']=find_code(p,'tra_infr',['motorway']) or find_code(p,'tra_infr',['motorways'])
    elif dataset=='rail_if_line_tr':
        if 'unit' in ids: filters['unit']=find_code(p,'unit',['kilometre']) or 'KM'
        if 'tra_infr' in ids: filters['tra_infr']=find_code(p,'tra_infr',['total'])
        if 'n_tracks' in ids: filters['n_tracks']=find_code(p,'n_tracks',['total'])
    clean={k:v for k,v in filters.items() if v}
    qurl=url(dataset,geo,clean,last=12); q=get_json(qurl); rows,_=decode(q); obs=comparable(rows)
    return obs,qurl,clean,len(rows)

data=json.load(open(ROOT/'public/data/market-pulse.json'))
countries=[c for c in data['europe']]
results=[]
for i,c in enumerate(countries,1):
    print(f"[{i:02d}/{len(countries)}] {c['country']}",flush=True)
    for key,dataset,label,role in DATASETS:
        try:
            obs,qurl,filters,n=query_candidate(key,dataset,c['geo'])
            status='PASS' if obs else 'NO_COMPARABLE_SERIES'
            row={'country':c['country'],'geo':c['geo'],'indicator':key,'label':label,'dataset':dataset,'role':role,'status':status,'rows':n,'url':qurl,'filters':filters}
            if obs:row.update(obs)
        except Exception as e:
            row={'country':c['country'],'geo':c['geo'],'indicator':key,'label':label,'dataset':dataset,'role':role,'status':'ERROR','error':repr(e)}
        results.append(row)
summary={}
for key,dataset,label,role in DATASETS:
    rr=[r for r in results if r['indicator']==key];summary[key]={'label':label,'dataset':dataset,'role':role,'pass':sum(r['status']=='PASS' for r in rr),'total':len(rr),'coveragePct':round(100*sum(r['status']=='PASS' for r in rr)/len(rr),1),'errors':sum(r['status']=='ERROR' for r in rr)}
out={'generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'countries':len(countries),'summary':summary,'results':results}
json.dump(out,open(OUT/'transport-infrastructure-verification.json','w'),indent=2)
fields=['country','geo','indicator','label','dataset','role','status','latest','latestDate','previous','previousDate','change','rows','filters','url','error']
with open(OUT/'transport-infrastructure-verification.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();
 for r in results:
  x=dict(r);x['filters']=json.dumps(x.get('filters',{}));w.writerow(x)
with open(OUT/'transport-infrastructure-verification.md','w') as f:
 f.write('# Transportation infrastructure candidate verification\n\n')
 f.write('| Indicator | Dataset | Passed | Coverage | Errors |\n|---|---|---:|---:|---:|\n')
 for k,v in summary.items():f.write(f"| {v['label']} | `{v['dataset']}` | {v['pass']}/{v['total']} | {v['coveragePct']}% | {v['errors']} |\n")
print(json.dumps(summary,indent=2))
if any(v['errors'] for v in summary.values()): raise SystemExit(2)
