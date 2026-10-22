from pathlib import Path
s=Path('scripts/refresh_market_trends.py').read_text();u=Path('src/trends-main.jsx').read_text()
for x in ["leading_survey","includedInVerticalAverage","yoyPointChange","excludedRoles","latestMonthlyPeriod","weighted_avg(items,gdp)"]:assert x in s,x
for x in ['pctx(vblock)','GDP-weighted activity YoY change','ch(i.avgYoY,i.displayChangeUnit)']:assert x in u,x
print('V2.36 CONTRACT OK')
