#!/usr/bin/env python3
"""GDP weighting helpers for Harmonised Europe aggregates."""
import json, math, urllib.parse, urllib.request
GDP_DATASET='nama_10_gdp'
GDP_UNIT='CP_MEUR'
GDP_ITEM='B1GQ'
GDP_SOURCE='https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table'
GDP_API='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp'

def weighted_avg(items, weights):
    pairs=[]
    for country,value in items:
        weight=weights.get(country)
        if isinstance(value,(int,float)) and math.isfinite(value) and isinstance(weight,(int,float)) and math.isfinite(weight) and weight>0:
            pairs.append((float(value),float(weight)))
    den=sum(w for _,w in pairs)
    return sum(v*w for v,w in pairs)/den if den else None

def represented_gdp_pct(countries, weights):
    total=sum(float(v) for v in weights.values() if isinstance(v,(int,float)) and math.isfinite(v) and v>0)
    represented=sum(float(weights[c]) for c in set(countries) if c in weights and isinstance(weights[c],(int,float)) and math.isfinite(weights[c]) and weights[c]>0)
    return represented/total*100 if total else None

def _inv(cat):return {int(v):k for k,v in (cat or {}).get('index',{}).items()}
def _decode(n,sizes):
    c=[]
    for s in reversed(sizes):c.append(n%s);n//=s
    return list(reversed(c))

def fetch_gdp_weights(country_to_geo, timeout=90):
    q={'freq':'A','unit':GDP_UNIT,'na_item':GDP_ITEM,'lang':'en','lastTimePeriod':5}
    url=GDP_API+'?'+urllib.parse.urlencode(q)
    req=urllib.request.Request(url,headers={'User-Agent':'EMEA-Market-Pulse-Trends/2.35'})
    with urllib.request.urlopen(req,timeout=timeout) as x:j=json.load(x)
    dims=j['id'];sizes=j['size'];gi=dims.index('geo');ti=dims.index('time')
    geos=_inv(j['dimension']['geo']['category']);times=_inv(j['dimension']['time']['category'])
    by_geo={}
    for k,v in j.get('value',{}).items():
        try:v=float(v)
        except:continue
        c=_decode(int(k),sizes);geo=geos.get(c[gi]);year=times.get(c[ti])
        if geo and year:by_geo.setdefault(geo,[]).append((int(str(year)[:4]),v))
    weights={};years={}
    for country,geo in country_to_geo.items():
        vals=sorted(by_geo.get(geo,[]),reverse=True)
        if vals:years[country],weights[country]=vals[0]
    used_year=max(years.values()) if years else None
    return weights,{'dataset':GDP_DATASET,'unit':GDP_UNIT,'item':GDP_ITEM,'sourceUrl':GDP_SOURCE,'apiUrl':url,'latestYear':used_year,'countryYears':years}
