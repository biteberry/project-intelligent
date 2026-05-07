# 02 Universe Selection Before Landing

## Purpose
Create a repeatable process to produce the stock universe before data lands in bronze.

---

## Stage 0 — Opportunity Detection Scanner (Daily)

### Problem This Solves
The pre-selected 30-symbol universe is blind to everything outside it. Sudden price or volume anomalies in unfamiliar or penny stocks driven by FII/DII institutional flows would be entirely missed. Stage 0 runs a daily scan on a broader candidate list to catch these opportunities before they are gone.

### Broad Scan Universe
- S&P 500 components (approximately 500 symbols) — fetched from a static reference list updated quarterly.
- Russell 2000 top 200 by liquidity (filtered for minimum dollar volume) — covers mid and small cap movers.
- This gives approximately 700 symbols scanned daily at minimal cost (yfinance batch fetch, no paid API).

### Scanner Anomaly Criteria
A symbol is flagged for the watchlist if it meets ANY of the following on the current trading day:

| Criterion | Threshold | Signal Meaning |
| --- | --- | --- |
| Volume spike | Daily volume > 5× its own 21-day average volume | Unusual institutional or retail activity |
| Single-day price move | Return_1d > 5% OR Return_1d < -5% | Significant directional move |
| Weekly breakout | Return_5d > 15% | Multi-day momentum surge |
| 52-week high breach | Close price crosses above 52-week high | Breakout from long consolidation |
| OBV pre-advance | OBV rising for 5+ days before volume spike | Possible institutional accumulation pattern |

### Scanner Output
- A daily `scanner_watchlist` S3 JSON file listing flagged symbols, their triggering criteria, and their current manipulation_risk_score (see microstructure architecture).
- Symbols on the scanner watchlist are reviewed by the weekly universe selection job as fast-track candidates.

### Fast-Track Promotion Rules
A scanner-flagged symbol may be fast-tracked into the universe only if:
1. It passes the standard eligibility gates (Stage 1 below).
2. Its manipulation_risk_score is below the fraud threshold.
3. It has at least 252 days of Bronze history (or can be backfilled before next ingestion cycle).
4. Adding it does not violate cap-tier quota limits.

If all conditions pass, the symbol bypasses the normal weekly cadence and can be added mid-week with a manual override record (per Guardrail G5).

### Scanner Guardrail
- The scanner is read-only and informational; it does not automatically add symbols to the universe.
- Every fast-track promotion must be logged with reason, triggering scanner criteria, manipulation_risk_score, and approver.
- Scanner output is auditable: every daily scan file is retained in S3 for 90 days.

---

## Selection Stages
1. Eligibility gates:
- Liquidity minimums
- Price floor checks
- Listing and data-health checks
- Manipulation risk gate: symbols with manipulation_risk_score above the critical threshold are hard-rejected regardless of composite score (see market_microstructure_analysis_architecture.md)

2. Multi-analysis scoring:
- Fundamental score
- Technical score
- Quant score
- Sentiment score (optional initially)
- Risk penalty

3. Composite ranking:
- Build normalized composite score.
- Suggested swing baseline weights:
  - Fundamental 25%
  - Technical 35%
  - Quant 25%
  - Sentiment 5%
  - Risk penalty 10% subtractive

4. Cap-tier allocation:
- Enforce final-list quotas by large/mid/small cap.
- Example for 30 symbols: 15 large, 10 mid, 5 small.

5. Governance:
- Weekly refresh cadence for swing universe.
- Keep audit snapshots of each selection run.
- Replace symbols only on rank deterioration, rule break, or severe data-quality issues.

## Pre-Landing Output Contract
candidate_universe fields:
- symbol
- cap_tier
- horizon
- fundamental_score
- technical_score
- quant_score
- sentiment_score
- risk_penalty
- composite_score
- manipulation_risk_score
- scanner_flagged (true if symbol was identified via Stage 0 scanner)
- selected_flag
- selection_date

---

## Guardrails

### G1 - Score Completeness
- Composite score cannot be computed if more than one of the five analysis domain scores is missing.
- Symbols with too many missing domain scores are excluded from ranking and flagged in the audit log.

### G2 - Cap-Tier Quota Enforcement
- The final selected universe must include symbols from all three cap tiers: large, mid, and small.
- A selection result with zero symbols from any cap tier is invalid and triggers a pipeline halt and alert.
- Cap-tier quotas are defined in the governance policy and cannot be overridden without approval.

### G3 - Minimum Universe Size
- The selected list must not drop below 10 symbols after all gate rules are applied.
- If the post-gate count is below 10, the pipeline halts, an alert is raised, and the previous valid selection is retained.

### G4 - Selection Staleness
- A universe selection snapshot older than 10 calendar days is invalid for triggering ingestion.
- Stale selections cause the ingestion pipeline to halt until a fresh selection is produced.

### G5 - Manual Override
- Any manual override to the selection (add or remove a symbol outside of the scoring process) must be logged with reason, approver, and timestamp.
- Overrides without an audit record are rejected.

### G6 - Immutability
- Once written, a selection snapshot is never modified.
- Corrections require a new weekly selection run; in-place edits to selection files are not permitted.
