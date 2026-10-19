import json,urllib.request,urllib.parse,datetime,sys
UA={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-Source-Audit/2.13','Accept':'application/json'}
TESTS=[('Eurostat construction','sts_copr_m'),('Eurostat building permits','teiis550'),('Eurostat rail freight','rail_go_typepas'),('Eurostat road freight','road_go_ta_tott'),('Eurostat maritime freight','mar_go_qm'),('Eurostat construction confidence','ei_bsbu_m_r2')]
WB=[('Water stress','ER.H2O.FWST.ZS'),('Water access','SH.H2O.SMDW.ZS'),('Renewable share','EG.FEC.RNEW.ZS'),('Renewable electricity','EG.ELC.RNEW.ZS'),('Agriculture growth','NV.AGR.TOTL.KD.ZG'),('Agriculture share','NV.AGR.TOTL.ZS'),('Oil rents','NY.GDP.PETR.RT.ZS'),('Gas rents','NY.GDP.NGAS.RT.ZS'),('Mineral rents','NY.GDP.MINR.RT.ZS')]
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120) as r:return json.load(r)
def main():
 rows=[]
 for name,ds in TESTS:
  url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+ds+'?'+urllib.parse.urlencode({'lang':'EN','geo':'ES','lastTimePeriod':'25'})
  try:j=get(url);n=len(j.get('value',{}));rows.append({'source':name,'dataset':ds,'status':'PASS' if n else 'NO_VALUES','observations':n,'dimensions':j.get('id',[]),'url':url})
  except Exception as e:rows.append({'source':name,'dataset':ds,'status':'ERROR','observations':0,'error':repr(e),'url':url})
 for name,ind in WB:
  url=f'https://api.worldbank.org/v2/country/ESP/indicator/{ind}?format=json&per_page=70'
  try:j=get(url);v=[x for x in (j[1] if len(j)>1 else []) if x.get('value') is not None];rows.append({'source':'World Bank '+name,'dataset':ind,'status':'PASS' if len(v)>=2 else 'INSUFFICIENT','observations':len(v),'latest':v[0] if v else None,'url':url})
  except Exception as e:rows.append({'source':'World Bank '+name,'dataset':ind,'status':'ERROR','observations':0,'error':repr(e),'url':url})
 out={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testCountry':'Spain','results':rows};open('source-verification.json','w').write(json.dumps(out,indent=2));print(json.dumps(out,indent=2));bad=[x for x in rows if x['status'] in ('ERROR','NO_VALUES')];sys.exit(2 if bad else 0)
if __name__=='__main__':main()
