# Market Microstructure Analysis Architecture

## Purpose
Model tradability and execution risk proxies relevant to swing decisions.

## Proxy Metrics (OHLCV-Friendly)
1. Liquidity proxies
- Average volume
- Dollar volume

2. Volatility-liquidity interaction
- Volume during high-range bars

3. Gap behavior
- Open-to-close and close-to-open patterns

4. Participation shocks
- Abnormal volume spikes and reversals

## Architecture Role
- Use microstructure as risk penalty and execution feasibility layer.
- For swing horizon, avoid symbols with unstable tradability profiles.
- Compute manipulation_risk_score to distinguish genuine institutional accumulation from coordinated price inflation (pump-and-dump).

---

## Manipulation Risk Score Architecture

### Problem
When a scanner-flagged symbol shows a sudden price or volume spike, there are two possible causes:
1. **Genuine institutional accumulation** — FII/DII players are quietly building a position. OBV rises for days/weeks before the price moves. Fundamental backing exists. Float is reasonable. This is an opportunity.
2. **Pump-and-dump manipulation** — A small group artificially inflates price using coordinated buying, then sells. Volume appears suddenly on the same day as the price spike. No prior OBV buildup. Often thin float, micro-cap, no real fundamentals.

The architecture must distinguish these two cases before allowing a scanner-flagged symbol into the universe.

### Distinguishing Signals

| Signal | Genuine Accumulation | Pump and Dump |
| --- | --- | --- |
| OBV slope before price spike | Rising for 5–10 days before the move | Flat or rising only on the spike day |
| Volume concentration | Volume spreads across multiple days | Volume concentrated in 1–2 days |
| Fundamental presence | P/E, revenue, earnings data exists | No or near-zero fundamentals |
| Market cap and float | Mid to large cap, adequate float | Micro-cap, very thin float |
| Price reversal speed | Price consolidates or continues after move | Price peaks and reverses within 1–5 days |
| Return magnitude | 5–20% move sustained over days | 30–100%+ spike then immediate crash |

### Manipulation Risk Score Fields

| Field | Calculation | Notes |
| --- | --- | --- |
| obv_pre_advance_slope | Slope of OBV over the 10 days before the volume spike | Positive and rising = accumulation signal; flat = suspicious |
| volume_concentration_ratio | volume_t / mean(volume_t-1 through t-5) | >5 = volume arrived all at once; suspicious |
| fundamental_presence_flag | 1 if P/E and revenue data exist, 0 if both are missing | Missing fundamentals = higher fraud risk |
| float_risk_flag | 1 if market_cap < $300M AND average_daily_volume < 500K shares | Thin float = easy to manipulate price |
| price_reversal_3d | (close_t+3 - high_t) / high_t | Negative and large (< -0.20) = price crashed after spike = post-pump dump |
| manipulation_risk_score | Weighted composite: 0.30×volume_concentration + 0.25×(1-obv_pre_advance) + 0.25×float_risk_flag + 0.20×(1-fundamental_presence_flag) | Score 0–1; higher = higher manipulation risk |

### Thresholds
- manipulation_risk_score < 0.30: low risk. Symbol may proceed to composite scoring.
- manipulation_risk_score 0.30–0.59: medium risk. Symbol enters universe only with manual review and documented justification.
- manipulation_risk_score >= 0.60: high risk. Symbol is hard-rejected from universe selection regardless of price action or composite score.

### Limitation
- `price_reversal_3d` requires 3 days of forward data — it cannot be computed in real-time for the current day.
- For the current-day scanner output, manipulation_risk_score uses only the first 4 signals. Price reversal confirmation is a retrospective check used to validate and calibrate the score, not a real-time gate.

---

## Guardrails

### G1 - Thin-Market Hard Gate
- Symbols with average daily volume below the configured minimum are excluded from the universe before any scoring.
- This gate cannot be overridden by any composite score result, regardless of how high other domain scores are.

### G2 - Liquidity Dollar Floor
- Symbols with average daily dollar volume below the minimum threshold are hard-rejected from the selected universe.
- Dollar volume floor values are defined in the governance policy.

### G3 - Gap Risk Ceiling
- Symbols with average overnight gap exceeding the configured percentage threshold are flagged as high execution risk.
- High-gap-risk symbols are capped at reduced universe weight and excluded during high-volatility stress regimes.

### G4 - Execution Risk Block
- Symbols with execution_risk_score above the critical threshold are excluded from the selected universe during any high-volatility stress regime.
- The exclusion is automatic and does not require manual trigger.

### G5 - Participation Shock Rule
- Three consecutive abnormal volume spike events on a symbol trigger a watchlist flag.
- Watchlisted symbols are reviewed before being retained in or added to the universe.

### G6 - Daily Recompute
- Microstructure scores must be recomputed on every daily batch run.
- Stale microstructure scores from a prior day are not reused; symbols with missing recompute results are excluded until resolved.

### G7 - Manipulation Risk Hard Gate
- Any symbol with manipulation_risk_score >= 0.60 is hard-rejected from universe selection.
- This gate cannot be overridden by composite score, scanner flag, or manual request without a documented review and approver sign-off.
- Medium-risk symbols (score 0.30–0.59) require documented justification before inclusion.
- The manipulation_risk_score and its component signals are stored in the selection audit snapshot for every candidate symbol.

## Output Fields
- liquidity_score
- execution_risk_score
- gap_risk_score
- manipulation_risk_score
- microstructure_as_of_date

---

## Microstructure Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Microstructure Signal | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Liquidity proxy | Average daily volume, dollar volume | 5 | 1 | 5 | 4.30 | Must-have now |
| Gap risk profile | Close-to-open gap distribution | 5 | 2 | 5 | 3.70 | Must-have now |
| Volume-volatility interaction | Volume during high ATR bars | 4 | 2 | 5 | 3.10 | Must-have now |
| Execution risk score | Combined liquidity and gap penalty | 5 | 2 | 5 | 3.70 | Must-have now |
| Participation shock flag | Abnormal volume spike detection | 4 | 2 | 5 | 3.10 | Must-have now |
| Thin-market filter | Minimum tradability gate | 5 | 1 | 5 | 4.30 | Must-have now |
| Intraday range analysis | Daily high-low range consistency | 3 | 2 | 5 | 2.60 | Add next |
| Bid-ask spread proxy | Effective spread from OHLC (Roll model) | 3 | 4 | 4 | 1.90 | Add later |

Interpretation:
- Priority score >= 2.80: must-have for swing now.
- Priority score 2.00 to 2.79: add next.
- Priority score < 2.00: add later.

## Microstructure Architecture Backlog for Swing

Must-have now:
- Thin-market filter and minimum liquidity gate.
- Liquidity proxy score.
- Gap risk profile.
- Execution risk score.
- Participation shock and abnormal volume flag.
- Volume-volatility interaction.

Add next:
- Intraday range consistency analysis.

Add later:
- Effective bid-ask spread proxy using Roll model.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Liquidity proxy: 35%
- Gap risk profile: 30%
- Execution risk score: 25%
- Participation shock flag: 10%
