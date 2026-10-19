import json,urllib.request,urllib.parse
u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_copr_m?'+urllib.parse.urlencode({'lang':'EN','geo':'DE','lastTimePeriod':'2'})
r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 EMEA-Market-Pulse-GitHubActions/2.6'});j=json.load(urllib.request.urlopen(r,timeout=120));print('OK dimensions:',j.get('id'),'sizes:',j.get('size'))
