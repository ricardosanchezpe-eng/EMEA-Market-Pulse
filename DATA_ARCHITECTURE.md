# Data Architecture v2.18

## Core rule
A methodology row and a data adapter are separate objects. Every indicator has an explicit contract. A value is published only when the adapter returns at least two comparable observations and the transformation passes validation.

## Adapter states
- `connected`: endpoint/dataset has already passed source verification.
- `candidate`: official structured dataset is configured and tested on every refresh; it becomes visible only for countries with usable observations.
- `pending`: methodology remains visible but no number is fabricated because no stable machine-readable country adapter exists.

## Country-by-country audit
Every refresh produces `coverage-matrix.csv/json`: one row for every universe × country × vertical × indicator. This makes missing values diagnosable as pending, no usable series, or endpoint error.

## Current limitations
Project-pipeline indicators (TEN-T/CEF, EIB/EBRD, national approvals, auctions, storage, mines/tailings) remain pending until a stable and auditable classification adapter is implemented. This package does not invent project values.

## Deployment note
This package replaces `.github/workflows/weekly-refresh.yml`; do not keep a second scheduled refresh workflow. The UI methodology file is generated from the same contracts so collector keys and visible audit rows stay aligned.

## Promotion gate
Before running the production refresh, run **Verify complete data architecture**. It tests all configured Eurostat and World Bank adapters for Germany, Spain, Poland, Saudi Arabia and South Africa, validates latest/previous observations and dates, and produces a vertical-by-vertical report. A candidate source is still not described as connected until this report proves usable comparable observations.
