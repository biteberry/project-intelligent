# Fundamental Analysis Architecture

## Purpose
Provide a stable, auditable quality layer for universe selection and risk control.

## Factor Domains
1. Business quality
2. Financial strength
3. Profitability and efficiency
4. Growth quality
5. Cash flow integrity
6. Valuation reasonability
7. Governance quality
8. Sector and macro fit

## Theoretical Anchors
- Intrinsic value
- Margin of safety
- Economic moat
- Relative valuation
- Mean reversion in valuation
- Quality at reasonable price

## Scoring Blueprint
- Build normalized score from 0 to 100.
- Maintain domain-level sub-scores and confidence.
- Keep as-of date for point-in-time correctness.

## Gate Rules
- Reject or penalize symbols with governance and accounting risks.
- Reject symbols with severe leverage stress or weak cash flow quality.

## Guardrails

### G1 - Mandatory Field Gate
- Symbols missing more than 2 of the 6 must-have fundamental factors are excluded from scoring entirely.
- Partial scores built on insufficient data are not permitted.

### G2 - Governance Red Flag Hard Rejection
- Any symbol with an active governance or accounting red flag is automatically excluded from universe selection regardless of its composite score.
- This gate cannot be overridden by any scoring result.

### G3 - Leverage Stress Gate
- Symbols with Debt/Equity above the critical threshold and declining interest coverage for 2 or more consecutive periods are hard-rejected.
- Threshold values are defined in the governance policy document.

### G4 - Cash Flow Gate
- Symbols with 3 or more consecutive quarters of negative operating cash flow are hard-rejected.

### G5 - Point-in-Time Rule
- Fundamental scores must use only data available as of the selection date.
- Any use of future-quarter or post-selection data invalidates the score and triggers a recompute.

### G6 - Score Staleness
- A fundamental score older than 95 days from the last reported earnings date is marked stale.
- Stale scores cannot be used in universe selection and must be refreshed before the next selection run.

### G7 - Score Versioning
- Every fundamental score record must carry a score_version field tied to the active policy document version.
- Scores without a version reference are rejected.

## Cadence
- Quarterly refresh plus event-driven refreshes.

## Output Fields
- fundamental_score
- fundamental_confidence
- fundamental_red_flags
- fundamental_as_of_date

---

## Fundamental Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Factor | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Cash flow integrity | CFO vs net income, FCF trend | 5 | 2 | 4 | 3.30 | Must-have now |
| Financial strength | Debt/Equity, interest coverage, current ratio | 5 | 2 | 4 | 3.30 | Must-have now |
| Profitability and efficiency | Gross/Op margin trend, ROE, ROIC | 5 | 3 | 4 | 3.10 | Must-have now |
| Valuation reasonability | P/E, EV/EBITDA, PEG vs peers | 5 | 2 | 4 | 3.30 | Must-have now |
| Growth quality | Revenue and EPS CAGR consistency | 4 | 2 | 4 | 3.00 | Must-have now |
| Governance quality | Insider behavior, audit flags | 4 | 3 | 3 | 2.30 | Must-have now |
| Business quality | Moat, pricing power, revenue model | 4 | 4 | 2 | 1.60 | Add next |
| Sector and macro fit | Sector cycle, rate sensitivity | 3 | 3 | 3 | 1.80 | Add next |
| Intrinsic value (DCF proxy) | Simplified DCF band estimation | 3 | 4 | 3 | 1.60 | Add later |

Interpretation:
- Priority score >= 2.50: must-have for swing now.
- Priority score 1.50 to 2.49: add next.
- Priority score < 1.50: add later.

## Fundamental Architecture Backlog for Swing

Must-have now:
- Cash flow integrity signal.
- Financial strength gate.
- Profitability and efficiency trend.
- Valuation reasonability check.
- Revenue and earnings growth consistency.
- Governance red-flag gate.

Add next:
- Business quality and moat scoring.
- Sector and macro fit context tag.

Add later:
- Simplified DCF intrinsic value band.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Cash flow integrity: 20%
- Financial strength: 20%
- Profitability and efficiency: 15%
- Valuation reasonability: 15%
- Growth quality: 15%
- Governance quality: 10%
- Business quality and macro fit: 5%
