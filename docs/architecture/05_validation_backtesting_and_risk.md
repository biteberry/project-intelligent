# 05 Validation, Backtesting, and Risk

## Validation Method
- Time-series split only.
- Walk-forward evaluation.
- Independent evaluation per trading horizon.

## Model Metrics
Classification:
- Accuracy
- Precision and recall
- F1
- ROC-AUC
- Directional accuracy by cap tier

Regression:
- MAE
- RMSE
- MAPE
- Correlation of predicted versus realized returns
- MAE and RMSE by cap tier

## Trading Metrics
- Cumulative return
- Sharpe ratio
- Max drawdown
- Win rate (label_direction_1d accuracy)
- R:R win rate (proportion of label_rr_outcome_5d = win among all valid trades)
- R:R average return (mean of label_rr_return_5d across all valid trades)
- Timeout rate (proportion of trades exiting at max hold without hitting stop or target)
- Turnover-adjusted returns with cost assumptions

## 1:2 Risk-Reward Backtest Simulation
The backtest must simulate real swing trade execution using the R:R labels defined in doc 11.

### Simulation Rules
- Every row where the model predicts direction = 1 and confidence >= threshold is treated as a trade entry.
- Entry price: open price of T+1 (the next trading day after signal).
- Stop loss: entry_price - (1 × ATR_14 at T). ATR_14 is from the feature set at date T (no look-ahead).
- Take profit: entry_price + (2 × ATR_14 at T).
- Scan T+1 through T+5 using daily high and low to determine exit.
- If daily low crosses stop level: trade closed at stop loss price (loss).
- If daily high crosses target level: trade closed at take profit price (win).
- Priority on same day where both could be hit: stop loss takes priority (conservative).
- If neither hit by end of T+5 close: trade closed at adj_close_t+5 (timeout).

### Cost Assumptions for Backtest
Cost assumptions differ by market_context because Indian markets have mandatory statutory charges that US markets do not.

#### market_context = india (NSE/BSE equity delivery)
| Cost Component | Rate | Notes |
| --- | --- | --- |
| STT (Securities Transaction Tax) | 0.10% on sell side only | SEBI-mandated statutory tax. Non-negotiable. Applied on sell value only. |
| Exchange transaction charges | ~0.00345% (NSE) | Both sides. |
| SEBI turnover fee | ~0.0001% | Both sides. |
| GST on brokerage | 18% of brokerage amount | Applied on broker fee only |
| Stamp duty | 0.015% on buy side | Varies by state but standardized for equity delivery |
| Slippage | 0.10% per trade entry and exit | Indian mid/small cap liquidity is thinner than US |
| **Total round-trip cost estimate** | **~0.50%** | Conservative. Large-cap liquid NSE stocks ≈ 0.35%; small-cap ≈ 0.60%+ |

#### market_context = us (NYSE/NASDAQ equity)
| Cost Component | Rate | Notes |
| --- | --- | --- |
| Commission | 0% | Most retail brokers (Zerodha US / IBKR lite) are commission-free |
| SEC fee | ~0.00278% on sell side | Negligible |
| Slippage | 0.05% per trade entry and exit | Round-trip = 0.10% |
| **Total round-trip cost estimate** | **~0.10%** | Current assumption unchanged |

**Backtest rule:** Every trade's P&L must be reduced by the market_context-appropriate round-trip cost before computing win/loss and Sharpe ratio. Mixed-market portfolios must apply costs per symbol, not a single blended rate.

### Backtest Report Must Include
- ML model accuracy: directional accuracy on label_direction_1d (out-of-sample).
- R:R win rate: percentage of trades where label_rr_outcome_5d = win.
- R:R average P&L per trade after costs.
- Timeout rate: percentage of trades reaching max hold.
- Sharpe ratio of the R:R trade sequence.
- Max drawdown of the R:R trade sequence.
- All metrics broken down by cap_tier.
- Comparison against buy-and-hold benchmark for the same period.

## Horizon-Specific Risk Views
- Intraday: slippage and latency sensitivity
- Swing: overnight gap exposure and average hold performance
- Long: drawdown resilience across regimes

## Guardrails

### G1 - Data Splitting
- Time-series random splits are strictly prohibited; walk-forward evaluation only.
- Any validation result produced with a non-temporal split is invalid and discarded.

### G2 - Look-Ahead Bias
- Any validation window where training data contains observations after the evaluation start date is immediately invalidated.
- Look-ahead violations trigger a pipeline halt and mandatory review.

### G3 - Transaction Costs
- All backtest results must include slippage and transaction cost assumptions.
- Backtest reports without cost assumptions are marked incomplete and not accepted for model promotion decisions.

### G4 - Benchmark Requirement
- Every backtest report must include a comparison against the buy-and-hold benchmark.
- Reports without a benchmark comparison are incomplete and not accepted.

### G5 - Minimum Backtest Window
- Backtest must cover at least 252 trading days (one full year) to be considered valid.
- Shorter backtests are flagged as insufficient and cannot support model promotion.

### G6 - Per-Tier Reporting
- Validation reports that do not include cap-tier breakdowns (large, mid, small) are incomplete.
- Overall-only metrics are insufficient for architecture sign-off.

### G7 - Overfitting Check
- If in-sample performance exceeds out-of-sample performance by more than 20 percentage points on the primary metric, the model is flagged for review and blocked from promotion.

### G8 - Drawdown Ceiling
- Models with max drawdown exceeding the defined threshold during backtest evaluation are not promoted to serving.
- The drawdown threshold is defined in the governance policy document and reviewed per phase.

### G9 - R:R Simulation Is Mandatory
- Every swing model backtest must include the 1:2 R:R trade simulation, not only raw directional accuracy.
- A backtest report that evaluates only label_direction_1d accuracy without simulating stop/target exits is incomplete and not accepted for model promotion.

### G10 - ATR Used for R:R Must Match Feature ATR
- The ATR_14 value used to compute stop and target levels in the backtest must be the same ATR_14 stored in the Gold feature row for date T.
- Using a separately computed ATR for backtest simulation that differs from the feature is a data consistency violation.
