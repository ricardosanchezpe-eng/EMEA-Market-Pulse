# EMEA Market Pulse v2.1
Upload all files to the root of the `EMEA-Market-Pulse` repository and select GitHub Actions in Settings > Pages. This build includes the real map, full matrix, methodology, worked calculation, country expansion and zero-score validation. The weekly workflow runs at Monday 07:30 Europe/Madrid using a dual-UTC schedule with a local-time gate.

## Live coverage in v2.2
The weekly collector queries Eurostat with explicit dimensions for construction production, civil engineering, building construction, construction confidence and building permits. It calculates Overall, Transportation and Site Development only when minimum coverage is met. Missing inputs remain null and appear as insufficient data. Waste & Water, Oil & Gas, Mining, Renewables and Agriculture require additional official-source adapters and are not fabricated.

## v2.3 vertical methodology
The build now carries explicit 100%-weighted public-source methodology definitions for Waste & Water, Oil & Gas, Mining, Renewables and Agriculture. The source registry uses Eurostat Water/Agriculture, IRENA, ENTSO-E, World Bank commodity data, EIB open projects and EBRD projects. `update_verticals.py` validates that weights sum to 100 and publishes methodology into the site dataset. These methodology definitions do not fabricate country scores: country values stay insufficient until a source adapter has retrieved and validated observations for that country.
