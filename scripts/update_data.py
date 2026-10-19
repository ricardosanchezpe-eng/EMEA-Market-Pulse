import json,pathlib,datetime,time,traceback
from config import WB
from adapters import eurostat_cube,decode_nace,yoy_index,wb_series,wb_change
P=pathlib.Path('public/data/market-pulse.json')
def weighted(parts,mincov=.4):
 live=[(s,w) for s,w in parts if s is not None];cov=sum(w for s,w in live)
 return ((round(sum(s*w for s,w in live)/cov) if cov>=mincov else None),round(cov*100))
def put(c,key,score,raw,date,url,status='live'):c['indicators'][key]={'score':score,'raw':raw,'date':date,'url':url,'status':status}
def main():
 d=json.loads(P.read_text());log=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for c in d['europe']:
  c.setdefault('indicators',{});errors=[]
  try:
   cube,url=eurostat_cube(c['geo']);f=yoy_index(decode_nace(cube,'F'));f41=yoy_index(decode_nace(cube,'F41'));f42=yoy_index(decode_nace(cube,'F42'))
   put(c,'construction_production',f,None,now,url);put(c,'building_output',f41,None,now,url);put(c,'civil_output',f42,None,now,url)
  except Exception as e:f=f41=f42=None;errors.append('Eurostat construction: '+repr(e))
  w={}
  for k,ind in WB.items():
   try:
    rows,u=wb_series(c['wb'],ind);level=k in ('renewable_share','renewable_electricity','water_stress','drinking_water','agri_share','oil_rents','gas_rents','mineral_rents');s,raw,date=wb_change(rows,3,level);w[k]=s;put(c,k,s,raw,date,u)
   except Exception as e:w[k]=None;errors.append(k+': '+repr(e))
  c['overall'],co=weighted([(f,.55),(f42,.25),(f41,.20)],.45)
  c['transport'],ct=weighted([(f42,.80)],.40)
  c['site'],cs=weighted([(f41,.60)],.40)
  c['water'],cw=weighted([(w.get('water_stress'),.20),(w.get('drinking_water'),.15)],.25)
  c['renewables'],cr=weighted([(w.get('renewable_share'),.20),(w.get('renewable_electricity'),.15)],.25)
  c['agriculture'],ca=weighted([(w.get('agri_growth'),.20),(w.get('agri_share'),.10)],.20)
  c['oil'],cog=weighted([(w.get('oil_rents'),.20),(w.get('gas_rents'),.15)],.20)
  c['mining'],cm=weighted([(w.get('mineral_rents'),.20)],.20)
  c['coverage']={'overall':co,'transport':ct,'site':cs,'water':cw,'renewables':cr,'agriculture':ca,'oil':cog,'mining':cm}
  c['confidence']={k:('High' if v>=80 else 'Medium' if v>=55 else 'Low' if v>=40 else 'Insufficient') for k,v in c['coverage'].items()}
  c['stale']=bool(errors);log.append({'country':c['country'],'scores':{k:c[k] for k in ['overall','transport','site','water','oil','mining','renewables','agriculture']},'errors':errors})
  time.sleep(.1)
 d['generatedAt']=now;d['pipelineStatus']=f"Live refresh complete. Countries with scores: overall {sum(x['overall'] is not None for x in d['europe'])}, water {sum(x['water'] is not None for x in d['europe'])}, oil & gas {sum(x['oil'] is not None for x in d['europe'])}, mining {sum(x['mining'] is not None for x in d['europe'])}, renewables {sum(x['renewables'] is not None for x in d['europe'])}, agriculture {sum(x['agriculture'] is not None for x in d['europe'])}.";d['diagnostics']=log;P.write_text(json.dumps(d,ensure_ascii=False,indent=2));pathlib.Path('public/data/refresh-diagnostics.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
