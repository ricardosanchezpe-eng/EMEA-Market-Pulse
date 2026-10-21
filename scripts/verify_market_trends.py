#!/usr/bin/env python3
import json,math,pathlib,sys
p=pathlib.Path(__file__).resolve().parents[1]/'public/data/market-trends.json';d=json.load(open(p));e=[]
for r in d.get('records',[]):
 s=r.get('series',[]);f=r.get('actualFrequency');expected=24 if f=='monthly' else 8 if f=='quarterly' else 6
 if len(s)!=expected:e.append((r['country'],r['indicator'],'window',len(s),expected))
 if any(x.get('value')==0 for x in s if x.get('value') is None):e.append(('null-as-zero',r['country'],r['indicator']))
 if r.get('ageMonths',999)<=6 and f in ('monthly','quarterly') and not r.get('sourceUrl'):e.append(('url',r['country'],r['indicator']))
 if r.get('ytdMatched') and '/' not in r['ytdMatched']:e.append(('ytd',r['country'],r['indicator']))
if not d.get('regionalIndicators'):e.append('no regional indicators')
if not d.get('verticals'):e.append('no verticals')
print('records',len(d.get('records',[])),'regional',len(d.get('regionalIndicators',[])),'verticals',len(d.get('verticals',{})),'errors',len(e))
if e:print(e[:30]);sys.exit(2)
print('MARKET_TRENDS_VERIFICATION_OK')
