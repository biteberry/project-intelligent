# 04 Model Strategy and Serving

## Strategy
Start simple and auditable, then increase complexity only after consistent validation gains.

## Horizon Strategy
- Intraday: separate product line, deferred for phase 1.
- Swing: primary starting horizon.
- Long: phase 2 expansion.

## Cap-Tier Strategy
- Phase 1: single model with cap_tier as a feature.
- Phase 2: compare to separate models for each cap tier.

## Target Design
- Direction classification (primary ML target)
- Return regression (secondary ML target)
- Horizon-specific targets:
  - Swing: 1-day forward direction and 1-day forward return
  - The 1-day prediction fires the entry signal; trade management (see below) governs how long the position is held

## Trade Management Architecture (1:2 Risk-Reward)
Once a prediction signal fires (predicted direction = 1, confidence above floor), a swing trade is entered with the following exit rules:

### Entry
- Signal fires at market close on date T.
- Entry execution: market open of T+1.
- Entry price reference: open price of T+1 (used in backtesting and live paper trading).

### Stop Loss (Risk = 1R)
- Stop loss level: entry_price - (1 × ATR_14_at_T)
- ATR_14 is computed at date T (fully known at signal time; no look-ahead).
- If stop loss is hit intraday (low price of any day T+1 through T+5 crosses below stop level), the trade is closed at stop loss price.

### Take Profit (Reward = 2R)
- Take profit level: entry_price + (2 × ATR_14_at_T)
- If take profit is hit intraday (high price of any day T+1 through T+5 crosses above take profit level), the trade is closed at take profit price.

### Maximum Hold Period
- If neither stop loss nor take profit is hit within 5 trading days, the trade is closed at the close price of T+5.
- This is the swing horizon: maximum hold is 5 trading days.
- Outcome of a timeout exit is logged as neither win nor loss; the actual P&L is the T+5 close minus entry price.

### Exit Priority Rule
- On any given day, if both stop and target could theoretically be hit (wide daily range), stop loss takes priority (conservative assumption).
- This is the cautious default for backtesting; it slightly understates strategy performance.

### Risk-Reward Label for Backtesting
- Each trade entry at T has a computed label: `label_rr_outcome_5d`
- Values: `win` (target hit first), `loss` (stop hit first), `timeout` (max hold reached)
- This label is stored in Gold alongside the 1-day ML labels and used exclusively for trade performance backtesting.

## Feature Groups
- Price returns and rolling statistics
- Technical indicators (RSI, MACD, ATR, Bollinger, SMA crossover)
- Volume behaviour (including OBV and OBV divergence, A/D line, MFI)
- Volatility and regime descriptors (market_context-aware: Nifty 50 + India VIX for India; S&P 500 + CBOE VIX for US)
- Calendar and earnings event features (days_to_next_earnings, earnings_blackout_flag, pre_earnings_zone_flag)
- Candlestick patterns (Hammer, Engulfing, Shooting Star, Doji)
- Institutional positioning (institutional_ownership_pct, FII/DII change quarter-over-quarter)
- India-specific regulatory risk features (promoter pledging, circuit breaker flags)
- 52-week high/low proximity, relative strength vs Nifty 50
- Delivery percentage features (NSE only — genuine accumulation vs intraday speculation)
- Support and resistance level proximity (swing high/low 20-day, pivot detection)

## Prediction Serving Gate: Earnings Blackout

Before a prediction is served to any consumer (API response or downstream system), the serving layer applies a set of non-overridable gates:

| Gate | Condition | Action |
| --- | --- | --- |
| Earnings blackout | `earnings_blackout_flag = 1` (result within 2 trading days) | Prediction is suppressed. Reason logged as `earnings_blackout`. Not actionable. |
| Circuit breaker active | `upper_circuit_flag = 1` OR `lower_circuit_flag = 1` (India only) | Prediction is suppressed. Reason logged as `circuit_frozen`. Cannot execute. |
| Confidence floor | Model confidence below configured threshold | Prediction suppressed (existing G3 gate). |
| Model staleness | Model trained on snapshot older than 30 days | Prediction suppressed (existing G7 gate). |

**Why earnings blackout is a hard gate, not a soft signal:**
The 1:2 R:R model uses ATR-14 as the stop distance. ATR-14 is the average daily range over 14 trading days. On a result day, the stock can move 4–10× its daily ATR in one gap. The stop loss is meaningless — the position will gap through it with a loss far larger than 1R. No amount of ML confidence justifies entering before a binary event of unknown direction. This gate is not configurable to off.

## Position Sizing Architecture

The 1:2 R:R trade management defines *when* to exit. Position sizing defines *how much capital* to allocate to each trade. Without this, the platform generates signals with no framework for actual capital deployment.

### Core Principle: Risk a Fixed Fraction of Portfolio Per Trade
The only quantity that should be fixed is the rupee risk per trade, not the number of shares or the percentage of capital. This way, every trade risks the same amount regardless of the stock's price or volatility.

### Position Size Formula
```
Risk per trade (₹) = Total portfolio capital × risk_pct_per_trade
ATR stop distance (₹) = ATR_14_at_T × stop_atr_multiplier
Position size (shares) = Risk per trade / ATR stop distance
Position value (₹) = Position size × entry_price
```

**Example (India, ₹10 lakh portfolio, 1% risk per trade):**
- Portfolio capital: ₹10,00,000
- Risk per trade: 1% = ₹10,000
- Stock: Reliance.NS, Entry price: ₹1,500, ATR_14 = ₹30
- Stop distance = 1 × ₹30 = ₹30 (stop at ₹1,470)
- Position size = ₹10,000 / ₹30 = 333 shares
- Position value = 333 × ₹1,500 = ₹4,99,500 (≈50% of portfolio in one trade)
- Position value cap applies: see Max Exposure Per Trade below

### Parameters (Config-Driven)
All parameters are defined in `configs/position_sizing.yaml` — not hardcoded.

| Parameter | Default Value | Notes |
| --- | --- | --- |
| risk_pct_per_trade | 1.0% | Percentage of total portfolio to risk on a single trade |
| max_position_pct | 20% | Maximum % of portfolio that can be in any single stock |
| max_open_positions | 5 | Maximum number of concurrent swing positions |
| max_sector_exposure_pct | 40% | Maximum % of portfolio in any single sector simultaneously |

### Position Value Cap
- Even if the formula yields a large position, the position value is capped at `max_position_pct` of portfolio.
- If the capped position implies a risk greater than `risk_pct_per_trade`, the position is not taken (the stock is too low volatility or too large for the risk budget).

### Why This Approach Is Correct for Swing Trading
- Fixed rupee risk ensures a string of losses does not accelerate capital erosion (drawdown is arithmetic, not geometric).
- ATR-based sizing ensures position size adjusts to the stock's current volatility — high-ATR stocks get smaller positions automatically.
- Max open positions (5) limits concentration. With 1% risk per trade and 5 positions, maximum simultaneous loss is 5% of portfolio if all 5 hit stop loss on the same day.

### Sizing in Backtesting
- Backtest P&L is reported both as percentage return AND in rupee terms using the formula above.
- Position sizing is applied in backtesting to make reported Sharpe ratio and max drawdown realistic, not theoretical.

---

## Serving Architecture
- Batch-first predictions for cost control.
- API surface for latest predictions, confidence, and metadata.
- Response includes horizon, cap_tier, market_context, and prediction serving gate status.

---

## Guardrails

### G1 - Look-Ahead Bias
- Any feature that uses data with a date on or after the prediction target date is rejected at feature build time.
- Look-ahead violations halt the gold build and raise an alert.

### G2 - Model Promotion
- A model is not promoted to serving unless it beats the naive baseline on directional accuracy by at least 2 percentage points on out-of-sample data.
- Models that do not pass promotion criteria are logged and archived but not served.

### G3 - Confidence Floor
- Predictions with confidence below the configured threshold are suppressed from API responses.
- Suppressed predictions are logged but never exposed to consumers.

### G4 - API Response Contract
- Every API response must include: symbol, date, horizon, cap_tier, prediction, and confidence.
- Responses missing any mandatory field are rejected before delivery.

### G5 - Snapshot Reference Integrity
- Serving jobs must reference a named, frozen gold snapshot version.
- Floating references to a latest pointer are not permitted in serving or training jobs.

### G6 - Horizon Isolation
- A swing model must not consume features derived from intraday or long-horizon windows.
- Cross-horizon feature contamination is detected at gold build time and causes a pipeline halt.

### G7 - Model Age
- A model trained on a gold snapshot older than 30 days is flagged as stale.
- Stale models are blocked from serving new predictions until retrained.

### G8 - Risk-Reward Parameters Are Config-Driven
- The stop loss multiplier (default 1×) and take profit multiplier (default 2×) are defined in configs/label_rules.yaml.
- Hard-coded R:R values in pipeline code are a guardrail violation.
- Changing R:R parameters requires a new label_version tag and a full Gold rebuild before any model is trained or backtested on the new parameters.

### G9 - Earnings Blackout Is Non-Overridable
- Any symbol with `earnings_blackout_flag = 1` (board meeting / result date within 2 trading days) must have its prediction suppressed at the serving layer.
- This gate cannot be disabled by configuration, manual override, or high model confidence.
- The blackout reason must be logged in the prediction audit table for every suppressed prediction.
