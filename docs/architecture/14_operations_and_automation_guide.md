# 14 Operations and Automation Guide

## Purpose
Define which pipeline steps are fully automated, which require manual decisions, and which are setup-once tasks. This is the operational reference for the platform owner (you) as the single operator running the system.

---

## Guiding Principle

The platform is designed so that **data collection, feature engineering, model training, and prediction generation are fully automated** after initial setup. Your role as operator is not to run processes — it is to make the small number of decisions that require human judgement and accountability: reviewing scanner alerts, approving universe changes, and managing open positions before known risk events.

**Target weekly effort after setup: 30–60 minutes every Sunday.**

---

## Section 1 — Fully Automated (Daily, Monday to Friday)

These steps run without any human involvement every trading day. They are triggered by AWS EventBridge at 21:00 UTC (2:30 AM IST next day, after NSE/BSE close + after US market close).

| Step | What Happens | Output |
| --- | --- | --- |
| **1. Market data ingestion (J02)** | EC2 pulls OHLCV for all universe symbols from yfinance. NSE bhav copy CSV (delivery %) downloaded from NSE archives. Raw files written to Landing layer (S3, Object Lock). G0 quality gate runs; passing records promoted to Bronze. | Landing raw files → Bronze OHLCV + delivery parquet files in S3 |
| **2. Earnings calendar check** | yfinance earnings dates checked against today's date. `days_to_next_earnings` updated for all symbols. | Silver calendar join ready |
| **3. Corporate action flag** | yfinance actions table checked. Any symbol with an ex-date today gets `corporate_action_flag = 1`. | Rows flagged for training exclusion |
| **4. Bronze → Silver promotion (J04)** | Cleaning, deduplication, adjusted price enforcement, all Silver joins applied (calendar, corporate actions, regime, macro). | Silver Iceberg snapshot in S3 |
| **5. Silver → Gold feature engineering (J05)** | All 10 feature groups computed for every symbol: price returns, rolling stats, technicals (RSI, MACD, ATR, Bollinger, SMA, 52-week, RS, support/resistance), volume (OBV, A/D, MFI, delivery %), volatility, regime (Nifty 50 + India VIX), calendar + earnings events, candlestick patterns, institutional positioning, India regulatory risk (promoter pledging, circuit breaker flags). | Gold Iceberg snapshot in S3 |
| **6. Prediction gate checks** | Automatically applied before predictions are served — no human action: Earnings blackout (result in ≤2 days → suppressed), Circuit breaker gate (upper/lower circuit hit → suppressed), Macro event gate (RBI/Budget within 2 days → suppressed for rate-sensitive sectors), Confidence floor gate (model confidence below threshold → suppressed). | Suppression flags logged in DynamoDB |
| **7. Batch inference (J07)** | ML model reads Gold snapshot. Generates 1-day direction prediction + confidence for each non-suppressed symbol. | Predictions written to DynamoDB |
| **8. Local sync (J08)** | DynamoDB predictions + audit records synced to local PostgreSQL on laptop. S3 landing/bronze/silver/gold synced to local disk mirror. | Local backup current |
| **9. Monitoring and alerts** | CloudWatch checks: billing alarm ($0.10 threshold), DynamoDB RCU/WCU usage, S3 storage (5 GB limit), job failure status. SNS email sent on any breach. | SNS alert email to you if any threshold hit |

**If any step fails:** The chain stops. Downstream steps do not run. A CloudWatch alert is raised. The failed step is retried automatically on the next daily run. No manual restart needed unless the failure is structural.

---

## Section 2 — Fully Automated (Weekly, Every Sunday)

These steps run every Sunday without human involvement.

| Step | Time (UTC) | What Happens | Output |
| --- | --- | --- | --- |
| **Universe scoring (J01)** | 14:00 | All active symbols re-scored on the composite (fundamental + technical + quant + sentiment + risk penalty). Rankings updated. Cap-tier quotas enforced. | Universe snapshot in S3, DynamoDB audit |
| **Opportunity scanner** | 14:00 (part of J01) | ~700 NSE symbols scanned for volume/price anomalies (volume >5×, price move >5%, 52-week high breach). Manipulation risk score computed for flagged symbols. | Scanner watchlist JSON in S3 |
| **Macro data ingestion (J03)** | 15:00 | RBI repo rate, India 10Y/2Y bond yields, India CPI updated. India VIX and Nifty 50 weekly series updated. yfinance earnings calendar refreshed. Corporate actions calendar refreshed. Raw responses written to Landing layer first; G0 gate applied before Bronze promotion. | Landing raw files → Bronze macro parquet files in S3 |
| **Model training (J06)** | 16:00 | Weekly training run on latest Gold snapshot. New model compared to current live model. Promoted automatically only if directional accuracy improves by ≥2 percentage points on out-of-sample data. | New model artifact in S3 (if promoted), training report in DynamoDB |
| **New symbol backfill (J09)** | After J01 if new symbols | If J01 adds new symbols to universe, targeted 252-day backfill runs for those symbols before Monday's daily pipeline. Historical raw data written to Landing layer; G0 gate applied before Bronze promotion. | Landing raw files → Bronze backfill parquet in S3 |

---

## Section 3 — Requires Your Decision (Weekly Manual Review)

These are intentional human gates. The system cannot and should not automate them — they require your judgement as the investment decision maker.

**Recommended: Review these every Sunday before the market opens Monday.**

### 3.1 Scanner Watchlist Review
**What:** The opportunity scanner flagged stocks outside your current universe that showed unusual volume or price action this week.

**Where to look:** S3 scanner watchlist file → your review dashboard or direct file read.

**Your decision:**
- Is this a genuine mover or a pump-and-dump?
- Does the manipulation_risk_score support inclusion?
- Do you want to fast-track this symbol into the universe?

**Action if yes:** Log the approval with reason, triggering scanner criteria, and manipulation_risk_score. The symbol enters standard eligibility gates before being added.

**Time required:** 10–20 minutes depending on how many symbols were flagged.

---

### 3.2 Universe Composition Review
**What:** The weekly scoring may suggest adding or removing symbols based on composite score changes.

**Where to look:** Universe snapshot in S3. DynamoDB audit record for J01 shows additions, removals, and borderline symbols.

**Your decision:**
- Accept the automated ranking as-is, or
- Override a specific addition/removal if you have context the model does not (e.g., you know a company is under regulatory scrutiny not yet reflected in data).

**Any override must be logged with reason.**

**Time required:** 10–15 minutes.

---

### 3.3 Model Promotion Review
**What:** The weekly training job produces a model comparison report. If the new model passed the automated promotion threshold (≥2% accuracy improvement), it was already promoted. If it did not pass, you see the report but no change was made.

**Where to look:** Training report in DynamoDB (or local PostgreSQL mirror).

**Your decision:**
- If the model was automatically promoted: confirm you are comfortable with the change. If not, you can manually roll back to the previous model artifact.
- If the model was not promoted: no action needed. The previous model continues serving.

**Time required:** 5 minutes.

---

### 3.4 Medium Manipulation Risk Symbol Review
**What:** The manipulation risk scoring flags symbols into three bands:
- Score < 0.30 → automatically cleared. No action needed.
- Score 0.30–0.59 → **requires your documented review** before inclusion.
- Score ≥ 0.60 → automatically hard-rejected. No action needed.

**Where to look:** Universe audit record in DynamoDB flags medium-risk symbols.

**Your decision:** Include with documented justification, or reject.

**Time required:** Variable. Usually 0–5 minutes (most weeks no medium-risk symbols are pending).

---

### 3.5 Open Position Review Before Known Risk Events
**What:** The automated prediction gates block *new entries* before earnings, RBI MPC, and Budget dates. They do **not** automatically exit *open positions* you already hold. Managing open positions before these events is your responsibility.

**Known risk events to check weekly:**
- Which universe symbols have board meeting / results in the next 5 trading days?
- Is the next RBI MPC announcement within the next 5 days?
- Do you hold positions in banking, NBFC, or real estate sectors going into an MPC date?

**Your decision:** Exit the position early to avoid event risk, or hold and accept the gap risk.

**Where to look:** Silver calendar join table (days_to_next_earnings for all symbols). India macro event reference file in Bronze.

**Time required:** 5–10 minutes.

---

## Section 4 — Setup Once, Then Automated

These require your time only once at project start, or once per year thereafter.

| Task | When | Your Effort | Then Automated |
|---|---|---|---|
| AWS infrastructure setup | Project start | 2–4 hours: EC2, S3 buckets, DynamoDB tables, EventBridge rules, Lambda functions, CloudWatch alarms, IAM roles | Fully automated thereafter |
| GitHub repository + CI/CD | Project start | 1–2 hours: repo creation, branch strategy, GitHub Actions workflows | Automated on every commit |
| Local PostgreSQL setup | Project start | 30 minutes: schema creation, sync script configuration | Automated daily sync |
| Initial Bronze backfill | Project start (runs once) | Trigger J09 once; pipeline runs automatically | Completes in hours unattended |
| RBI MPC calendar update | Every April (RBI publishes annual schedule) | 5 minutes: copy 6 dates into Bronze reference file | Pipeline reads it all year |
| Union Budget date update | Once per year (~60 days before budget, usually December) | 2 minutes: update one date in Bronze reference file | Pipeline reads it |
| NSE circuit band reference | Pipeline auto-fetches weekly | No manual effort after first run | Fully automated |
| Finnhub API key setup | Project start | 5 minutes: register free account, store key in AWS Secrets Manager | Automated thereafter |
| RBI data source setup | Project start | 30 minutes: configure weekly scrape endpoint in pipeline config | Automated weekly |

### 4.1 How to manually update the India Macro Events Calendar

Because it is brittle to build automated scrapers for government websites, the RBI MPC and Union Budget dates are maintained manually. An automated GitHub Action (`.github/workflows/annual_maintenance_reminder.yml`) runs every year on April 1st to remind you to do this.

**To perform the update:**
1. Open the file: `configs/india_macro_events.yaml` in this repository.
2. **For RBI MPC Dates:** 
   - Go to the [RBI Press Releases website](https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx).
   - Search the press releases for "Monetary Policy Committee meeting schedule". (They publish all 6 dates for the upcoming financial year at once).
   - Update the YAML file using the *last day* of each meeting window as the `event_date`.
3. **For Union Budget:**
   - Wait until the Finance Ministry officially announces the Union Budget date (typically February 1st).
   - Add this single date to the YAML file.
4. **Commit the changes:** Just commit and push to the `main` branch. 
5. **Automation takes over:** The automated weekly J07 pipeline will automatically detect your changes on Saturday and sync them to the S3 database without any further manual steps!

---

## Section 5 — Governance Actions (As Needed, Not Regular)

These happen infrequently but must be done correctly when they arise.

| Trigger | Action Required |
|---|---|
| New data source needed (e.g., BSE shareholding data for FII/DII split) | Write an ADR. Review and approve. Then implement. |
| Changing R:R parameters (stop multiplier, target multiplier, max hold days) | Update `configs/label_rules.yaml`. Increment `label_version`. Trigger full Gold rebuild. Retrain model. |
| Changing position sizing parameters | Update `configs/position_sizing.yaml`. Document reason. |
| Changing manipulation risk thresholds | Update governance policy document. Log version change. |
| Billing alarm fires ($0.10 threshold) | Investigate immediately. Check which service is billing. Reduce usage or activate local laptop failover per ADR-004. |
| Universe size hits 150 symbols | Begin PostgreSQL migration planning per ADR-003 guardrail. |
| Model performance decays (accuracy drops ≥5% from baseline) | Trigger off-cycle retraining review. Check for regime shift. May need feature version update. |
| Phase gate transition (Phase 0 → 1 → 2 → 3) | Complete phase exit checklist (all docs reviewed, all guardrails met). Sign off. Log date and approver. |

---

## Section 6 — Summary

| Category | Steps | Weekly Effort |
|---|---|---|
| Fully automated (daily) | 9 steps | Zero |
| Fully automated (weekly) | 5 steps | Zero |
| Manual review required | 5 decision points | 30–60 minutes every Sunday |
| Setup once | 10 items | A few hours at project start |
| Governance (as needed) | 8 triggers | Infrequent, event-driven |

### The Simple Weekly Routine

Every Sunday morning (30–60 minutes total):
1. Check your SNS alert email — any alarms fired this week?
2. Read the scanner watchlist — any flagged stocks worth reviewing?
3. Check universe changes — any additions/removals to approve?
4. Read the model training report — any performance change?
5. Check next week's event calendar — any earnings, RBI MPC, or Budget dates that affect open positions?
6. Done. The rest runs itself.

---

## Guardrails

### G1 - No Automated Trade Execution
- The platform generates prediction signals. It does not place buy or sell orders automatically.
- Actual trade execution is always a manual human action.
- Any integration with a broker API for automated order placement requires a formal architecture review and sign-off before design begins.

### G2 - All Manual Decisions Are Logged
- Every manual override (fast-track promotion, universe composition change, model rollback, medium-risk symbol approval) must include: date, decision, reason, and approver identity.
- Undocumented overrides are treated as policy violations.

### G3 - Open Position Risk Is Owner Responsibility
- The system blocks new entries before known risk events. It does not close existing positions automatically.
- The platform owner (you) is responsible for reviewing open positions before each earnings result, RBI MPC, and Budget date.
- This responsibility cannot be delegated to the automation layer.

### G4 - Setup Tasks Must Be Completed Before Phase 1 Starts
- All Section 4 setup tasks must be completed and verified before the Phase 0 → Phase 1 gate sign-off.
- No Phase 1 implementation begins with incomplete infrastructure.

### G5 - Governance Changes Are Versioned
- Any change to config files (label_rules.yaml, position_sizing.yaml) or policy thresholds must be committed to GitHub with a descriptive commit message and logged in the relevant architecture document.
- Config changes without version history are policy violations.
