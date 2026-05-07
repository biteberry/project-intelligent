# Theories and Algorithm Playbook (Architecture)

## Objective
Define high-value theories, algorithm families, and decision logic that improve stock selection and prediction quality without leaving architecture mode.

## 1. Classical Market Theories to Embed

1. Dow Theory
- Confirm trend using price action structure:
  - Higher highs and higher lows for uptrend
  - Lower highs and lower lows for downtrend
- Confirm trend across broad market and sector/index proxies.
- Treat volume as confirmation signal.

2. Wyckoff Cycle Logic
- Map accumulation, markup, distribution, markdown behavior.
- Use as context tag for swing setup quality.

3. Mean Reversion Theory
- Extreme moves tend to revert under range-bound regimes.
- Apply only when regime is sideways or weak-trend.

4. Trend Following Theory
- Momentum persistence is stronger in directional regimes.
- Prefer breakout and pullback continuation setups in bull/bear trend states.

5. Market Breadth Theory
- Trend quality is stronger when participation breadth is broad.
- Weak breadth during index highs is a caution signal.

## 2. Quant and ML Algorithm Families

1. Regime Detection
- State machine rules from trend and volatility thresholds.
- Hidden Markov Models for latent regime estimation.
- Change-point detection for structural shifts.

2. Signal Generation
- Cross-sectional ranking models.
- Tree-based models for nonlinear interaction capture.
- Probability calibration layer to stabilize confidence.

3. Ensemble Logic
- Weighted ensemble across fundamental, technical, quant, and regime signals.
- Dynamic reweighting based on recent out-of-sample performance.

4. Risk and Allocation Logic
- Volatility targeting.
- ATR-based stop logic and position scaling.
- Max drawdown-based exposure throttling.

## 3. Product-Level Decision Logic

## 3.1 Pre-Landing Universe Rules
- Select symbols that pass risk and data-quality gates.
- Rank by composite score with cap-tier quota controls.
- Refresh weekly for swing horizon.

## 3.2 Prediction Acceptance Rules
- Accept predictions only if:
  - Regime confidence is above threshold.
  - Signal agreement exists across at least two analysis families.
  - Liquidity and tradability checks pass.

## 3.3 Capital Protection Rules
- Lower exposure during high-volatility stress regimes.
- Reject new entries when model confidence and market breadth diverge.
- Trigger watchlist downgrade after repeated false-signal streaks.

## 4. Suggested Architecture Priority (Swing First)

Phase A:
- Dow trend state machine.
- Basic regime classifier.
- Composite ranking with risk penalties.

Phase B:
- Add HMM or change-point detector.
- Add dynamic ensemble weights by regime.

Phase C:
- Add adaptive allocation layer and confidence-aware throttling.

## 4.1 Weighted Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness: 1 (low) to 5 (high)
- Complexity: 1 (low) to 5 (high)
- Data cost: 1 (low) to 5 (high)

Weighted priority formula:
Priority Score = 0.60 x Usefulness - 0.25 x Complexity - 0.15 x Data Cost

| Theory or Algorithm | Usefulness | Complexity | Data Cost | Priority Score | Recommendation |
| --- | ---: | ---: | ---: | ---: | --- |
| Dow Theory trend state machine | 5 | 2 | 1 | 2.35 | Implement now |
| Trend-following continuation rules | 5 | 2 | 1 | 2.35 | Implement now |
| Mean-reversion in sideways regime | 4 | 2 | 1 | 1.75 | Implement now |
| Market breadth confirmation | 4 | 3 | 2 | 1.35 | Implement now |
| Composite ensemble with static weights | 5 | 3 | 2 | 1.95 | Implement now |
| Regime rule-based classifier | 5 | 3 | 1 | 2.10 | Implement now |
| ATR-based risk throttling | 4 | 3 | 1 | 1.50 | Implement now |
| Dynamic ensemble reweighting | 4 | 4 | 2 | 1.10 | Implement next |
| Change-point detection | 3 | 4 | 2 | 0.80 | Implement next |
| Hidden Markov regime model | 3 | 5 | 2 | 0.55 | Implement later |
| Advanced sentiment NLP layer | 3 | 4 | 4 | 0.70 | Implement later |

Interpretation rules:
- Priority score >= 1.50: implement now.
- Priority score 1.00 to 1.49: implement next.
- Priority score < 1.00: implement later.

## 4.2 Architecture Backlog by Priority Bucket

Implement now:
- Dow Theory trend state machine.
- Regime rule-based classifier.
- Trend-following and mean-reversion strategy switch by regime.
- Breadth confirmation and ATR risk throttling.
- Static weighted ensemble across fundamental, technical, quant, and regime signals.

Implement next:
- Dynamic ensemble reweighting based on rolling out-of-sample performance.
- Change-point detection as a secondary regime transition signal.

Implement later:
- Hidden Markov regime model.
- Advanced sentiment enrichment beyond lightweight headline polarity.

## 5. Theory Activation Architecture

### The Core Question
We have Dow Theory, Wyckoff, Mean Reversion, Trend Following, and Market Breadth. Can we use all of them at once? No — they are designed for different market conditions and using all simultaneously would produce conflicting signals that cancel each other out.

### The Answer: Regime-Conditional Theory Activation
The **regime label** (bull_trend, bear_trend, sideways, high_vol) is the switch that determines which theory is dominant. This is already designed in the regime detection architecture. The connection to theories is formalized here.

### Theory Activation Map

| Theory | bull_trend | bear_trend | sideways | high_vol | Role |
| --- | --- | --- | --- | --- | --- |
| **Dow Theory** | Foundation | Foundation | Foundation | Foundation | Always active. Identifies the primary trend direction. The baseline before anything else. |
| **Trend Following** | Primary | Primary | Suppressed | Suppressed | Active when trend is clear. Momentum continuation setups have high probability. |
| **Mean Reversion** | Suppressed | Suppressed | Primary | Suppressed | Active only in range-bound sideways regimes. Trend-following fails here; extremes tend to revert. |
| **Wyckoff Cycle** | Context enricher | Context enricher | Context enricher | Context enricher | Always active as a context layer. Tells you WHERE in the cycle a stock is (accumulation, markup, distribution, markdown). Does not drive trade direction on its own. |
| **Market Breadth** | Quality filter | Quality filter | Quality filter | Hard gate | Always active as a quality filter. In high-vol stress, weak breadth is a hard gate — no new entries if breadth is deteriorating. |

### What "Suppressed" Means
- Suppressed does not mean the signal is deleted. Its feature value is still in the Gold feature row.
- The ML model learns from training data that trend-following features have low predictive power in sideways regimes and automatically down-weights them during inference.
- The regime label is a feature — the model discovers the activation relationship from data. No manual signal switching is required inside the model.

### For Universe Scoring (Composite Weights)
Universe selection composite weights shift by regime to reflect which theory is dominant:

| Analysis Domain | bull_trend | bear_trend | sideways | high_vol |
| --- | --- | --- | --- | --- |
| Technical (trend signals) | 40% | 20% | 20% | 15% |
| Fundamental | 20% | 30% | 30% | 30% |
| Quant (momentum/vol) | 25% | 20% | 20% | 20% |
| Sentiment | 5% | 5% | 5% | 5% |
| Risk penalty (subtractive) | 10% | 25% | 25% | 30% |

In bull_trend, technical momentum signals (Dow/Trend Following) dominate. In bear_trend and sideways, quality and risk gates (Wyckoff distribution awareness, Mean Reversion) are elevated. In high_vol, risk penalty is maximum and all positive signals are down-weighted.

### How Wyckoff Works Without Switching
Wyckoff is never "on" or "off" — it is always embedded as feature context:
- `wyckoff_accumulation_proxy` is high → suggests a stock is being quietly bought (like early markup phase). This makes the technical and momentum signals more trustworthy when they fire.
- `wyckoff_distribution_proxy` is high → suggests smart money is selling. A positive Dow trend signal is less reliable when Wyckoff says distribution is underway.
- The ML model learns this interaction through training. No hard rule needed.

### Summary: How a Prediction Is Actually Made
1. Regime detection runs → outputs regime_label (e.g., bull_trend).
2. All features from all 8 groups are computed (technical, volume, volatility, candlestick, regime context, etc.) — theories are encoded as features, not as rules.
3. The ML model predicts direction using all features, but the regime_label feature causes it to weight theory-relevant features differently per regime.
4. For universe selection, composite weights shift to the regime-appropriate table above.
5. The R:R trade management (ATR stop/target) runs after the ML signal fires — this is Dow Theory's "trend confirmation before entry" translated into a quantitative rule.

---

## 6. Governance Requirements
- Version every theory-to-rule mapping.
- Keep threshold values in policy docs, not hardcoded in implementation.
- Track all overrides with reason, approver, and timestamp.
