# Quantitative Analysis Architecture

## Purpose
Convert historical price and volume behavior into statistically robust predictive signals.

## Core Quant Blocks
1. Return distribution profiling
- Mean, variance, skew, kurtosis

2. Serial dependency
- Autocorrelation and partial autocorrelation

3. Volatility behavior
- Rolling volatility, volatility clustering proxies

4. Stability and regime fitness
- Rolling stationarity checks and regime-sensitive performance

5. Signal reliability
- Information coefficient style rank checks

## Modeling Principles
- Prefer simple robust models before complex ones.
- Use walk-forward validation only.
- Track performance decay over time slices.

## Guardrails

### G1 - Walk-Forward Only
- Any model evaluation or signal validation using random or non-temporal splits is invalid and rejected.
- Walk-forward is the only accepted evaluation method for all quant signals.

### G2 - Minimum Window Enforcement
- Rolling statistics must strictly respect the minimum window size.
- Computations with fewer observations than the required window produce nulls, not estimates.
- Partial-window estimates are not accepted in the gold layer.

### G3 - Look-Ahead Bias
- All quant signals must be computable solely from data on or before the feature date.
- Signal definitions referencing future periods are rejected at design time.

### G4 - Outlier Handling
- Extreme return values beyond a defined z-score threshold must be flagged and capped before entering distribution statistics.
- Uncapped outliers distort rolling moments and are not accepted in the gold feature table.

### G5 - Stationarity Awareness
- Features derived from non-stationary series without a transformation step are flagged for review.
- Stationarity flags must be included in the quant output contract.

### G6 - Signal Decay Monitoring
- If a signal's stability score drops below the configured threshold for 4 consecutive weeks, the signal is placed in a review queue.
- Degraded signals are not removed automatically; they are flagged, reviewed, and a documented decision is made.

## Output Fields
- quant_score
- signal_stability_score
- volatility_profile
- drawdown_risk_score
- quant_as_of_date

---

## Quantitative Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Quant Block | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Rolling volatility | 10/20-day realized vol, vol ratio | 5 | 1 | 5 | 4.30 | Must-have now |
| Return distribution | Mean, variance, skew of returns | 5 | 2 | 5 | 3.70 | Must-have now |
| Drawdown profile | Rolling max drawdown, recovery speed | 5 | 2 | 5 | 3.70 | Must-have now |
| Volatility clustering | Vol persistence proxy | 4 | 2 | 5 | 3.10 | Must-have now |
| Signal stability score | Rolling IC-style rank check | 4 | 3 | 5 | 2.90 | Must-have now |
| Autocorrelation | 1-5 lag return autocorrelation | 3 | 2 | 5 | 2.60 | Add next |
| Stationarity check | ADF rolling stationarity flag | 3 | 3 | 5 | 2.40 | Add next |
| Partial autocorrelation | PACF lag structure | 2 | 3 | 5 | 1.90 | Add later |
| Regime-conditional moments | Return moments per regime state | 4 | 4 | 5 | 2.70 | Add next |

Interpretation:
- Priority score >= 2.80: must-have for swing now.
- Priority score 2.20 to 2.79: add next.
- Priority score < 2.20: add later.

## Quantitative Architecture Backlog for Swing

Must-have now:
- Rolling volatility at 10 and 20 day windows.
- Return distribution profiling (mean, variance, skew).
- Rolling drawdown profile.
- Volatility clustering proxy.
- Signal stability check.

Add next:
- Autocorrelation lags 1 to 5.
- Stationarity flag.
- Regime-conditional return moments.

Add later:
- Partial autocorrelation structure.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Rolling volatility: 30%
- Drawdown profile: 25%
- Return consistency: 25%
- Signal stability: 20%
