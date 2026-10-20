import json,pathlib
P=pathlib.Path('public/data/market-pulse.json')
EU=[('Germany','DE','DEU','276'),('France','FR','FRA','250'),('Italy','IT','ITA','380'),('Spain','ES','ESP','724'),('Netherlands','NL','NLD','528'),('Switzerland','CH','CHE','756'),('Poland','PL','POL','616'),('Belgium','BE','BEL','056'),('Ireland','IE','IRL','372'),('Sweden','SE','SWE','752'),('Austria','AT','AUT','040'),('Norway','NO','NOR','578'),('Denmark','DK','DNK','208'),('Romania','RO','ROU','642'),('Czechia','CZ','CZE','203'),('Portugal','PT','PRT','620'),('Finland','FI','FIN','246'),('Greece','EL','GRC','300'),('Hungary','HU','HUN','348'),('Slovakia','SK','SVK','703'),('Bulgaria','BG','BGR','100'),('Croatia','HR','HRV','191'),('Luxembourg','LU','LUX','442'),('Lithuania','LT','LTU','440'),('Slovenia','SI','SVN','705'),('Latvia','LV','LVA','428'),('Estonia','EE','EST','233'),('Cyprus','CY','CYP','196'),('Malta','MT','MLT','470')]
EM=[('Saudi Arabia','SA','SAU','682'),('United Arab Emirates','AE','ARE','784'),('Türkiye','TR','TUR','792'),('Israel','IL','ISR','376'),('Egypt','EG','EGY','818'),('South Africa','ZA','ZAF','710'),('Nigeria','NG','NGA','566'),('Algeria','DZ','DZA','012'),('Morocco','MA','MAR','504'),('Ethiopia','ET','ETH','231'),('Kenya','KE','KEN','404'),('Ghana','GH','GHA','288'),('Tanzania','TZ','TZA','834'),('Côte d’Ivoire','CI','CIV','384'),('Angola','AO','AGO','024'),('Kazakhstan','KZ','KAZ','398'),('Qatar','QA','QAT','634'),('Kuwait','KW','KWT','414'),('Oman','OM','OMN','512'),('Bahrain','BH','BHR','048'),('Jordan','JO','JOR','400'),('Tunisia','TN','TUN','788')]
SCORES=['overall','transport','site','water','oil','mining','renewables','agriculture']
def base(n,g,w,i,r):
 x={'country':n,'geo':g,'wb':w,'id':i,'gdpRank':r,'coverage':{},'confidence':{},'indicators':{},'sourceStatus':{},'stale':False};x.update({k:None for k in SCORES});return x
def merged(old,spec):
 old_by={x.get('country'):x for x in old if isinstance(x,dict)};out=[]
 for r,(n,g,w,i) in enumerate(spec,1):
  x=base(n,g,w,i,r);x.update(old_by.get(n,{}));x.update(country=n,geo=g,wb=w,id=i,gdpRank=r);out.append(x)
 return out
try:d=json.loads(P.read_text())
except Exception:d={}
d['europe']=merged(d.get('europe',[]),EU);d['emea']=merged(d.get('emea',[]),EM);d.setdefault('diagnostics',[]);d['pipelineStatus']='Country universe ready; refresh in progress.'
P.parent.mkdir(parents=True,exist_ok=True);P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(f"Europe {len(d['europe'])}; Broader EMEA {len(d['emea'])}; total {len(d['europe'])+len(d['emea'])}")
