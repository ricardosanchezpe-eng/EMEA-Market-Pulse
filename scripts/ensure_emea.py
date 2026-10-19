import json,pathlib
P=pathlib.Path('public/data/market-pulse.json')
COUNTRIES=[('Saudi Arabia','SA','SAU','682'),('United Arab Emirates','AE','ARE','784'),('Türkiye','TR','TUR','792'),('Israel','IL','ISR','376'),('Egypt','EG','EGY','818'),('South Africa','ZA','ZAF','710'),('Nigeria','NG','NGA','566'),('Algeria','DZ','DZA','012'),('Morocco','MA','MAR','504'),('Ethiopia','ET','ETH','231'),('Kenya','KE','KEN','404'),('Ghana','GH','GHA','288'),('Tanzania','TZ','TZA','834'),('Côte d’Ivoire','CI','CIV','384'),('Angola','AO','AGO','024'),('Kazakhstan','KZ','KAZ','398'),('Qatar','QA','QAT','634'),('Kuwait','KW','KWT','414'),('Oman','OM','OMN','512'),('Bahrain','BH','BHR','048'),('Jordan','JO','JOR','400'),('Tunisia','TN','TUN','788')]
d=json.loads(P.read_text())
old={c['country']:c for c in d.get('emea',[])}
rows=[]
for rank,(n,g,wb,i) in enumerate(COUNTRIES,1):
 c=old.get(n,{'country':n,'geo':g,'wb':wb,'id':i,'overall':None,'transport':None,'site':None,'water':None,'oil':None,'mining':None,'renewables':None,'agriculture':None,'coverage':{},'confidence':{},'indicators':{},'stale':False})
 c.update({'geo':g,'wb':wb,'id':i,'gdpRank':rank});rows.append(c)
d['emea']=rows
P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print('Broader EMEA countries:',len(rows))
