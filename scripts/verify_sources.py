import json,urllib.request,urllib.parse,datetime,sys
UA={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-Source-Audit/1.0','Accept':'application/json'}
TESTS=[
 ('Eurostat construction','sts_copr_m','ES'),('Eurostat building permits','teiis550','ES'),('Eurostat rail freight','rail_go_typepas','ES'),('Eurostat road freight','road_go_ta_tott','ES'),('Eurostat maritime freight','mar_m_go_qm_cwhd','ES'),('Eurostat construction confidence','ei_bsbu_m_r2','ES')]
WB=[('Water stress','ER.H2O.FWST.ZS'),('Water access','SH.H2O.SMDW.ZS'),('Renewable share','EG.FEC.RNEW.ZS'),('Renewable electricity','EG.ELC.RNEW.ZS'),('Agriculture growth','NV.AGR.TOTL.KD.ZG'),('Agriculture share','NV.AGR.TOTL.ZS'),('Oil rents','NY.GDP.PETR.RT.ZS'),('Gas rents','NY.GDP.NGAS.RT.ZS'),('Mineral rents','NY.GDP.MINR.RT.ZS')]
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120) as r:return json.load(r)
def main():
 rows=[]
 for name,ds,geo in TESTS:
  url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':geo,'lastTimePeriod':'25'})
  try:
   j=get(url);count=len(j.get('value',{}));rows.append({'source':name,'dataset':ds,'status':'PASS' if count else 'NO_VALUES','observations':count,'dimensions':j.get('id',[]),'url':url})
  except Exception as e:rows.append({'source':name,'dataset':ds,'status':'ERROR','observations':0,'error':repr(e),'url':url})
 for name,ind in WB:
  url=f'https://api.worldbank.org/v2/country/ESP/indicator/{ind}?format=json&per_page=70'
  try:
   j=get(url);values=[x for x in (j[1] if isinstance(j,list) and len(j)>1 else []) if x.get('value') is not None];rows.append({'source':'World Bank '+name,'dataset':ind,'status':'PASS' if len(values)>=2 else 'INSUFFICIENT','observations':len(values),'latest':values[0] if values else None,'url':url})
  except Exception as e:rows.append({'source':'World Bank '+name,'dataset':ind,'status':'ERROR','observations':0,'error':repr(e),'url':url})
 out={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testCountry':'Spain','results':rows}
 open('source-verification.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 with open('source-verification.md','w') as f:
  f.write('# EMEA Market Pulse source verification\n\n| Source | Dataset | Status | Observations |\n|---|---|---:|---:|\n')
  for r in rows:f.write(f"| {r['source']} | `{r['dataset']}` | {r['status']} | {r['observations']} |\n")
 print(json.dumps(out,indent=2))
 failed=[r for r in rows if r['status'] in ('ERROR','NO_VALUES')]
 if failed:sys.exit(2)
if __name__=='__main__':main()
