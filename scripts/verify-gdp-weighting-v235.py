#!/usr/bin/env python3
from gdp_weighting import weighted_avg,represented_gdp_pct
w={'Large':80,'Small':20}
assert abs(weighted_avg([('Large',-4),('Small',20)],w)-0.8)<1e-9
assert abs(weighted_avg([('Large',-4),('Missing',99)],w)+4)<1e-9
assert abs(represented_gdp_pct(['Large'],w)-80)<1e-9
assert weighted_avg([('Missing',5)],w) is None
print('V2.35 GDP WEIGHTING UNIT TEST OK')
