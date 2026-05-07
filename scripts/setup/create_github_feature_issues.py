"""
create_github_feature_issues.py
Creates all 21 FEATURE (epic) issues for PROJECT INTELLIGENT via gh CLI.
Usage: python scripts/setup/create_github_feature_issues.py
Requires: gh CLI authenticated (gh auth login)
"""

import subprocess
import tempfile
import os
import sys

REPO = "biteberry/project-intelligent"
GH   = r"C:\Program Files\GitHub CLI\gh.exe"

# Milestone titles (gh CLI accepts title strings for --milestone)
M = {
    0: "M0: Phase 0 - Architecture and Sign-Off",
    1: "M1: Phase 1.1 - Environment Provisioning",
    2: "M2: Phase 1.2 - Data Ingestion Layer",
    3: "M3: Phase 1.3 - Feature Engineering Layer",
    4: "M4: Phase 1.4 - ML Training Pipeline",
    5: "M5: Phase 1.5 - Inference and Signals",
    6: "M6: Phase 1.6 - Monitoring and Operations",
    7: "M7: Phase 1.7 - Acceptance Testing and Go-Live",
}

ISSUES = [
    {
        "title": "[FEATURE-001] Architecture Phase Closure",
        "labels": "type:feature,phase:0-setup,comp:docs,priority:critical",
        "milestone": M[0],
        "body": """\
## Description
Close the architecture design phase. Sign off PRD v1.0, create Phase 0 gate audit record, ensure all docs are committed to GitHub.

## PRD Reference
All FRs (design prerequisite for all implementation)

## Architecture Reference
- docs/architecture/ (all 14 docs)
- docs/prd/PRD_v1.0.md
- docs/adr/ (ADR-001 to ADR-005)

## Child Stories
- [ ] Phase 0 gate audit document
- [ ] PRD v1.0 sign-off and approval
- [ ] configs/position_sizing.yaml creation
- [ ] All architecture docs pushed to GitHub (DONE)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Phase 0 gate audit record exists with date and approval
- [ ] configs/position_sizing.yaml committed to repo
- [ ] All 14 architecture docs + 9 analysis docs + 5 ADRs + PRD in main branch

## Notes
Per doc 07 Guardrail G4: no phase begins before previous phase exit criteria are fully documented and signed off.
"""
    },
    {
        "title": "[FEATURE-002] Environment Provisioning",
        "labels": "type:feature,phase:0-setup,comp:infra,priority:critical",
        "milestone": M[1],
        "body": """\
## Description
Provision all AWS infrastructure, local PostgreSQL, GitHub Actions CI, and external API keys before any pipeline code is written.

## PRD Reference
NFR-01 (Cost $0), NFR-05 (Security), NFR-07 (Portability)

## Architecture Reference
- docs/architecture/12_aws_cost_model.md
- docs/architecture/13_github_repository_structure.md
- docs/adr/ADR-003-database-decision.md
- docs/adr/ADR-004-backup-and-failover.md

## Child Stories
- [ ] AWS IAM roles and least-privilege policies
- [ ] AWS S3 buckets: landing / bronze / silver / gold / artifacts
- [ ] AWS DynamoDB tables: predictions + audit
- [ ] AWS EventBridge rules: daily 21:00 UTC + weekly Sunday
- [ ] AWS Lambda SSM dispatcher function
- [ ] AWS CloudWatch alarms and SNS email alerts
- [ ] AWS Secrets Manager: API key storage
- [ ] AWS Glue Catalog for Iceberg
- [ ] EC2 t2.micro: Python environment setup
- [ ] Local PostgreSQL schema (ADR-003)
- [ ] GitHub Actions CI: lint + test runner
- [ ] Finnhub API key in Secrets Manager

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Zero API keys in any committed file
- [ ] Billing alarm fires at USD 0.10 threshold
- [ ] EC2 reachable via SSM Session Manager (no direct SSH)

## Notes
Least-privilege IAM only. No wildcard * permissions. All secrets in AWS Secrets Manager. EC2 access via SSM only per NFR-05.
"""
    },
    {
        "title": "[FEATURE-003] NSE OHLCV Daily Ingestion (J01)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:critical",
        "milestone": M[2],
        "body": """\
## Description
Daily OHLCV collection for all active universe symbols via yfinance. Writes immutable raw Parquet to Bronze layer partitioned by date/symbol.

## PRD Reference
FR-01

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — OHLCV Bronze Schema section

## Child Stories
- [ ] yfinance OHLCV fetcher with .NS suffix support
- [ ] Bronze Parquet writer (partitioned by date/symbol)
- [ ] Retry logic for failed symbol fetches (max 3 attempts)
- [ ] Ticker suffix routing table (.NS / .BO / none)
- [ ] DynamoDB job audit record write for J01
- [ ] SNS alert on J01 failure

## Acceptance Criteria
- [ ] All child stories closed
- [ ] >=95% active universe symbols have OHLCV in Bronze by 23:59 UTC on any trading day
- [ ] Both unadjusted OHLCV and adjusted close stored
- [ ] market_context field set on every row (.NS = india, no suffix = us)

## Notes
Bronze is immutable — append only, no overwrites. Medallion layer: Landing → Bronze (this job) → Silver → Gold.
"""
    },
    {
        "title": "[FEATURE-004] NSE Delivery Percentage Ingestion (J01)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:critical",
        "milestone": M[2],
        "body": """\
## Description
Daily NSE bhav copy delivery percentage data. Free public CSV from NSE archives. Joined to OHLCV in Silver layer by symbol and date.

## PRD Reference
FR-02

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — NSE Bhav Copy Ingestion section

## Child Stories
- [ ] NSE bhav copy CSV downloader (daily URL pattern)
- [ ] Delivery pct Bronze writer (partitioned by date)
- [ ] Join delivery pct to OHLCV by symbol + date in Silver layer
- [ ] Market holiday detection (no false failure alert when bhav not published)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] delivery_pct non-null for >=90% of NSE Silver rows on any trading day
- [ ] delivery_pct = null for market_context=us (expected, not an error)

## Notes
URL pattern: https://archives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv
NSE-only feature. Feeds Group 4 delivery % features in Gold layer.
"""
    },
    {
        "title": "[FEATURE-005] Quarterly Fundamentals Ingestion (J02)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:high",
        "milestone": M[2],
        "body": """\
## Description
Quarterly fundamentals via yfinance: P/E, margins, debt, cash flow, institutional ownership. Refreshed within 7 days of each symbol's earnings announcement.

## PRD Reference
FR-03

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — Fundamentals Bronze Schema section

## Child Stories
- [ ] yfinance .info fundamentals fetcher
- [ ] yfinance .financials / .balance_sheet / .cashflow fetcher
- [ ] Bronze fundamentals Parquet writer (partitioned by quarter)
- [ ] Staleness check: skip if last fetch < 30 days old
- [ ] Institutional ownership fields extraction (institutional_ownership_pct, insider_ownership_pct, short_ratio)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Every active symbol has fundamentals record no older than 95 days in Silver
- [ ] All 17 required fields populated or explicitly null (not missing/absent)

## Notes
Refresh triggered within 7 days of earnings date (cross-reference FEATURE-007 earnings calendar).
"""
    },
    {
        "title": "[FEATURE-006] India Macro Data Ingestion (J03)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:high",
        "milestone": M[2],
        "body": """\
## Description
Weekly India macro indicators: RBI repo rate, India 10Y/2Y bond yields, India VIX (^INDIAVIX), Nifty 50 (^NSEI). Feeds Group 6 regime descriptor features in Gold layer.

## PRD Reference
FR-04

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — India Macro section
- docs/architecture/10_feature_engineering_architecture.md — Group 6

## Child Stories
- [ ] RBI repo rate fetcher (RBI public portal)
- [ ] India 10Y and 2Y bond yield fetcher
- [ ] India VIX daily fetcher (yfinance ^INDIAVIX)
- [ ] Nifty 50 daily fetcher (yfinance ^NSEI)
- [ ] Bronze macro Parquet writer (partitioned by date)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] India macro fields non-stale (<=35 days) for all market_context=india symbols at every Gold build

## Notes
market_context switch: india = RBI + ^INDIAVIX + ^NSEI. us = FRED + ^VIX + ^GSPC.
Feature names are identical — only the data sources differ. This is the core India-first design.
"""
    },
    {
        "title": "[FEATURE-007] Earnings Calendar Ingestion (J03)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:high",
        "milestone": M[2],
        "body": """\
## Description
Weekly NSE board meeting dates (quarterly result announcement dates). Computes days_to_next_earnings and earnings_blackout_flag which is a non-overridable serving gate.

## PRD Reference
FR-05

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — Quarterly Results Calendar Ingestion section
- docs/architecture/10_feature_engineering_architecture.md — Group 7

## Child Stories
- [ ] NSE board meeting dates scraper (weekly, public NSE URL)
- [ ] Bronze earnings calendar Parquet writer
- [ ] Silver enrichment: days_to_next_earnings and days_since_last_earnings fields
- [ ] earnings_blackout_flag = 1 within +-2 trading days of result date

## Acceptance Criteria
- [ ] All child stories closed
- [ ] >=80% of active NSE symbols have known next earnings date in Silver at any point in the quarter
- [ ] earnings_blackout_flag correctly set within +-2 trading days of result date

## Notes
Earnings blackout is NON-OVERRIDABLE serving gate (Guardrail G9). Prediction suppressed regardless of model confidence during blackout window.
"""
    },
    {
        "title": "[FEATURE-008] Corporate Actions Ingestion (J03)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:high",
        "milestone": M[2],
        "body": """\
## Description
Weekly corporate action ex-dates: bonus shares, stock splits, dividends, rights issues. Rows on ex-dates are flagged and automatically excluded from ML model training.

## PRD Reference
FR-06

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — Corporate Actions Ingestion section

## Child Stories
- [ ] yfinance .actions fetcher (bonus, split, dividend)
- [ ] Bronze corporate actions Parquet writer
- [ ] Silver enrichment: corporate_action_flag computation
- [ ] Training exclusion gate: is_valid_row = false on ex-dates

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Zero ex-date rows in model training dataset without exclusion flag
- [ ] corporate_action_type field populated: bonus / split / dividend / rights

## Notes
Without this feature, the model trains on -50% returns on bonus ex-dates and learns a false negative signal. Critical data quality gate.
"""
    },
    {
        "title": "[FEATURE-009] India Macro Event Calendar (J03)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:medium",
        "milestone": M[2],
        "body": """\
## Description
Annual maintenance of RBI MPC announcement dates and Union Budget date. Drives macro_event_blackout_flag for rate-sensitive sectors within 2 trading days of each event.

## PRD Reference
FR-07

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — India Macro Event Calendar section
- docs/architecture/10_feature_engineering_architecture.md — Group 7

## Child Stories
- [ ] RBI MPC and Budget date YAML calendar file (annual update task, April each year)
- [ ] Silver enrichment: days_to_next_macro_event field
- [ ] macro_event_blackout_flag = 1 for rate-sensitive sectors within 2 trading days

## Acceptance Criteria
- [ ] All child stories closed
- [ ] macro_event_blackout_flag correctly set for rate-sensitive sectors within 2 days of each RBI MPC and Budget date
- [ ] Calendar stored in configs/ not hardcoded

## Notes
Rate-sensitive sectors: Banking, NBFC, Real Estate, Auto. RBI publishes next annual MPC schedule each April. Budget date known ~60 days in advance.
"""
    },
    {
        "title": "[FEATURE-010] NSE Circuit Band Ingestion (J03)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:high",
        "milestone": M[2],
        "body": """\
## Description
Weekly NSE circuit band reference file fetch. Determines upper/lower circuit limits per symbol. Circuit flags are a non-overridable serving gate that suppresses predictions.

## PRD Reference
FR-13 (circuit breaker gate)

## Architecture Reference
- docs/architecture/08_data_ingestion_architecture.md — NSE Circuit Band section

## Child Stories
- [ ] NSE circuit band reference file auto-fetcher (weekly)
- [ ] Bronze circuit bands Parquet writer
- [ ] Silver enrichment: upper_circuit_flag and lower_circuit_flag per symbol per day

## Acceptance Criteria
- [ ] All child stories closed
- [ ] upper_circuit_flag and lower_circuit_flag correctly set for all NSE symbols in Silver
- [ ] Both flags = null for market_context=us (expected, not error)

## Notes
NSE-only. A symbol hitting circuit limit cannot be traded at market price. Prediction must be suppressed at inference serving gate.
"""
    },
    {
        "title": "[FEATURE-011] Silver Layer Transformation (J04)",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:silver,priority:critical",
        "milestone": M[2],
        "body": """\
## Description
Bronze to Silver transformation. Cleans, joins, and validates all Bronze sources into unified Apache Iceberg Silver tables. Sets market_context field on every row.

## PRD Reference
FR-01 through FR-07 (all ingestion FRs produce Bronze; Silver consumes all of them)

## Architecture Reference
- docs/architecture/03_data_architecture_medallion.md — Silver layer section
- docs/architecture/08_data_ingestion_architecture.md

## Child Stories
- [ ] Bronze to Silver transformation job runner (reads all Bronze sources)
- [ ] Schema validation on Silver write: reject bad rows and log rejections
- [ ] Iceberg table management for Silver (PyIceberg + AWS Glue Catalog)
- [ ] market_context field propagation on every Silver row
- [ ] Data quality audit: null check, row count comparison Bronze vs Silver

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Every Silver row has market_context populated (india or us)
- [ ] Iceberg snapshot ID recorded in DynamoDB audit for every Silver write
- [ ] Schema validation rejects and logs bad rows rather than silently skipping

## Notes
Silver is the single source of truth for all downstream jobs. Gold reads only from Silver, never directly from Bronze. Iceberg enables time travel and snapshot reproducibility.
"""
    },
    {
        "title": "[FEATURE-012] Feature Engineering Groups 1-5 (J04)",
        "labels": "type:feature,phase:1-core,comp:feature-eng,layer:gold,priority:critical",
        "milestone": M[3],
        "body": """\
## Description
Compute Gold layer feature groups 1 through 5: price returns, rolling statistics, technical indicators (including 52-week high/low, RS vs index, support/resistance), volume behaviour (including NSE delivery %), and volatility features.

## PRD Reference
FR-08

## Architecture Reference
- docs/architecture/10_feature_engineering_architecture.md — Groups 1-5

## Child Stories
- [ ] Group 1: price return features (1d / 5d / 10d / 21d / 63d)
- [ ] Group 2: rolling statistical features (mean / std / skew / kurtosis)
- [ ] Group 3: technical indicators (RSI-14, MACD, ATR-14, Bollinger Bands, SMA-10/50)
- [ ] Group 3: 52-week high/low proximity (pct_from_52w_high, pct_from_52w_low, near_52w_high_flag)
- [ ] Group 3: RS vs index — market_context-aware (rs_vs_index_63d, rs_rank_63d — Nifty 50 for india, S&P 500 for us)
- [ ] Group 3: support and resistance levels (swing_high_20d, swing_low_20d, pivot_high, pivot_low)
- [ ] Group 4: volume behaviour (OBV, A/D line, MFI-14, CLV, buy_pressure_pct)
- [ ] Group 4: NSE delivery pct features (delivery_pct_ratio, delivery_volume_spike_flag) — india only
- [ ] Group 5: volatility features (realized_vol, Garman-Klass, vol_ratio)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] All Group 1-5 features non-null for symbols with >=252 days Bronze history
- [ ] Delivery pct features null for market_context=us (expected, not error)
- [ ] Zero look-ahead bias violations (features use only data available at prediction time T)

## Notes
252 days minimum history required for 52-week and RS features. Symbols below threshold get null for those features only — they remain in the universe.
"""
    },
    {
        "title": "[FEATURE-013] Feature Engineering Groups 6-10 (J04)",
        "labels": "type:feature,phase:1-core,comp:feature-eng,layer:gold,priority:critical",
        "milestone": M[3],
        "body": """\
## Description
Compute Gold layer feature groups 6 through 10: regime descriptors (market_context-aware sources), calendar/earnings/corporate actions/macro event features, candlestick patterns, institutional positioning, India regulatory risk.

## PRD Reference
FR-08

## Architecture Reference
- docs/architecture/10_feature_engineering_architecture.md — Groups 6-10

## Child Stories
- [ ] Group 6: regime descriptor features — india uses RBI/IndiaVIX/Nifty; us uses FRED/CBOE/SP500; same field names both sides
- [ ] Group 7: calendar features (day_of_week, month, quarter, is_month_end, is_quarter_end)
- [ ] Group 7: earnings event features (days_to_next_earnings, earnings_blackout_flag, pre_earnings_zone_flag, earnings_cycle_position)
- [ ] Group 7: corporate action flag propagation from Silver
- [ ] Group 7: macro_event_blackout_flag propagation from Silver (India only)
- [ ] Group 8: candlestick patterns (hammer, inverted hammer, shooting star, bullish/bearish engulfing, doji)
- [ ] Group 9: institutional positioning (institutional_ownership_pct, institutional_ownership_change_qoq, short_ratio)
- [ ] Group 10: India regulatory risk (promoter_pledging_pct, fii_change_qoq, circuit_consecutive_5d) — null for us
- [ ] Gold Iceberg table writer (PyIceberg + AWS Glue Catalog)
- [ ] Look-ahead bias audit script

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Group 10 features null for market_context=us (expected)
- [ ] Gold Iceberg snapshot ID in DynamoDB audit for every Gold write
- [ ] Look-ahead bias audit script passes with zero violations

## Notes
Group 6 is the core India-first design: identical feature names, different data sources controlled by market_context field.
"""
    },
    {
        "title": "[FEATURE-014] Market Regime Detection (J05)",
        "labels": "type:feature,phase:1-core,comp:feature-eng,layer:gold,priority:high",
        "milestone": M[3],
        "body": """\
## Description
Daily market regime classification per market_context (india / us). Drives composite scoring weights and ML theory activation. 3-day stability buffer prevents single-day flips.

## PRD Reference
FR-09

## Architecture Reference
- docs/architecture/10_feature_engineering_architecture.md — Group 6
- docs/analysis/regime_analysis_architecture.md
- docs/analysis/theories_and_algorithm_playbook.md — Section 5 Theory Activation

## Child Stories
- [ ] Regime classifier: bull_trend / bear_trend / sideways / high_vol
- [ ] 3-day stability buffer (no single-day regime transition recorded)
- [ ] Regime label written to Gold layer and DynamoDB
- [ ] market_context-aware index and VIX source routing

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Valid regime label for both india and us market_context on every trading day
- [ ] No regime transition recorded from a single-day signal (3-day minimum)

## Notes
Regimes: bull_trend = index above 50d MA with positive slope; bear_trend; sideways = low slope both directions; high_vol = VIX above threshold configured in configs/regime_config.yaml.
"""
    },
    {
        "title": "[FEATURE-015] ML Training Pipeline (J06)",
        "labels": "type:feature,phase:1-core,comp:ml-pipeline,layer:gold,priority:critical",
        "milestone": M[4],
        "body": """\
## Description
Weekly model training on Gold layer snapshot. XGBoost / LightGBM baseline. Walk-forward validation only (no random splits). Promotion gate: >=2% directional accuracy improvement over current production model.

## PRD Reference
FR-10, FR-11

## Architecture Reference
- docs/architecture/04_model_strategy_and_serving.md
- docs/architecture/05_validation_backtesting_and_risk.md
- docs/architecture/11_label_engineering_architecture.md

## Child Stories
- [ ] Gold snapshot loader with walk-forward time-series splitter
- [ ] Label computation: label_direction_1d (1-day forward price direction)
- [ ] Corporate action row exclusion: is_valid_row = false rows removed from training set
- [ ] XGBoost / LightGBM baseline trainer
- [ ] Walk-forward out-of-sample directional accuracy evaluation
- [ ] Model metadata writer (feature_version, label_version, Gold snapshot_id, training_date)
- [ ] Model promotion gate: >=2% accuracy improvement vs current production model
- [ ] Model artifact writer to S3 artifacts/ prefix
- [ ] MLflow / SQLite experiment tracker

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Trained model achieves >=55% directional accuracy on OOS walk-forward data before promotion eligibility
- [ ] No model promoted without >=2% improvement threshold or documented manual override with logged justification
- [ ] Model metadata fully populated for every training run

## Notes
India backtesting cost: 0.50% round-trip (STT + exchange + GST + stamp + slippage). US: 0.10%. market_context field drives cost assumption per symbol row.
"""
    },
    {
        "title": "[FEATURE-016] Universe Selection and Opportunity Scanner (J07)",
        "labels": "type:feature,phase:1-core,comp:universe,priority:critical",
        "milestone": M[5],
        "body": """\
## Description
Weekly universe scoring (30 active symbols, hard cap 50) using composite score across fundamental / technical / quant / sentiment dimensions. Daily opportunity scanner across ~700 NSE symbols with manipulation risk scoring.

## PRD Reference
FR-15, FR-16, FR-17

## Architecture Reference
- docs/architecture/02_universe_selection_pre_landing.md
- docs/analysis/market_microstructure_analysis_architecture.md — Manipulation Risk Score section

## Child Stories
- [ ] Fundamental scoring module (25% weight)
- [ ] Technical scoring module (35% weight)
- [ ] Quant scoring module (25% weight)
- [ ] Sentiment scoring using Finnhub bullishPercent / bearishPercent (5% weight)
- [ ] Risk penalty module (10%) integrated with manipulation_risk_score
- [ ] Regime-conditional weight table (weights shift per bull/bear/sideways/high_vol)
- [ ] Hard eligibility gates: liquidity floor, price floor, manipulation_risk_score < 0.60
- [ ] Cap-tier quota: large / mid / small cap allocation ratios from configs/
- [ ] Universe snapshot writer to S3 (weekly, every Monday before daily pipeline runs)
- [ ] Opportunity scanner: ~700 NSE symbols daily scan (volume >5x avg, price >5%, 52w high breach, OBV pre-advance)
- [ ] manipulation_risk_score computation (6 components: OBV slope, vol concentration, fundamental presence, float risk, price reversal)
- [ ] Scanner watchlist writer to S3 (daily)

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Valid universe snapshot in S3 every Monday before daily pipeline runs
- [ ] Zero symbols with manipulation_risk_score >= 0.60 in active universe
- [ ] Every medium-risk (0.30-0.59) symbol inclusion has logged justification

## Notes
Scanner output is for human review only — no automatic universe addition. Universe hard cap = 50 symbols. Target = 30 active symbols.
"""
    },
    {
        "title": "[FEATURE-017] Daily Batch Inference and Trade Signals (J08)",
        "labels": "type:feature,phase:1-core,comp:inference,priority:critical",
        "milestone": M[5],
        "body": """\
## Description
Daily batch predictions for all active universe symbols. Applies 5 serving gates. Computes trade signals with entry / stop loss / take profit / position size. Writes all predictions (including suppressions) to DynamoDB.

## PRD Reference
FR-12, FR-13, FR-14

## Architecture Reference
- docs/architecture/04_model_strategy_and_serving.md — Prediction Serving Gate table + Position Sizing section

## Child Stories
- [ ] Gold feature loader for active universe symbols
- [ ] Model artifact loader from S3
- [ ] Prediction batch runner (1-day direction + confidence score)
- [ ] Gate 1: earnings_blackout_flag = 1 → suppress (NON-OVERRIDABLE Guardrail G9)
- [ ] Gate 2: upper_circuit_flag or lower_circuit_flag = 1 → suppress (NSE only)
- [ ] Gate 3: macro_event_blackout_flag = 1 → suppress for rate-sensitive sectors
- [ ] Gate 4: confidence below configured floor threshold → suppress
- [ ] Gate 5: model trained on snapshot older than 30 days → suppress
- [ ] Trade signal: entry = T+1 open reference, stop = entry minus 1x ATR_14, target = entry plus 2x ATR_14
- [ ] Position size = (portfolio_value x risk_pct_per_trade) / ATR_stop_distance (configs/position_sizing.yaml)
- [ ] DynamoDB writer: symbol, date, horizon, market_context, predicted_direction, confidence, suppression_reason, entry, stop, target, position_size

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Prediction or suppression record for 100% of active symbols in DynamoDB by 23:59 UTC on every trading day
- [ ] Zero predictions served for symbols meeting any gate condition
- [ ] All suppressions stored in DynamoDB with reason code (never silently dropped)

## Notes
Max hold = 5 trading days. Risk/reward = 1:2 (1x ATR stop, 2x ATR target). Platform generates signals only — never places orders (Guardrail G1).
"""
    },
    {
        "title": "[FEATURE-018] Finnhub News Sentiment Ingestion",
        "labels": "type:feature,phase:1-core,comp:ingestion,layer:bronze,priority:medium",
        "milestone": M[5],
        "body": """\
## Description
Daily news sentiment via Finnhub free API (60 calls/min rate limit). Extracts bullishPercent / bearishPercent / buzz per symbol. Feeds the 5% sentiment weight in universe composite scoring.

## PRD Reference
FR-12 (sentiment input to features), FR-15 (5% sentiment weight in universe score)

## Architecture Reference
- docs/adr/ADR-005-news-api-decision.md
- docs/architecture/08_data_ingestion_architecture.md — Sentiment section

## Child Stories
- [ ] Finnhub API client with 60-call/min rate limiter (1 second pause after every 60 calls)
- [ ] bullishPercent / bearishPercent / buzz extraction per symbol
- [ ] Bronze sentiment Parquet writer (partitioned by date)
- [ ] Silver sentiment enrichment joined to symbol rows by symbol + date

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Finnhub API key in AWS Secrets Manager only — never in committed code
- [ ] Rate limiter prevents HTTP 429 errors in production
- [ ] 30 symbols x 2 calls = 60 calls completes within 65 seconds

## Notes
ADR-005: Finnhub accepted as primary sentiment source. RSS feed as fallback if Finnhub unavailable. 30 symbols x 2 calls fits exactly within one 60-call/min window.
"""
    },
    {
        "title": "[FEATURE-019] Monitoring and Observability (J09)",
        "labels": "type:feature,phase:1-core,comp:monitoring,priority:high",
        "milestone": M[6],
        "body": """\
## Description
Full observability stack: CloudWatch alarms for AWS spend, DynamoDB limits, S3 storage, pipeline job failures, and model staleness. SNS email alerts within 15 minutes. DynamoDB audit trail for all pipeline runs and manual overrides. 365-day retention.

## PRD Reference
FR-19, FR-20

## Architecture Reference
- docs/architecture/06_platform_mlops_observability_security.md
- docs/architecture/14_operations_and_automation_guide.md — Section 5 Governance Triggers

## Child Stories
- [ ] CloudWatch alarm: AWS billing at USD 0.10 threshold
- [ ] CloudWatch alarm: DynamoDB RCU/WCU at 80% of free-tier limit
- [ ] CloudWatch alarm: S3 storage at 80% of 5GB free-tier
- [ ] CloudWatch alarm: any J01-J09 pipeline job failure
- [ ] CloudWatch alarm: active production model older than 30 days
- [ ] SNS email subscription setup and delivery test
- [ ] DynamoDB job audit schema and writer (run_id, job_id, status, symbol_counts, duration_sec, timestamp)
- [ ] Manual override log writer (universe change / model rollback / medium-risk approval)
- [ ] 365-day audit retention policy configuration

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Platform owner receives SNS alert within 15 minutes of any threshold breach
- [ ] Full pipeline history reconstructable from DynamoDB for any date in past 365 days
- [ ] Billing alarm tested and confirmed to fire before any real AWS charges

## Notes
Billing alarm at USD 0.10 is the earliest possible warning before actual charges. Target is USD 0.00 spend throughout the 12-month free-tier period.
"""
    },
    {
        "title": "[FEATURE-020] Local Backup and Failover",
        "labels": "type:feature,phase:1-core,comp:data-store,priority:high",
        "milestone": M[6],
        "body": """\
## Description
Daily-synchronized local backup of all S3 data and DynamoDB to local PostgreSQL on the platform owner's laptop. Full pipeline must be runnable locally within 2 hours of failover activation per ADR-004.

## PRD Reference
FR-18

## Architecture Reference
- docs/adr/ADR-003-database-decision.md
- docs/adr/ADR-004-backup-and-failover.md

## Child Stories
- [ ] S3 to local daily sync script (Bronze / Silver / Gold + model artifacts)
- [ ] DynamoDB to PostgreSQL daily sync script
- [ ] PostgreSQL failover schema validation test
- [ ] Local pipeline environment smoke test script
- [ ] Failover runbook document referencing ADR-004

## Acceptance Criteria
- [ ] All child stories closed
- [ ] Local PostgreSQL never more than 2 calendar days behind DynamoDB
- [ ] Failover drill completed within 2 hours end-to-end
- [ ] Sync scripts run on schedule automatically (not manual)

## Notes
ADR-003: PostgreSQL already installed on local Windows laptop. ADR-004: failover target is 2 hours from activation to fully operational local pipeline. Sync includes model artifacts — not just data.
"""
    },
    {
        "title": "[FEATURE-021] End-to-End Acceptance Testing and Go-Live",
        "labels": "type:feature,phase:1-core,comp:monitoring,priority:critical",
        "milestone": M[7],
        "body": """\
## Description
Final acceptance testing phase. All 10 Definition of Done criteria from PRD v1.0 Section 9 must pass before Phase 1 is declared complete and live trade signals are used.

## PRD Reference
Section 9 — Definition of Done (all 10 criteria)

## Architecture Reference
- docs/prd/PRD_v1.0.md — Section 9

## Child Stories
- [ ] DoD-01: Full pipeline runs end-to-end without manual intervention on 5 consecutive trading days
- [ ] DoD-02: >=95% OHLCV symbol coverage confirmed on those 5 days
- [ ] DoD-03: delivery_pct non-null for >=90% NSE Silver rows confirmed
- [ ] DoD-04: At least one model trained, promoted, and serving predictions in production
- [ ] DoD-05: All 5 serving gates tested with known suppression test cases (one test per gate)
- [ ] DoD-06: Trade signals include entry / stop / target / position_size for 100% of served predictions
- [ ] DoD-07: AWS billing alarm test fired and confirmed (simulated USD 0.10 threshold event)
- [ ] DoD-08: Local PostgreSQL sync verified <= 2 calendar days behind DynamoDB
- [ ] DoD-09: Failover drill completed within 2 hours (per ADR-004)
- [ ] DoD-10: Full pipeline history for any date in past 30 days reconstructable from DynamoDB audit records

## Acceptance Criteria
- [ ] ALL 10 DoD child stories closed with evidence
- [ ] Zero open priority:critical or priority:high bugs
- [ ] Platform owner sign-off recorded in GitHub

## Notes
Phase 1 is NOT complete until all 10 DoD items pass. No partial go-live. After go-live, the Sunday 5-step review routine begins per doc 14 Section 6.
"""
    },
]


def create_issue(issue):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(issue["body"])
        tmp_path = f.name
    try:
        result = subprocess.run(
            [GH, "issue", "create",
             "--repo", REPO,
             "--title", issue["title"],
             "--label", issue["labels"],
             "--milestone", str(issue["milestone"]),
             "--body-file", tmp_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"  OK  {issue['title']}")
            print(f"      {url}")
        else:
            print(f"  FAIL {issue['title']}")
            print(f"       {result.stderr.strip()}")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    print(f"Creating {len(ISSUES)} Feature issues on {REPO} ...\n")
    for i, issue in enumerate(ISSUES, 1):
        print(f"[{i:02d}/{len(ISSUES)}] Creating...", end=" ", flush=True)
        create_issue(issue)
    print(f"\nDone. Verify at: https://github.com/{REPO}/issues")
