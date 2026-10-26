from pathlib import Path
import ast
s=Path('scripts/refresh_market_trends.py').read_text();u=Path('src/trends-main.jsx').read_text();v=Path('scripts/verify_market_trends.py').read_text();ast.parse(s)
for x in ["r.get('actualFrequency')==r.get('preferredFrequency')","databrowser/view/{r['dataset']}/default/table?lang=en","'retrievalUrl':url","'schemaVersion':'2.37'"]:assert x in s,x
for x in ['frequency_fallback_published','monthly_period_invalid','quarterly_period_invalid','annual_period_invalid','human_source_url_is_api']:assert x in v,x
assert 'Open official Eurostat Data Browser' in u
print('V2.37 FREQUENCY + HUMAN SOURCE CONTRACT OK')
