# Regime Analysis Architecture

## Purpose
Detect market state shifts and adapt model expectations accordingly.

## Regime Types
- Bull trend
- Bear trend
- Sideways range
- High-volatility stress

## Detection Inputs
- Index trend and slope
- Volatility state
- Breadth proxies
- Drawdown context

## Theory Layer
1. Dow Theory
- Primary trend definition from price structure.
- Secondary corrections versus primary trend continuation.
- Volume confirmation for trend conviction.

2. Trend and Mean-Reversion Context
- Favor trend-following logic in directional regimes.
- Favor mean-reversion logic in sideways regimes.

3. Breadth Confirmation
- Regime confidence increases when index move and breadth agree.

## Regime Algorithms (Architecture Options)
1. Rule-based state machine
- Use trend slope, moving average structure, and volatility thresholds.

2. Hidden Markov Model
- Estimate latent regime state probability and transitions.

3. Change-point detection
- Detect structural breaks for regime shift events.

4. Ensemble regime label
- Combine rule-based and probabilistic outputs for stable labeling.

## Regime-to-Strategy Mapping
- Bull trend: prioritize continuation signals and higher confidence trend setups.
- Bear trend: reduce net-long exposure and tighten entry quality filters.
- Sideways range: prioritize selective mean-reversion setups.
- High-volatility stress: reduce exposure and increase risk penalties.

## Architecture Rules
- Maintain explicit regime labels per date.
- Evaluate all model performance by regime.
- Introduce regime-based confidence adjustment in predictions.
- Keep a regime transition buffer to avoid whipsaw due to single-day flips.

## Guardrails

### G1 - Transition Buffer
- A regime label change is only accepted after the new signal persists for a minimum of 3 consecutive trading days.
- Single-day signals do not trigger a label update; the prior label is held during the buffer period.

### G2 - Confidence Floor
- Regime labels with confidence below the configured threshold are not propagated to the strategy mapper.
- The previous valid high-confidence label is held until confidence recovers.

### G3 - Algorithm Version Lock
- The regime algorithm version used for a given date's label must be recorded in the output.
- Mixing outputs from different algorithm versions for the same date range is not permitted.

### G4 - Regime Instability Review
- If regime transitions occur more than 4 times within any 20 trading day window, a stability review is automatically triggered.
- During the review period, model exposure is reduced and alerts are raised.

### G5 - Breadth Agreement
- Regime label confidence is automatically reduced when index trend and breadth signals disagree.
- The disagreement is logged as a supporting signal conflict.

### G6 - Mandatory Regime Context
- No prediction is accepted without a valid, non-stale regime label.
- Predictions produced without a current regime context are suppressed from serving.

## Output Fields
- regime_label
- regime_confidence
- regime_transition_risk
- regime_as_of_date
- regime_algorithm_version
- regime_supporting_signals

---

## Regime Signal Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Regime Signal or Algorithm | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Dow Theory trend state | HH/HL uptrend, LH/LL downtrend, volume | 5 | 2 | 5 | 3.70 | Must-have now |
| Rule-based regime classifier | MA slope, volatility threshold, drawdown | 5 | 2 | 5 | 3.70 | Must-have now |
| Breadth confirmation signal | Advance-decline proxy, participation ratio | 4 | 2 | 4 | 2.80 | Must-have now |
| Regime transition buffer | Anti-whipsaw cooldown logic | 4 | 2 | 5 | 3.10 | Must-have now |
| Regime-to-strategy mapper | Strategy mode by regime label | 5 | 2 | 5 | 3.70 | Must-have now |
| Change-point detection | Structural break identification | 3 | 4 | 5 | 2.30 | Add next |
| Ensemble regime label | Combine rule and probabilistic outputs | 4 | 4 | 5 | 2.70 | Add next |
| Hidden Markov Model | Latent regime probability estimation | 3 | 5 | 5 | 2.00 | Add later |

Interpretation:
- Priority score >= 2.80: must-have for swing now.
- Priority score 2.10 to 2.79: add next.
- Priority score < 2.10: add later.

## Regime Architecture Backlog for Swing

Must-have now:
- Dow Theory trend state machine.
- Rule-based regime classifier.
- Regime-to-strategy mapper.
- Anti-whipsaw transition buffer.
- Breadth confirmation signal.

Add next:
- Ensemble regime label combining rules and probabilistic output.
- Change-point detection for structural breaks.

Add later:
- Hidden Markov Model for latent regime probability.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Regime label: 40%
- Regime confidence score: 35%
- Transition risk penalty: 25%
