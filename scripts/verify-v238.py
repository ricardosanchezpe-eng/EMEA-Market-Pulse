from pathlib import Path
s=Path('src/trends-main.jsx').read_text();c=Path('src/trends-styles.css').read_text()
for x in ['function EuropeDrawer','EVIDENCE DETAIL · HARMONISED EUROPE','Country contributions','Raw index levels are never averaged across countries','setEuropeDrawer(i)','Open official Eurostat Data Browser','gdpWeights={data.gdpWeights||{}}','GDP weight*','Contribution']:
 assert x in s,x
assert '.europe-evidence-hit' in c
print('V2.38 EUROPE EVIDENCE CONTRACT OK')
