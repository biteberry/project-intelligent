## Description
Transform raw Bronze-layer data through Silver (cleaned, validated) to Gold
(feature-engineered). Covers 10 feature groups and market regime detection.

## PRD Reference
PRD Â§4 â€” Feature engineering requirements

## Architecture Reference
docs/architecture/05_feature_engineering.md
docs/architecture/06_data_schema.md

## Child Features
- [x] #11 â€” [FEATURE-011] Silver Layer Transformation (J04)
- [x] #12 â€” [FEATURE-012] Feature Engineering Groups 1-5 (J04)
- [x] #13 â€” [FEATURE-013] Feature Engineering Groups 6-10 (J04)
- [x] #14 â€” [FEATURE-014] Market Regime Detection (J05)

## Acceptance Criteria
- [x] Silver layer passes null/outlier validation suite
- [x] All 10 feature groups computed and stored in Gold
- [x] Market regime labels back-tested for coherence

## Notes
Gold layer is the training input to EPIC-004.
