# Technical Analysis Architecture

## Purpose
Capture market behavior, trend, momentum, volatility, and entry timing for swing predictions.

## Indicator Families
1. Trend
- Moving averages, slope, crossover states

2. Momentum
- RSI, stochastic, rate of change

3. Volatility
- ATR, Bollinger bandwidth, realized volatility

4. Volume and participation
- OBV, volume spikes, volume trend

5. Price structure
- Breakout and pullback states, support and resistance zones

6. Candlestick patterns
- Single-candle reversal and continuation signals derived from OHLC geometry
- Hammer, inverted hammer, shooting star, doji, engulfing patterns
- Pattern validity requires trend context (e.g., hammer is only a bullish signal in a downtrend)

## Design Logic
- Use indicator states, not only raw values.
- Avoid redundant indicators with high overlap.
- Keep feature lagging rules explicit to avoid look-ahead bias.

## Guardrails

### G1 - Look-Ahead Bias
- All technical indicator computations must use only data on or before the feature date.
- Any forward-looking computation is rejected at gold build time and triggers a pipeline halt.

### G2 - Minimum History
- Indicators requiring an N-day window must have at least N days of valid, non-null price history.
- Symbols with insufficient history are excluded from that indicator and flagged; they do not receive a partial estimate.

### G3 - Indicator Redundancy
- Adding two indicators from the same family with high pairwise correlation requires architecture justification and review before inclusion.
- Redundant indicators inflate feature noise and are actively avoided.

### G4 - State Over Raw Values
- Indicator raw values must be converted to states or normalized scores before entering the gold feature table.
- Raw unnormalized values are not accepted as standalone features.

### G5 - NaN Rate
- Features with NaN values exceeding 5% of rows for a symbol block that symbol from gold promotion until resolved.

### G6 - Daily Recompute
- Technical scores and states must be recomputed on every daily batch run.
- Stale technical states carried forward from a prior day without recompute are not accepted.

## Swing-Oriented Windows
- 5 to 20 trading day context windows.
- Daily timeframe baseline.

## Output Fields
- technical_score
- trend_state
- momentum_state
- volatility_state
- setup_quality
- technical_as_of_date

---

## Technical Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Indicator / Signal | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Trend state | MA slope, crossover, price vs MA | 5 | 1 | 5 | 4.30 | Must-have now |
| ATR (volatility) | Average true range, band width | 5 | 1 | 5 | 4.30 | Must-have now |
| RSI (momentum) | 14-day RSI level and slope | 5 | 1 | 5 | 4.30 | Must-have now |
| Bollinger bands | Band width, price position | 4 | 2 | 5 | 3.10 | Must-have now |
| MACD | Signal, histogram, crossover | 4 | 2 | 5 | 3.10 | Must-have now |
| Volume trend | OBV, volume z-score | 4 | 2 | 5 | 3.10 | Must-have now |
| Price structure state | Breakout and pullback detection | 5 | 3 | 5 | 2.90 | Must-have now |
| Hammer candlestick | Bullish reversal: long lower shadow, small body at top | 4 | 2 | 5 | 3.10 | Must-have now |
| Engulfing pattern | Bullish/bearish engulfing candle | 4 | 2 | 5 | 3.10 | Must-have now |
| Shooting star | Bearish reversal: long upper shadow, small body at bottom | 3 | 2 | 5 | 2.60 | Add next |
| Doji | Indecision: open ≈ close, long shadows | 3 | 1 | 5 | 2.80 | Add next |
| Stochastic oscillator | %K and %D crossover | 3 | 2 | 5 | 2.60 | Add next |
| Rate of change | ROC over 5 and 10 days | 3 | 1 | 5 | 2.80 | Add next |
| Support and resistance zones | Pivot level derivation | 4 | 4 | 4 | 2.40 | Add next |
| Volume spike detection | Abnormal volume flag | 3 | 3 | 5 | 2.40 | Add next |
| Ichimoku cloud | Cloud, kijun, tenkan lines | 3 | 4 | 5 | 2.20 | Add later |

Interpretation:
- Priority score >= 2.80: must-have for swing now.
- Priority score 2.20 to 2.79: add next.
- Priority score < 2.20: add later.

## Technical Architecture Backlog for Swing

Must-have now:
- Trend state from moving average structure.
- ATR for volatility and stop sizing.
- RSI for momentum and overbought/oversold context.
- Bollinger bands and MACD for continuation signals.
- Volume trend confirmation.
- Price structure state (breakout, pullback).
- Hammer candlestick pattern (bullish reversal at downtrend low).
- Bullish and bearish engulfing candlestick patterns.

Add next:
- Rate of change, stochastic, volume spike flag.
- Support and resistance zone proximity.
- Shooting star (bearish reversal at uptrend high).
- Doji (indecision candle at key levels).

Add later:
- Ichimoku cloud composite.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Trend state: 25%
- Momentum (RSI, MACD): 20%
- Volatility (ATR, Bollinger): 20%
- Price structure quality: 20%
- Volume confirmation: 15%
