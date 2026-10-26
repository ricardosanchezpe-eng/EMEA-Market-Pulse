#!/usr/bin/env python3
import json,math,pathlib,sys
p=pathlib.Path(__file__).resolve().parents[1]/'public/data/market-trends.json';d=json.load(open(p));e=[]
for r in d.get('records',[]):
 s=r.get('series',[]);f=r.get('actualFrequency');expected=24 if f=='monthly' else 8 if f=='quarterly' else 6
 if len(s)!=expected:e.append((r['country'],r['indicator'],'window',len(s),expected))
 if any(x.get('value')==0 for x in s if x.get('value') is None):e.append(('null-as-zero',r['country'],r['indicator']))
 if r.get('ageMonths',999)<=6 and f in ('monthly','quarterly') and not r.get('sourceUrl'):e.append(('url',r['country'],r['indicator']))
 if r.get('ytdMatched') and '/' not in r['ytdMatched']:e.append(('ytd',r['country'],r['indicator']))
if len(d.get('records',[]))<350:e.append(('record_count_too_low',len(d.get('records',[]))))

import re
for r in d.get('records',[]):
 if r.get('actualFrequency')!=r.get('preferredFrequency'):e.append(('frequency_fallback_published',r.get('country'),r.get('indicator'),r.get('preferredFrequency'),r.get('actualFrequency')))
 f=r.get('actualFrequency');per=str(r.get('latestPeriod') or '')
 if f=='monthly' and not re.fullmatch(r'\d{4}-\d{2}',per):e.append(('monthly_period_invalid',r.get('country'),r.get('indicator'),per))
 if f=='quarterly' and not re.fullmatch(r'\d{4}-Q[1-4]',per):e.append(('quarterly_period_invalid',r.get('country'),r.get('indicator'),per))
 if f=='annual' and not re.fullmatch(r'\d{4}',per):e.append(('annual_period_invalid',r.get('country'),r.get('indicator'),per))
 if 'api/dissemination' in str(r.get('sourceUrl','')):e.append(('human_source_url_is_api',r.get('country'),r.get('indicator')))
if not d.get('regionalIndicators'):e.append('no regional indicators')
if not d.get('verticals'):e.append('no verticals')
print('records',len(d.get('records',[])),'regional',len(d.get('regionalIndicators',[])),'verticals',len(d.get('verticals',{})),'errors',len(e))
if e:print(e[:30]);sys.exit(2)
print('MARKET_TRENDS_VERIFICATION_OK')
