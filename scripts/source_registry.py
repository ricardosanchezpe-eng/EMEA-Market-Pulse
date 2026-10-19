"""Executable source contracts for EMEA Market Pulse.
Statuses:
  connected: machine-readable adapter is implemented and audited.
  candidate: official structured dataset is known; workflow tests it and only publishes on valid observations.
  pending: no stable machine-readable country adapter; methodology stays visible but no value is fabricated.
"""
EUROSTAT = {
 'construction_production': {'dataset':'sts_copr_m','filters':{'nace_r2':'F'},'frequency':'monthly','status':'connected'},
 'civil_output': {'dataset':'sts_copr_m','filters':{'nace_r2':'F42'},'frequency':'monthly','status':'connected'},
 'building_output': {'dataset':'sts_copr_m','filters':{'nace_r2':'F41'},'frequency':'monthly','status':'connected'},
 'building_permits': {'dataset':'teiis550','filters':{},'frequency':'monthly','status':'connected'},
 'rail_freight': {'dataset':'rail_go_typepas','filters':{},'frequency':'annual_or_quarterly','status':'connected'},
 'road_freight': {'dataset':'road_go_ta_tott','filters':{},'frequency':'annual_or_quarterly','status':'connected'},
 'port_freight': {'dataset':'mar_go_qm','filters':{},'frequency':'quarterly','status':'connected'},
 'construction_confidence': {'dataset':'ei_bsbu_m_r2','filters':{},'frequency':'monthly_balance','status':'connected'},
 'wastewater_treatment': {'dataset':'sdg_06_20','filters':{},'frequency':'annual','status':'candidate'},
 'water_stress_eu': {'dataset':'sdg_06_60','filters':{},'frequency':'annual','status':'candidate'},
 'waste_generation': {'dataset':'env_wasgen','filters':{},'frequency':'biennial','status':'candidate'},
 'waste_treatment': {'dataset':'env_wastrt','filters':{},'frequency':'biennial','status':'candidate'},
 'mining_production': {'dataset':'sts_inpr_m','filters':{'nace_r2':'B'},'frequency':'monthly','status':'candidate'},
 'renewable_share_eu': {'dataset':'nrg_ind_ren','filters':{},'frequency':'annual','status':'candidate'},
 'agri_output_prices': {'dataset':'apri_pi_outa','filters':{},'frequency':'annual','status':'candidate'},
}
WORLD_BANK = {
 'water_stress': 'ER.H2O.FWST.ZS', 'water_access':'SH.H2O.SMDW.ZS',
 'renewable_share':'EG.FEC.RNEW.ZS', 'renewable_power':'EG.ELC.RNEW.ZS',
 'agri_growth':'NV.AGR.TOTL.KD.ZG', 'agri_share':'NV.AGR.TOTL.ZS',
 'oil_rents':'NY.GDP.PETR.RT.ZS', 'gas_rents':'NY.GDP.NGAS.RT.ZS',
 'mineral_rents':'NY.GDP.MINR.RT.ZS', 'resource_rents':'NY.GDP.TOTL.RT.ZS'
}
