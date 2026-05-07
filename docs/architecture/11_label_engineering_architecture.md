# 11 Label Engineering Architecture

## Purpose
Define how swing trading labels are constructed, what edge cases are handled, how label validity is determined, and how labels are versioned and governed in the Gold layer.

---

## Design Principles

1. Labels use adjusted prices. Splits and dividends must not create artificial direction signals.
2. Labels are point-in-time. A label at date T uses only data at T+1 (ML target) or T+1 through T+5 (R:R evaluation).
3. Label validity is explicit. Every label row carries an is_label_valid flag.
4. Edge cases have defined rules. Halts, suspensions, and data gaps have documented handling, not silent filling.
5. Labels are versioned. Any change to label definition produces a new label_version tag.
6. Two label types coexist. The 1-day label trains the ML model. The R:R outcome label evaluates trade performance in backtesting.

---

## Swing Label Definition

### Primary ML Target: 1-Day Forward Prediction
The ML model is trained to predict the next trading day's direction.
This daily prediction signal is used to decide whether to enter a swing trade.

### Label Types - Primary (Both Computed for Every Row)

#### Direction Label (Classification Target)
- Name: `label_direction_1d`
- Type: integer
- Values: `1` = next day close is higher than or equal to today's close, `0` = next day close is lower
- Formula: `1 if adj_close_t+1 >= adj_close_t else 0`
- Threshold: 0.0% (no dead-zone in Phase 1)
- Phase 2 consideration: introduce a dead-zone (e.g., exclude rows where |return| < 0.3%) to remove noise near zero.

#### Return Label (Regression Target)
- Name: `label_return_1d`
- Type: float
- Formula: `(adj_close_t+1 / adj_close_t) - 1`
- Expressed as a decimal (0.015 = +1.5%, -0.008 = -0.8%).

### Label Types - Secondary (R:R Outcome for Backtest Evaluation)
This label simulates the real-world outcome of a 1:2 risk-reward swing trade entered on signal date T.

#### R:R Outcome Label
- Name: `label_rr_outcome_5d`
- Type: string
- Values:
  - `win` = take profit level (entry + 2 × ATR_14) was hit before stop loss level (entry - 1 × ATR_14) within 5 trading days
  - `loss` = stop loss level was hit before take profit level within 5 trading days
  - `timeout` = neither level was hit within 5 trading days; trade exited at T+5 close
  - `invalid` = trade could not be simulated (missing data, halt, or is_label_valid = false)
- Computation inputs:
  - entry_price = open price of T+1 (market open after signal)
  - atr_14 = ATR_14 computed at date T (no look-ahead)
  - stop_level = entry_price - (1 × atr_14)
  - target_level = entry_price + (2 × atr_14)
  - scan days T+1 through T+5: check if daily low crosses stop_level or daily high crosses target_level
  - if both could be hit on the same day: stop loss takes priority (conservative)
- Note: this label is not used to train the ML model. It is used only in backtest evaluation.

#### R:R Return Label
- Name: `label_rr_return_5d`
- Type: float
- The actual P&L fraction realized:
  - `win`: `(target_level - entry_price) / entry_price`
  - `loss`: `(stop_level - entry_price) / entry_price` (negative)
  - `timeout`: `(adj_close_t+5 - entry_price) / entry_price`
  - `invalid`: null

### Reference Date Alignment
- `adj_close_t`: adjusted close on the prediction date T (already known at prediction time).
- `adj_close_t+1`: adjusted close 1 trading day after T (primary ML label outcome).
- `open_t+1`: open price 1 trading day after T (R:R entry price).
- `adj_close_t+5`: adjusted close 5 trading days after T (timeout exit price for R:R label).
- Calendar days are not counted. Trading days only. If T is a Friday, T+1 is Monday.
- Non-trading days (weekends, public holidays) are skipped automatically using the observed trading calendar.

---

## Trading Calendar

- US trading calendar is the reference for all trading day offsets.
- Source: pandas_market_calendars library (free, open source) or a pre-built NYSE calendar file.
- Public holidays where the market is closed: New Year's Day, MLK Day, Presidents' Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, Christmas.
- Early-close days are treated as normal trading days for daily OHLCV; no special handling needed for daily bars.

---

## Edge Case Handling

### Case 1 - Trading Halt on T+1 (Next Day)
- Definition: the symbol has no trading record on T+1.
- Rule: if adj_close_t+1 is missing, the 1-day ML labels are invalid.
- Action: set `is_label_valid = false`, set `label_direction_1d = null`, set `label_return_1d = null`, set `label_rr_outcome_5d = invalid`.
- Rationale: if the stock cannot trade the next day, the entry cannot be executed; the entire label row is invalid.

### Case 2 - Stock Delisted on or Before T+1
- Definition: the symbol stops trading permanently on or before T+1.
- Rule: same as Case 1. Missing adj_close_t+1 → label invalid.
- Action: same as Case 1.
- Additional action: flag the symbol for removal from the universe at the next weekly selection run.

### Case 3 - Stock Split on T+1
- Definition: a stock split occurs on T+1.
- Rule: use adjusted close prices at both T and T+1.
- Since adj_close is backward-adjusted by yfinance, both T and T+1 adj_close prices already reflect the split.
- No special handling needed at the 1-day ML label layer.
- For the R:R label: if a split occurs within T+1 to T+5, the stop and target levels (computed from pre-split ATR) may be distorted. Flag `label_rr_outcome_5d = invalid` if a split is detected in the T+1 to T+5 window.

### Case 4 - Dividend During Forward Window
- Definition: a dividend is paid between T and T+5.
- Rule: same as Case 3. adj_close is dividend-adjusted; label calculation is unaffected.
- No special handling needed at the label layer.

### Case 5 - Missing Forward Price (Data Gap, Not Halt)
- Definition: adj_close_t+5 is missing due to a data provider gap (yfinance outage, API error), not a market event.
- Rule: if the Silver record for T+5 exists with is_valid_row = false or adj_close is null for reasons other than a market halt, the label is invalid.
- Action: same as Case 1.
- The data gap should be resolved at ingestion and Silver before it propagates to Gold labels.

### Case 6 - Price at T+1 Is Unreasonably Extreme
- Definition: `abs(label_return_1d) > 0.20` (more than 20% move in 1 day).
- Rule: flag for review. A 20%+ single-day move is rare but can be real (earnings, merger, short squeeze).
- Action: set `label_extreme_flag = true`. The row remains valid for training unless manually reviewed and invalidated.
- Log count of extreme flags per Gold build in the audit record.

### Case 7 - Prediction Date T Itself Has No Trade
- Definition: the symbol has no trading record on date T (missing from Silver for date T).
- Rule: no label can be computed if the anchor price adj_close_t is unknown.
- Action: no label row is created for that symbol and date. The gap is logged in the audit record.

### Case 8 - R:R Window Has Missing Days (T+2 to T+5)
- Definition: adj_close, high, or low data is missing for one or more days in T+2 through T+5, but T+1 is valid.
- Rule: the 1-day ML labels (label_direction_1d and label_return_1d) remain valid.
- Action: set `label_rr_outcome_5d = invalid` and `label_rr_return_5d = null`. The ML labels are still used for training; only the R:R backtest evaluation is affected.

---

## Label Validity Flag

Every label row in Gold carries `is_label_valid`:

| Value | Meaning |
| --- | --- |
| true | Label is fully computed and trusted for training |
| false | Label is null or unreliable due to a data edge case |

Training jobs filter to `is_label_valid = true` before fitting. This is enforced by the same guardrail as `is_valid_row` in the feature layer.

---

## Class Balance Monitoring

### Monitoring Threshold
- After each Gold build, compute the class distribution of `label_direction_5d` across all valid rows.
- If the dominant class exceeds 70% of all valid rows, log a class imbalance warning in the audit record.
- If the dominant class exceeds 80%, raise a CloudWatch alert and flag for model strategy review.

### Action on Imbalance
- Class imbalance does not automatically block model training.
- Models must handle imbalance through class weighting or sampling strategy (defined in model strategy architecture).
- Architecture alert is the signal; the model design decision is separate.

---

## Label Version Policy

### What Triggers a New Label Version
- Any change to the label formula (e.g., changing the return threshold from 0.0% to 0.5%).
- Any change to the forward window length (e.g., changing 5-day to 3-day).
- Any change to edge case handling rules.

### How Versioning Works
- Each Gold build is tagged with a `label_version` string (example: `v1.0.0`).
- label_version is stored in the Gold Iceberg snapshot metadata alongside feature_version.
- label_version and feature_version together form the full Gold snapshot contract.
- A model artifact records both the feature_version and label_version it was trained on.
- Inference jobs verify both versions match before running.

### Label Version History
- label_version v1.0.0: 1-day direction and return labels (primary ML targets), 1:2 R:R outcome label over 5-day max hold window, 0.0% direction threshold, no dead-zone, as defined in this document.
- Future versions are documented by appending to this section.

---

## Gold Label Schema Fields

| Field | Type | Notes |
| --- | --- | --- |
| symbol | string | Ticker |
| date | date | Prediction date T |
| cap_tier | string | large, mid, or small; mandatory |
| horizon | string | swing; mandatory in Phase 1 |
| label_direction_1d | integer | 1 or 0; primary ML classification target; null if is_label_valid = false |
| label_return_1d | float | 1-day decimal return; primary ML regression target; null if is_label_valid = false |
| label_rr_outcome_5d | string | win / loss / timeout / invalid; R:R backtest evaluation only |
| label_rr_return_5d | float | Actual P&L fraction for the R:R trade; null if invalid |
| is_label_valid | boolean | True if 1-day ML labels are usable for training |
| label_extreme_flag | boolean | True if abs(label_return_1d) > 0.20 |
| label_version | string | Version tag of this label definition |
| gold_snapshot_id | string | Iceberg snapshot ID of this Gold build |

---

## Label Audit Record

Each Gold build writes a label audit record to DynamoDB:

| Field | Content |
| --- | --- |
| gold_snapshot_id | Snapshot ID |
| total_label_rows | Total rows attempted |
| valid_label_rows | Rows with is_label_valid = true |
| invalid_label_rows | Rows with is_label_valid = false |
| extreme_flag_rows | Rows with label_extreme_flag = true |
| direction_1_count | Count of label_direction_1d = 1 |
| direction_0_count | Count of label_direction_1d = 0 |
| rr_win_count | Count of label_rr_outcome_5d = win |
| rr_loss_count | Count of label_rr_outcome_5d = loss |
| rr_timeout_count | Count of label_rr_outcome_5d = timeout |
| rr_invalid_count | Count of label_rr_outcome_5d = invalid |
| class_imbalance_flag | True if dominant class > 70% |
| label_version | Version tag used for this build |

---

## Guardrails

### G1 - No Future Data in Labels
- adj_close_t+5 is the only forward-looking value used in label computation.
- No other field from T+1 through T+5 may be used to derive label values (e.g., using the high or volume of forward days is prohibited).
- Violations are detected by the feature-label alignment check at Gold build time and halt the pipeline.

### G2 - Adjusted Price Mandatory
- Labels must be computed from adj_close, never from unadjusted close.
- Any label computation using unadjusted close is rejected at Gold build time.

### G3 - Edge Case Rules Are Not Optional
- The handling rules for halts, delistings, and data gaps defined in this document are mandatory.
- Silently forward-filling or zero-filling missing forward prices to produce a label is a data integrity violation.

### G4 - is_label_valid Must Be Set
- Every label row must carry an explicit is_label_valid value.
- Null or absent is_label_valid is treated as false by all training jobs.

### G5 - Training Filter Mandatory
- All training jobs must apply `WHERE is_label_valid = true AND is_valid_row = true` before fitting.
- This filter is enforced by the training job's pre-training data quality check.

### G6 - Label Version Lock
- A model artifact must record the label_version it was trained on.
- Inference on a Gold snapshot with a different label_version is blocked.
- This prevents silent label drift from affecting served predictions.

### G7 - Class Balance Alert
- Gold builds that produce more than 70% of one class must write a class imbalance flag to the audit record.
- Gold builds that produce more than 80% of one class must raise a CloudWatch alert.
- Ignoring a class imbalance alert blocks model promotion until the issue is reviewed and documented.
