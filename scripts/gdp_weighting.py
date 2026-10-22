import json,math,urllib.parse,urllib.request
GDP_SOURCE='https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table'
def weighted_avg(items,w):
 p=[(float(v),float(w[c])) for c,v in items if isinstance(v,(int,float)) and math.isfinite(v) and c in w and w[c]>0];d=sum(x[1] for x in p);return sum(v*x for v,x in p)/d if d else None
def represented_gdp_pct(countries,w):
 d=sum(w.values());return sum(w[c] for c in set(countries) if c in w)/d*100 if d else None
def fetch_gdp_weights(ctg,timeout=90):
 q={'freq':'A','unit':'CP_MEUR','na_item':'B1GQ','lang':'en','lastTimePeriod':5};url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp?'+urllib.parse.urlencode(q)
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EMEA-Market-Pulse/2.36'}),timeout=timeout) as x:j=json.load(x)
 inv=lambda c:{int(v):k for k,v in c.get('index',{}).items()};dims=j['id'];sizes=j['size'];gi=dims.index('geo');ti=dims.index('time');geos=inv(j['dimension']['geo']['category']);times=inv(j['dimension']['time']['category'])
 def dec(n):
  a=[]
  for s in reversed(sizes):a.append(n%s);n//=s
  return list(reversed(a))
 bg={}
 for k,v in j.get('value',{}).items():
  c=dec(int(k));g=geos.get(c[gi]);t=times.get(c[ti]);
  if g and t:bg.setdefault(g,[]).append((int(str(t)[:4]),float(v)))
 w={};years={}
 for country,g in ctg.items():
  a=sorted(bg.get(g,[]),reverse=True)
  if a:years[country],w[country]=a[0]
 return w,{'dataset':'nama_10_gdp','unit':'CP_MEUR','item':'B1GQ','sourceUrl':GDP_SOURCE,'latestYear':max(years.values()) if years else None,'countryYears':years}
