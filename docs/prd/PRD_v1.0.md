# Product Requirements Document (PRD)
## PROJECT INTELLIGENT — Stock Market Prediction Platform
**Version:** 1.0
**Date:** 2026-05-07
**Author:** Platform Owner
**Status:** Draft — Pending Phase 0 Sign-Off

---

## 1. Product Vision

PROJECT INTELLIGENT is a personal stock market prediction platform that uses machine learning to generate daily swing trade signals for Indian NSE/BSE stocks, with secondary support for US-listed equities.

The platform ingests market data, financial fundamentals, macroeconomic indicators, and news sentiment every trading day, processes them through a multi-layer data pipeline, and produces actionable buy signals with defined entry, stop loss, and profit target levels — all without requiring paid data services or cloud spend beyond the AWS free tier.

The platform owner reviews a small set of system outputs every Sunday and acts on trade signals at their own discretion. The system never places trades automatically.

**The core problem it solves:** Individual investors lack the data infrastructure, analytical depth, and systematic discipline to consistently identify high-probability swing trade setups. This platform provides institutional-grade analysis at zero ongoing cost.

---

## 2. Target User

| Attribute | Detail |
| --- | --- |
| **Who** | Single individual investor and platform owner |
| **Background** | Platform Engineer — comfortable with technology, not a professional trader |
| **Primary market** | NSE/BSE Indian equities (focus) |
| **Secondary market** | US-listed equities (future expansion) |
| **Trading style** | Swing trading — hold positions 1 to 5 trading days |
| **Capital base** | Personal investment capital (amount not disclosed in this document) |
| **Risk tolerance** | Disciplined — willing to accept defined losses in exchange for systematic process |
| **Time available** | 30–60 minutes per week for system review; not available for intraday monitoring |
| **Goal** | Generate consistent positive returns above Nifty 50 benchmark on a risk-adjusted basis |

---

## 3. Functional Requirements

Each requirement is numbered, uniquely identified, and testable. Every requirement maps to one or more architecture documents.

---

### FR-01 — Daily Market Data Collection
**The system must collect daily OHLCV (Open, High, Low, Close, Volume) data for all active universe symbols every trading day after market close.**

- Covers NSE-listed stocks (suffix `.NS`) and US-listed stocks (no suffix).
- Must include adjusted close price for split and dividend corrections.
- Must store both unadjusted OHLCV (for audit) and adjusted close (for calculations).
- Must retry failed symbol fetches up to 3 times before skipping and alerting.

**Acceptance Criteria:** On any given trading day, ≥95% of active universe symbols have a new OHLCV record in Bronze by 23:59 UTC.

---

### FR-02 — NSE Delivery Percentage Collection
**The system must collect NSE bhav copy delivery percentage data for all NSE-listed universe symbols every trading day.**

- Source: NSE archives bhav copy CSV (free, no API key).
- Fields required: total traded quantity, delivery quantity, delivery percentage.
- Must be joined to the corresponding OHLCV record by symbol and date.

**Acceptance Criteria:** Delivery percentage field is non-null for ≥90% of NSE symbol rows in Silver on any trading day.

---

### FR-03 — Quarterly Fundamental Data Collection
**The system must collect financial fundamental data for all active universe symbols on a quarterly cadence.**

- Includes: P/E ratio, revenue, net income, EPS, gross/operating/net margins, total debt, total equity, debt-to-equity, current ratio, ROE, operating cash flow, free cash flow, market cap, sector, industry, institutional ownership %, insider ownership %, short ratio.
- Source: yfinance `.info`, `.financials`, `.balance_sheet`, `.cashflow`.
- Must be refreshed within 7 days of each symbol's earnings announcement date.

**Acceptance Criteria:** Every active universe symbol has a fundamental record no older than 95 days in the Silver layer.

---

### FR-04 — Macroeconomic Data Collection (India)
**The system must collect Indian macroeconomic indicators on a weekly cadence.**

- Indicators: RBI repo rate, India 10Y government bond yield, India 2Y government bond yield, India CPI, India VIX (daily), Nifty 50 index (daily).
- Sources: RBI public data portal, yfinance for India VIX (`^INDIAVIX`) and Nifty 50 (`^NSEI`).

**Acceptance Criteria:** India macro fields are non-stale (≤35 days old) for all Indian market_context symbols at every Gold build.

---

### FR-05 — Earnings Calendar Collection
**The system must collect upcoming quarterly result announcement dates (board meeting dates) for all NSE-listed universe symbols.**

- Source: NSE corporate filings board meetings page (free, public).
- Must be refreshed weekly every Sunday.
- Must expose `days_to_next_earnings` and `days_since_last_earnings` fields on every Silver row.

**Acceptance Criteria:** ≥80% of active NSE universe symbols have a known next earnings date populated in Silver at any point in the quarter.

---

### FR-06 — Corporate Actions Detection
**The system must detect and flag corporate action ex-dates (bonus shares, stock splits, dividend ex-dates, rights issues) for all universe symbols.**

- Source: yfinance `.actions` endpoint + NSE corporate calendar.
- Any row where a corporate action ex-date falls on the record date must have `corporate_action_flag = 1`.
- Rows with `corporate_action_flag = 1` must be excluded from ML model training automatically.

**Acceptance Criteria:** Zero corporate action ex-date rows appear in the model training dataset without the exclusion flag.

---

### FR-07 — India Macro Event Calendar
**The system must maintain a reference calendar of RBI MPC announcement dates and Union Budget dates.**

- Updated once per year (RBI publishes annual MPC schedule in April; Budget date known ~60 days in advance).
- Must expose `days_to_next_macro_event` and `macro_event_blackout_flag` on Silver rows for Indian symbols.

**Acceptance Criteria:** `macro_event_blackout_flag` is correctly set to 1 for rate-sensitive sector symbols within 2 trading days of each RBI MPC announcement and Budget date.

---

### FR-08 — Feature Engineering (10 Feature Groups)
**The system must compute all 10 feature groups for every active universe symbol on every trading day and store them in the Gold layer.**

Feature groups:
1. Price return features (1d, 5d, 10d, 21d, 63d)
2. Rolling statistical features (mean, std, skew, kurtosis)
3. Technical indicators (RSI-14, MACD, ATR-14, Bollinger Bands, SMA-10/50, 52-week high/low proximity, relative strength vs Nifty 50, support/resistance levels)
4. Volume behaviour (OBV, A/D line, MFI-14, CLV, buy pressure %, delivery % features — NSE only)
5. Volatility features (realized vol, Garman-Klass, vol ratio)
6. Regime descriptor features (index return, VIX, yield spread, macro rate, regime label — market_context-aware)
7. Calendar and earnings event features (day of week, month, earnings proximity, blackout flags, corporate action flag, macro event blackout)
8. Candlestick pattern features (hammer, inverted hammer, shooting star, bullish/bearish engulfing, doji)
9. Institutional positioning features (institutional ownership %, QoQ change, insider %, short ratio)
10. India regulatory risk features (promoter pledging %, FII/DII change, circuit breaker flags — NSE only)

**Acceptance Criteria:** Every Gold row for a symbol with ≥252 days of Bronze history contains non-null values for all 10 feature groups (subject to market_context applicability). Zero look-ahead bias violations detected by the Gold build audit.

---

### FR-09 — Market Regime Detection
**The system must classify the current market regime for each market_context (india / us) on every trading day.**

- Regime labels: `bull_trend`, `bear_trend`, `sideways`, `high_vol`.
- Detection based on index trend slope, moving average structure, VIX level, and breadth proxies.
- Regime label must persist for a minimum of 3 consecutive trading days before a transition is recorded (stability buffer).

**Acceptance Criteria:** A valid, non-stale regime label exists for both `india` and `us` market contexts on every trading day. No regime transition is recorded from a single-day signal.

---

### FR-10 — ML Model Training (Weekly)
**The system must train a direction classification model weekly on the latest Gold snapshot.**

- Primary target: `label_direction_1d` (1-day forward direction).
- Algorithm family: gradient boosting (XGBoost or LightGBM) as the baseline.
- Walk-forward validation only — no random splits.
- Must record feature_version, label_version, Gold snapshot ID, and training date in model metadata.

**Acceptance Criteria:** Trained model achieves ≥55% directional accuracy on out-of-sample walk-forward data before it is eligible for promotion. Model metadata is fully populated for every training run.

---

### FR-11 — Model Promotion Gate
**The system must automatically compare a newly trained model to the current production model before promotion.**

- New model is promoted only if out-of-sample directional accuracy exceeds the current production model by ≥2 percentage points.
- Failed promotion is logged; the previous model continues serving.
- The platform owner may manually override promotion (with logged justification).

**Acceptance Criteria:** No model is promoted to serving without passing the ≥2% accuracy improvement threshold or documented manual approval.

---

### FR-12 — Daily Batch Inference (Prediction Generation)
**The system must generate a 1-day direction prediction with confidence score for every active universe symbol every trading day.**

- Predictions are stored in DynamoDB with: symbol, date, horizon, cap_tier, market_context, predicted_direction, confidence, suppression_reason.
- Suppressed predictions (see FR-13) are stored with suppression reason — not silently dropped.

**Acceptance Criteria:** On every trading day, predictions or suppression records exist for 100% of active universe symbols in DynamoDB by 23:59 UTC.

---

### FR-13 — Prediction Serving Gates (Hard Blocks)
**The system must automatically suppress non-actionable predictions before they are served. The following are non-overridable hard gates:**

| Gate | Condition | Action |
| --- | --- | --- |
| Earnings blackout | `earnings_blackout_flag = 1` (results within 2 trading days) | Suppress prediction |
| Circuit breaker | `upper_circuit_flag = 1` OR `lower_circuit_flag = 1` (NSE only) | Suppress prediction |
| Macro event blackout | `macro_event_blackout_flag = 1` for rate-sensitive sectors | Suppress prediction |
| Confidence floor | Model confidence below configured threshold | Suppress prediction |
| Model staleness | Model trained on snapshot older than 30 days | Suppress prediction |

**Acceptance Criteria:** Zero predictions are served to the platform owner for symbols that meet any gate condition. All suppressions are logged with reason in DynamoDB.

---

### FR-14 — Trade Signal Output (Entry, Stop, Target)
**Every non-suppressed prediction must include the associated trade execution parameters.**

- Entry: market open of T+1.
- Stop loss: entry − (1 × ATR_14 at T).
- Take profit: entry + (2 × ATR_14 at T).
- Maximum hold: 5 trading days.
- Position size: derived from configured risk % per trade and ATR stop distance.

**Acceptance Criteria:** Every served prediction includes entry reference price, stop loss level, take profit level, and position size (in shares) for the configured portfolio size.

---

### FR-15 — Universe Selection and Scoring (Weekly)
**The system must select and rank a universe of stocks weekly using a composite multi-analysis score.**

- Composite score = Fundamental (25%) + Technical (35%) + Quant (25%) + Sentiment (5%) − Risk penalty (10%).
- Weights shift by market regime (see theories and algorithm playbook for regime-conditional weights).
- Hard eligibility gates: liquidity minimum, price floor, manipulation risk score < 0.60.
- Universe size: target 30 active symbols; hard cap 50.
- Cap-tier quotas enforced: large, mid, small cap allocation ratios defined in governance policy.

**Acceptance Criteria:** A valid universe snapshot exists in S3 every Monday before the daily pipeline runs. Every symbol in the universe has passed all eligibility gates and has a composite score ≥ the minimum threshold.

---

### FR-16 — Opportunity Scanner (Daily)
**The system must scan a broader candidate list (~700 NSE symbols) daily for unusual volume or price activity outside the active universe.**

- Flags symbols meeting any of: volume >5× 21-day average, single-day move >5%, weekly move >15%, 52-week high breach, OBV rising 5+ days before spike.
- Computes manipulation_risk_score for each flagged symbol.
- Outputs a daily scanner watchlist file to S3.
- Does NOT automatically add flagged symbols to the universe — requires platform owner review.

**Acceptance Criteria:** A scanner watchlist file is written to S3 every trading day. No flagged symbol is added to the active universe without documented platform owner approval.

---

### FR-17 — Manipulation Risk Scoring
**The system must compute a manipulation_risk_score for every scanner-flagged symbol and every symbol under review for universe inclusion.**

- Score components: OBV pre-advance slope, volume concentration ratio, fundamental presence flag, float risk flag.
- Score 0.00–0.29: low risk — eligible for universe.
- Score 0.30–0.59: medium risk — requires documented platform owner review.
- Score ≥0.60: high risk — hard-rejected automatically.

**Acceptance Criteria:** No symbol with manipulation_risk_score ≥ 0.60 appears in the active universe. Every medium-risk symbol inclusion has a logged justification record.

---

### FR-18 — Local Backup and Failover
**The system must maintain a daily-synchronized local copy of all critical data on the platform owner's laptop.**

- Sync covers: S3 Bronze/Silver/Gold snapshots, DynamoDB predictions and audit exports, model artifacts, SQLite experiment metadata.
- Local PostgreSQL mirrors DynamoDB schema for predictions and pipeline audit.
- In the event of AWS account issues, the full pipeline must be runnable locally within 2 hours of failover activation.

**Acceptance Criteria:** Local PostgreSQL is never more than 2 calendar days behind DynamoDB. Failover drill (per ADR-004) can be completed within 2 hours.

---

### FR-19 — Observability and Alerts
**The system must monitor its own health and alert the platform owner by email (SNS) when thresholds are breached.**

| Alert | Threshold | Channel |
| --- | --- | --- |
| AWS billing | $0.10 cumulative spend | SNS email |
| DynamoDB RCU/WCU | 80% of free-tier limit | SNS email |
| S3 storage | 80% of 5 GB free-tier limit | SNS email |
| Universe size | Warning at 150 symbols, critical at 200 | SNS email |
| Pipeline job failure | Any J01–J09 job failure | SNS email |
| Model staleness | Active model >30 days old | SNS email |

**Acceptance Criteria:** Platform owner receives an SNS alert within 15 minutes of any threshold breach during any trading day.

---

### FR-20 — Full Audit Trail
**The system must maintain a complete audit trail for all pipeline runs, model training events, universe changes, and manual overrides.**

- Every pipeline job writes a structured audit record to DynamoDB: run_id, job_id, status, symbol counts, duration, timestamp.
- Every manual override (universe promotion, model rollback, medium-risk approval) is logged with date, decision, and reason.
- Audit records are retained for minimum 365 days.

**Acceptance Criteria:** For any trading day in the past 365 days, the full pipeline execution history can be reconstructed from DynamoDB audit records.

---

### FR-21 — Infrastructure Provisioning (Terraform + CloudFormation)
**All AWS infrastructure must be provisioned and managed via Infrastructure-as-Code. No resources are created, modified, or deleted manually in the AWS console after initial account bootstrap.**

- **Primary tool — Terraform:** Manages all core AWS resources end-to-end:
  - IAM roles, IAM policies, and instance profiles (least-privilege, per-service).
  - S3 buckets: Bronze, Silver, Gold data lake zones, model artifacts bucket, Terraform state bucket.
  - DynamoDB tables: predictions store, pipeline audit log, Terraform state lock table.
  - Lambda functions and EventBridge schedules for all pipeline jobs (J01–J09).
  - CloudWatch alarms, log groups, and metric filters for observability (FR-19).
  - AWS Glue Catalog databases and table definitions for Iceberg metadata.
  - Secrets Manager secrets (all credentials and API keys — NFR-05).
  - EC2 t2.micro instance for batch compute jobs.
- **Secondary tool — CloudFormation:** Manages SNS topics and subscriptions for email alerting, and any resources where native CloudFormation support is preferred or Terraform AWS provider coverage is insufficient.
- Terraform remote state is stored in S3 (`project-intelligent-tf-state` bucket) with DynamoDB state locking (`tf-state-lock` table), versioning enabled, and SSE-S3 encryption.
- All provisioned resources must carry standard tags: `Project=ProjectIntelligent`, `ManagedBy=Terraform` (or `ManagedBy=CloudFormation`), `Phase=Phase0`.
- Terraform modules are organised by service domain: `iam`, `s3`, `dynamodb`, `lambda-eventbridge`, `cloudwatch-secrets-glue`, `ec2`.
- Infrastructure code lives in `infra/terraform/` and `infra/cloudformation/` within the GitHub repository.

**Acceptance Criteria:** `terraform apply` completes with zero errors and provisions all required AWS resources from a clean account state. `terraform plan` run against an already-provisioned environment reports zero drift. CloudFormation stack deploys successfully and SNS email subscription is confirmed.

---

## 4. Non-Functional Requirements

### NFR-01 — Cost
- Total AWS cloud spend must not exceed $0 per month during the 12-month AWS free-tier period.
- A billing hard-gate alarm at $0.10 provides the earliest possible warning before any charges occur.
- After the free-tier period, the architecture must support migration of heavy compute to local laptop (ADR-004 designed for this).

### NFR-02 — Reliability
- The daily pipeline (J02 → J04 → J05 → J07 → J08) must complete successfully on ≥95% of trading days in any calendar month.
- A single failed job must not prevent the next day's pipeline from running.
- Failed symbols are retried on the next trading day automatically.

### NFR-03 — Data Freshness
- Predictions must be generated from the same trading day's market data — no day-old data used for inference.
- Fundamental data staleness: ≤95 days.
- Macro data staleness: ≤35 days.
- Regime label staleness: ≤5 days.

### NFR-04 — Reproducibility
- Any historical prediction must be fully reproducible: given a symbol, date, and Gold snapshot version, the exact feature values and prediction can be reconstructed.
- Model artifacts, feature versions, label versions, and Gold snapshot IDs are permanently stored together.

### NFR-05 — Security
- No API keys, credentials, or secrets are stored in code or GitHub.
- All secrets in AWS Secrets Manager.
- Least-privilege IAM roles for all AWS services.
- No direct human write access to Bronze S3 zone.

### NFR-06 — Latency
- This is a batch system — no real-time latency requirement.
- Full daily pipeline (J02 → J08) must complete within 4 hours of trigger (by 01:00 UTC next day / 6:30 AM IST).

### NFR-07 — Portability
- All pipeline code must run on both EC2 (primary) and the platform owner's local Windows laptop (failover) without modification to core logic.
- Only environment configuration (paths, credentials) differs between environments.

### NFR-08 — Infrastructure as Code (IaC)
- Zero AWS resources are created, modified, or deleted via the AWS console after initial account bootstrap.
- All infrastructure changes are version-controlled in Git and applied exclusively via `terraform apply` or CloudFormation stack updates.
- Terraform state must always be stored in the remote S3 backend — local state files are never committed to the repository.
- Every infrastructure change must be reviewable as a `terraform plan` diff before application.
- Full environment tear-down and re-provisioning must complete without manual intervention.

---

## 5. Data Requirements

| Data | Source | Cadence | Mandatory |
| --- | --- | --- | --- |
| OHLCV (NSE stocks) | yfinance `.NS` suffix | Daily | Yes |
| OHLCV (US stocks) | yfinance no suffix | Daily | Yes |
| NSE delivery percentage | NSE bhav copy CSV | Daily | Yes (India) |
| Fundamentals (P/E, debt, cash flow, etc.) | yfinance `.info`, `.financials`, `.balance_sheet`, `.cashflow` | Quarterly | Yes |
| NSE earnings calendar | NSE corporate filings board meetings page | Weekly | Yes (India) |
| Corporate actions (bonus, split, dividend) | yfinance `.actions` + NSE corporate calendar | Weekly | Yes |
| India VIX | yfinance `^INDIAVIX` | Daily | Yes (India) |
| Nifty 50 index | yfinance `^NSEI` | Daily | Yes (India) |
| RBI repo rate and bond yields | RBI public data portal | Weekly | Yes (India) |
| CBOE VIX | yfinance `^VIX` | Daily | Yes (US) |
| S&P 500 index | yfinance `^GSPC` or FRED | Daily | Yes (US) |
| US macro (fed funds rate, yield spread) | FRED API (free) | Weekly | Yes (US) |
| News and sentiment | Finnhub API (free tier, 60 calls/min) | Daily | Yes |
| RBI MPC and Budget dates | RBI calendar + Finance Ministry (manual, annual update) | Annual | Yes (India) |
| NSE circuit band categories | NSE reference file | Weekly auto-fetch | Yes (India) |
| Institutional ownership, promoter data | yfinance `.info` (aggregate proxy) | Quarterly | Yes |
| Promoter pledging %, FII/DII split | BSE shareholding filing | Quarterly — Phase B | No (Phase 1) |

---

## 6. Out of Scope — Phase 1

The following are explicitly NOT part of Phase 1. They are not gaps — they are deliberate deferrals.

| Item | Reason Deferred |
|---|---|
| Intraday trading signals | Architecture guardrail G1: swing horizon must be fully validated before intraday begins |
| Long-horizon (weeks to months) signals | Deferred to Phase 2 |
| Automated trade execution (broker API) | Requires separate architecture review; out of scope by design |
| BSE shareholding data (FII/DII exact split) | Requires new ADR for new data source; Phase B |
| NLP on earnings call transcripts | Complexity 5, data cost high — deferred to Phase 3 |
| Multi-user support | Single operator platform — no auth or multi-tenancy needed |
| Mobile app or web dashboard | Phase 2 product skeleton |
| US macro data for Indian symbol scoring | US macro is US-context only; Indian symbols use RBI data |
| Options and derivatives signals | Entirely different product line |
| Sector rotation strategy | Phase 2 expansion after swing baseline validated |
| Advanced Wyckoff stage classifier | Phase B — OBV proxy added; full classifier deferred |
| Hidden Markov regime model | Phase C — rule-based classifier sufficient for Phase 1 |

---

## 7. Assumptions and Dependencies

| # | Assumption / Dependency |
| --- | --- |
| A1 | AWS free-tier account remains active and within limits for the first 12 months |
| A2 | yfinance continues to provide NSE data with `.NS` suffix at current data quality |
| A3 | NSE bhav copy CSV format does not change without notice |
| A4 | NSE board meeting intimation page remains publicly accessible without login |
| A5 | Finnhub free tier remains at 60 calls/min with no daily cap |
| A6 | RBI and FRED continue to publish macro data through free public endpoints |
| A7 | Local laptop is available and powered during the daily sync window (overnight) |
| A8 | PostgreSQL is already installed on the local laptop (confirmed — ADR-003) |
| A9 | GitHub repository access is available throughout the project |
| A10 | The platform owner has no more than 5 concurrent swing positions at any time (position sizing constraint) |
| A11 | Terraform CLI and AWS CLI are available in the development environment; Terraform version ≥ 1.6 is used throughout |

---

## 8. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | yfinance data quality degrades or NSE data becomes unavailable | Medium | High | ADR-004 local failover; switch to alternative source via ADR process |
| R2 | AWS free-tier limits exceeded unexpectedly | Low | Medium | $0.10 billing alarm; immediate local failover activation |
| R3 | ML model accuracy degrades in a new market regime | Medium | Medium | Weekly retraining + model staleness gate; regime-conditional feature weights |
| R4 | NSE bhav copy URL or format changes | Low | Medium | Weekly schema validation check; fallback to OBV-only volume signals |
| R5 | Promoter pledging data unavailable (yfinance limitation) | High | Low | Documented as Phase 1 limitation; BSE data source planned for Phase B |
| R6 | FII/DII ownership split unavailable | High | Low | Aggregate institutional ownership used as proxy; exact split deferred to Phase B |
| R7 | Scanner flags a pump-and-dump that passes manipulation risk check | Low | High | Medium-risk band requires manual review; position sizing limits loss to 1% of portfolio |
| R8 | Earnings gap loss exceeds ATR stop distance | Medium | Medium | Earnings blackout gate prevents new entries; existing positions are platform owner's responsibility |
| R9 | Model overfits to recent bull market data | Medium | Medium | Walk-forward validation; backtest must cover multiple regimes including bear periods |
| R10 | Local laptop unavailable during failover need | Low | High | 2-hour failover target; daily sync ensures data is current |

---

## 9. Definition of Done — Phase 1

Phase 1 (Swing Baseline) is complete when all of the following are true:

- [ ] All 9 pipeline jobs (J01–J09) execute successfully on at least 20 consecutive trading days with ≥95% symbol coverage.
- [ ] The Gold feature layer contains non-null values for all 10 feature groups for all active universe symbols with ≥252 days of history.
- [ ] Walk-forward backtest (minimum 2 years of history) shows: directional accuracy ≥55%, R:R win rate ≥40%, max drawdown ≤20%, Sharpe ratio ≥0.5 — all metrics computed after India transaction costs (0.50% round-trip).
- [ ] All 20 functional requirements have a passing acceptance criterion verified and documented.
- [ ] All 5 non-functional requirements are verified.
- [ ] Zero corporate action ex-date rows appear in the training dataset.
- [ ] All 5 prediction serving gates are confirmed operational via test cases.
- [ ] Local failover drill (per ADR-004) completed successfully within 2 hours.
- [ ] AWS billing has not exceeded $0.00 at any point during Phase 1 development.
- [ ] `terraform apply` provisions all AWS resources from a clean state with zero errors; `terraform plan` shows zero drift on an already-provisioned environment.
- [ ] All AWS resources carry correct `Project`, `ManagedBy`, and `Phase` tags.
- [ ] Phase 1 exit checklist signed off by platform owner.

---

## 10. Document History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-05-07 | Platform Owner | Initial PRD — created after architecture design phase completion |
| 1.1 | 2026-05-07 | Platform Owner | Added FR-21 (Terraform + CloudFormation IaC provisioning), NFR-08 (IaC governance), assumption A11, and IaC Definition of Done checklist items |
