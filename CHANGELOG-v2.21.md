# v2.21 — Full-country indicator connection
- Indicator Intelligence moved above map and matrix.
- Previous value/date and latest value/date visible together.
- Added Eurostat construction employment, construction cost, non-residential permits and fixed-investment adapters.
- Added monthly-to-quarterly fallbacks for construction, employment, costs, permits and mining.
- Every Europe country attempts every configured Eurostat adapter; every Broader EMEA country attempts every configured World Bank adapter.
- Missing observations now retain explicit terminal reasons and datasets tried.
- Added 51-country terminal-status verifier.

## v2.21.1 verification correction
- World Bank adapters now execute for Broader EMEA as well as Europe.
- Every failed or empty World Bank series receives an explicit terminal status and indicator code.
- Added offline regression tests for all 51 countries and all configured adapter terminal states.
