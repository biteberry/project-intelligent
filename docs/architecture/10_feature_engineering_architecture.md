# 10 Feature Engineering Architecture

## Purpose
Define all features, their window sizes, normalization strategy, missing value handling, versioning policy, and governance rules for the Gold feature layer. Applies to swing horizon only in Phase 1.

---

## Design Principles

1. No look-ahead bias. Every feature value at date T uses only data available strictly before T.
2. Adjusted prices only. All price-derived features use adj_close from Silver.
3. Feature versioning. Any change to a feature calculation produces a new Gold snapshot version; no silent recalculation on existing snapshots.
4. Reproducibility. A gold snapshot ID uniquely identifies the exact feature set used to train or evaluate any model.
5. Cap-tier tags mandatory. Every feature row carries cap_tier and horizon; rows missing these tags are invalid.

---

## Feature Groups and Specifications

### Group 1 - Price Return Features

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| return_1d | (adj_close_t / adj_close_t-1) - 1 | 1 day | Most recent daily return |
| return_5d | (adj_close_t / adj_close_t-5) - 1 | 5 days | Trailing week return |
| return_10d | (adj_close_t / adj_close_t-10) - 1 | 10 days | Trailing two-week return |
| return_21d | (adj_close_t / adj_close_t-21) - 1 | 21 days | Trailing month return |
| return_63d | (adj_close_t / adj_close_t-63) - 1 | 63 days | Trailing quarter return |

Minimum history required to compute all return features: 63 trading days.

---

### Group 2 - Rolling Statistical Features

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| rolling_mean_return_5d | Mean of daily returns over 5 days | 5 days | Short-term return tendency |
| rolling_mean_return_21d | Mean of daily returns over 21 days | 21 days | Monthly return tendency |
| rolling_std_return_5d | Std dev of daily returns over 5 days | 5 days | Short-term volatility proxy |
| rolling_std_return_21d | Std dev of daily returns over 21 days | 21 days | Monthly volatility proxy |
| rolling_skew_21d | Skewness of daily returns over 21 days | 21 days | Return distribution shape |
| rolling_kurt_21d | Kurtosis of daily returns over 21 days | 21 days | Tail risk indicator |

---

### Group 3 - Technical Indicator Features

| Feature Name | Specification | Lookback Window | Notes |
| --- | --- | --- | --- |
| rsi_14 | RSI with period 14 | 14 days | Wilder smoothing; values 0-100 |
| macd_line | EMA(12) - EMA(26) of adj_close | 26 days minimum | Raw MACD line |
| macd_signal | EMA(9) of macd_line | 9 days additional | Signal line |
| macd_histogram | macd_line - macd_signal | 35 days total | Momentum divergence |
| atr_14 | Average True Range with period 14 | 14 days | Volatility in price units |
| atr_14_pct | atr_14 / adj_close | 14 days | Normalised ATR as % of price |
| bb_upper | 20-day SMA + 2 × 20-day std of adj_close | 20 days | Bollinger upper band |
| bb_lower | 20-day SMA - 2 × 20-day std of adj_close | 20 days | Bollinger lower band |
| bb_pct | (adj_close - bb_lower) / (bb_upper - bb_lower) | 20 days | Position within Bollinger bands; values 0-1 |
| bb_width | (bb_upper - bb_lower) / 20-day SMA | 20 days | Band width as volatility measure |
| sma_10 | Simple moving average of adj_close over 10 days | 10 days | Short-term trend reference |
| sma_50 | Simple moving average of adj_close over 50 days | 50 days | Medium-term trend reference |
| price_vs_sma_10 | (adj_close / sma_10) - 1 | 10 days | Distance above/below short-term MA |
| price_vs_sma_50 | (adj_close / sma_50) - 1 | 50 days | Distance above/below medium-term MA |
| sma_cross_signal | 1 if sma_10 > sma_50 else -1 | 50 days | Golden/death cross binary signal |

Minimum history required to compute all technical features: 50 trading days.

#### 52-Week High and Low Proximity Features
The 52-week high and low are the most widely watched price reference levels in swing trading. Breakout above 52-week high is one of the strongest momentum signals — institutional buyers accelerate when a stock clears its yearly high. Proximity to 52-week low acts as a potential support level and mean-reversion setup.

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| high_52w | Maximum of adj_close over past 252 trading days | 252 days | 52-week high price level |
| low_52w | Minimum of adj_close over past 252 trading days | 252 days | 52-week low price level |
| pct_from_52w_high | (adj_close - high_52w) / high_52w | 252 days | 0 = at the high. Negative = how far below the high. -0.05 = 5% below 52W high (near breakout). -0.50 = 50% below (deep correction). |
| pct_from_52w_low | (adj_close - low_52w) / low_52w | 252 days | Positive = how far above the 52W low. Near 0 = testing yearly support. |
| near_52w_high_flag | 1 if pct_from_52w_high > -0.05 else 0 | 252 days | Stock is within 5% of its 52-week high. Breakout zone. |
| near_52w_low_flag | 1 if pct_from_52w_low < 0.10 else 0 | 252 days | Stock is within 10% of its 52-week low. Support zone. |

#### Relative Strength vs Index (RS Rating)
Not the RSI indicator. This measures how much the stock has gained relative to its home market index (Nifty 50 for India, S&P 500 for US). A stock rising faster than the index signals institutional interest or sector tailwind. IBD-style investing treats this as one of the most predictive selection criteria.

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| rs_vs_index_63d | return_63d_stock - return_63d_index | 63 days | Relative outperformance vs Nifty 50 (India) or S&P 500 (US) over the past quarter. Positive = outperforming. Negative = underperforming. |
| rs_vs_index_21d | return_21d_stock - return_21d_index | 21 days | Monthly relative strength. More sensitive to recent rotation. |
| rs_rank_63d | Cross-sectional percentile rank of rs_vs_index_63d within cap_tier and market_context | 63 days | Rank from 0 to 100 within the same cap tier and market. 80+ = top outperformer. Used in IBD-style RS Rating. |

#### Support and Resistance Level Features
Support is a price level where buying has historically appeared (price bounced up from there). Resistance is where selling has appeared (price was rejected there). For swing trading, buying near support and selling near resistance is the core timing logic. A simple proxy using recent swing highs and lows is computable from OHLCV without any external data.

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| swing_high_20d | Maximum high price over the past 20 days | 20 days | Recent resistance level proxy. Price approaching this = near supply zone. |
| swing_low_20d | Minimum low price over the past 20 days | 20 days | Recent support level proxy. Price approaching this = near demand zone. |
| pct_from_swing_high | (adj_close - swing_high_20d) / swing_high_20d | 20 days | Negative = below recent resistance. Near 0 = testing resistance. |
| pct_from_swing_low | (adj_close - swing_low_20d) / swing_low_20d | 20 days | Small positive = just above recent support. Large positive = extended away from support. |
| near_resistance_flag | 1 if pct_from_swing_high > -0.03 else 0 | 20 days | Stock within 3% of recent swing high. High risk of rejection. Use as caution signal for new long entries. |
| near_support_flag | 1 if pct_from_swing_low < 0.05 else 0 | 20 days | Stock within 5% of recent swing low. Potential bounce zone. Used as context for mean-reversion setups in sideways regime. |
| pivot_high | (high_t-1 > high_t-2) AND (high_t-1 > high_t) — detected at T for T-1 | 3 days | True if yesterday was a local swing high (price turned down from it). Used to update resistance reference. |
| pivot_low | (low_t-1 < low_t-2) AND (low_t-1 < low_t) — detected at T for T-1 | 3 days | True if yesterday was a local swing low (price bounced from it). Used to update support reference. |

---

### Group 4 - Volume Behaviour Features

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| volume_21d_avg | Mean of daily volume over 21 days | 21 days | Baseline volume reference |
| volume_ratio | volume_t / volume_21d_avg | 21 days | Today's volume vs baseline; >1 = elevated |
| volume_spike_flag | 1 if volume_ratio > 2.0 else 0 | 21 days | Binary spike indicator |
| volume_trend_5d | Slope of volume over 5 days (linear regression coefficient) | 5 days | Direction of volume change |
| price_volume_correlation_21d | Pearson correlation of adj_close and volume over 21 days | 21 days | Price-volume relationship |
| obv | Cumulative OBV: add volume on up days, subtract on down days | All available history | On-Balance Volume; direction of accumulation |
| obv_vs_sma_10 | (obv - 10-day SMA of obv) / 10-day SMA of obv | 10 days minimum | OBV position relative to its own short-term average |
| obv_slope_5d | Linear regression slope of OBV over 5 days | 5 days | Direction and rate of OBV change |

OBV interpretation: rising OBV with flat or falling price = accumulation (bullish divergence). Falling OBV with flat or rising price = distribution (bearish divergence). OBV is used in technical analysis as the primary volume confirmation signal.

#### Buying and Selling Pressure Features (Intraday Proxies)
OBV classifies an entire day as either buying (up day) or selling (down day). However, on most days both buyers and sellers are active. These features measure WHERE the price closed within the day's range — a close near the high means buyers dominated; a close near the low means sellers dominated. This is a better proxy for intraday buying vs selling pressure without requiring tick data.

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| clv | ((close - low) - (high - close)) / (high - low) | 1 day | Close Location Value. Ranges from -1 (closed at low = all selling) to +1 (closed at high = all buying). 0 = indecision. If high == low, set to 0. |
| buy_pressure_pct | (close - low) / (high - low) | 1 day | What fraction of the intraday range is below the close. Values near 1 = buyers dominated the day. Values near 0 = sellers dominated. If high == low, set to 0.5. |
| ad_line | Cumulative sum of (clv × volume) | All available history | Accumulation/Distribution Line. Unlike OBV, uses partial day participation rather than binary up/down. Rising with flat price = accumulation. Falling with rising price = distribution. |
| ad_line_slope_5d | Linear regression slope of ad_line over 5 days | 5 days | Direction and rate of A/D accumulation or distribution |
| mfi_14 | Money Flow Index over 14 days | 14 days | RSI equivalent for buying/selling pressure. Uses typical_price = (H+L+C)/3. Positive money flow on days when typical_price > previous typical_price. Range 0–100. >80 = overbought, <20 = oversold by buying pressure. |

#### Delivery Percentage Features (India NSE only — market_context = india)
Delivery % separates genuine accumulation from intraday speculation. OBV and A/D line count total volume; delivery % counts only shares that actually changed hands as settled positions. This is a free, daily NSE dataset unavailable in any US market equivalent. Source: NSE bhav copy (see doc 08 ingestion architecture for data source design).

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| delivery_pct | delivery_qty / total_traded_qty × 100 | 1 day | Today’s delivery percentage. Range 0–100. High = real buying. Low = intraday noise. Set to null for US symbols. |
| delivery_pct_21d_avg | Mean of delivery_pct over 21 days | 21 days | Baseline delivery percentage for this symbol. Establishes what is “normal”. |
| delivery_pct_ratio | delivery_pct / delivery_pct_21d_avg | 21 days | Today’s delivery vs its own baseline. >1.5 = unusually high delivery (strong conviction). <0.5 = unusually speculative. |
| delivery_volume_spike_flag | 1 if delivery_pct_ratio > 1.5 AND volume_ratio > 1.5 else 0 | 21 days | Both volume AND delivery are elevated simultaneously. The strongest accumulation signal in Indian markets. |

---

### Group 5 - Volatility Features

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| realized_vol_10d | Annualised std dev of daily log returns over 10 days | 10 days | Short-term realised volatility |
| realized_vol_21d | Annualised std dev of daily log returns over 21 days | 21 days | Monthly realised volatility |
| vol_ratio | realized_vol_10d / realized_vol_21d | 21 days | Short vs long vol ratio; >1 = rising vol |
| garman_klass_vol_21d | Garman-Klass estimator using OHLC over 21 days | 21 days | Higher-efficiency vol estimator |
| high_low_range_5d | Mean of (high - low) / adj_close over 5 days | 5 days | Intraday range normalised to price |

---

### Group 6 - Regime Descriptor Features

Regime features describe the broad market context at the time of prediction. They are sourced from the home market of each symbol, determined by the `market_context` field. All symbols sharing the same market context on the same date receive the same regime features.

#### market_context = india (NSE/BSE symbols)

| Feature Name | Source | Notes |
| --- | --- | --- |
| index_return_21d | Nifty 50 adj_close 21-day return | Indian market trend proxy |
| index_vs_sma_50 | Nifty 50 price vs its 50-day SMA | Indian market trend position |
| vix_level | India VIX (NSE, ticker ^INDIAVIX via yfinance) | Indian market fear/volatility regime |
| vix_vs_21d_avg | India VIX today vs its 21-day average | India VIX trend direction |
| macro_rate | RBI repo rate | Indian rate environment (source: RBI data API, free) |
| macro_yield_spread | India 10Y govt bond yield minus 2Y yield | Indian yield curve shape (source: RBI / investing.com scrape) |
| market_regime_label | Enum: bull_trend, bear_trend, sideways, high_vol | Derived from regime detection module using Indian index |

#### market_context = us (US-listed symbols)

| Feature Name | Source | Notes |
| --- | --- | --- |
| index_return_21d | S&P 500 adj_close 21-day return | US market trend proxy |
| index_vs_sma_50 | S&P 500 price vs its 50-day SMA | US market trend position |
| vix_level | CBOE VIX closing level | US market fear/volatility regime |
| vix_vs_21d_avg | VIX today vs its 21-day average | CBOE VIX trend direction |
| macro_rate | US Federal Funds Rate (FRED FEDFUNDS) | US rate environment |
| macro_yield_spread | 10Y minus 2Y treasury spread (FRED T10Y2Y) | US yield curve shape |
| market_regime_label | Enum: bull_trend, bear_trend, sideways, high_vol | Derived from regime detection module using US index |

The feature names are **identical** across both market contexts. Only the source data differs. This means a single ML model can be trained on both markets using the same feature schema — the `market_context` field itself becomes an additional categorical feature the model uses to learn market-specific behaviour.

---

### Group 7 - Calendar and Earnings Event Features

Calendar features capture time-of-year effects and, critically, the proximity of a stock to its quarterly results announcement. Earnings events are the single most powerful short-term price catalyst for individual stocks — the architecture must treat them as first-class features, not an afterthought.

#### Standard Calendar Features

| Feature Name | Calculation | Notes |
| --- | --- | --- |
| day_of_week | 0=Monday, 4=Friday | Day-of-week effect |
| month | 1-12 | Seasonal effects |
| quarter | 1-4 | Quarterly cycle |
| is_month_end | 1 if within 3 trading days of month end else 0 | Rebalancing and portfolio window-dressing effect |
| is_quarter_end | 1 if within 5 trading days of quarter end else 0 | Strong rebalancing and FII/DII reporting effect; amplified in India at March (year-end) |

#### Earnings Event Features

Source: Silver layer field `days_to_next_earnings` and `days_since_last_earnings`, derived from the quarterly results calendar (yfinance `.calendar` for both US and India). See ingestion architecture doc 08 for data source design.

| Feature Name | Calculation | Notes |
| --- | --- | --- |
| days_to_next_earnings | Trading days from date T until next board meeting / earnings date | Continuous. 0 = result day. Null = date unknown. |
| days_since_last_earnings | Trading days since the most recent past result announcement | Continuous. Tracks where we are in the quarterly earnings cycle. |
| pre_earnings_zone_flag | 1 if days_to_next_earnings is between 1 and 10 (inclusive) else 0 | The pre-result window where positioning behaviour is elevated. Price and volume patterns have different meaning here. |
| earnings_blackout_flag | 1 if days_to_next_earnings is 0, 1, or 2 else 0 | Hard signal: results are imminent. Binary event risk is highest. No new swing positions should be opened. Any open position must be reviewed. |
| earnings_date_unknown_flag | 1 if days_to_next_earnings is null else 0 | Calendar coverage gap. Pipeline treats this conservatively (no blackout assumed, but ML model sees the flag). |
| pre_earnings_volume_buildup | volume_ratio averaged over days where days_to_next_earnings was 3–7 | Has volume been elevated in the week before this result? Rising = market is positioning. Computed in the Silver enrichment stage as a lookback over the earnings approach window. |
| post_earnings_gap_1d | (open_t / close_t-1) - 1 on the first trading day after the result date | The opening gap on result day. Positive = beat. Negative = miss. Stored in Gold as a label-adjacent audit field, not a predictor (would be look-ahead if used as a feature for the same day's prediction). Used in backtest post-analysis only. |
| earnings_cycle_position | days_since_last_earnings / 63 | Fraction of the quarterly cycle elapsed. Values near 0 = just reported; near 1 = about to report again. Helps model learn cyclical pre/post-earnings drift patterns. |

#### Why Earnings Blackout Matters for Swing Trading

A swing trade entered on day T with a 1-day prediction horizon and 5-day max hold is extremely vulnerable to earnings:

- If results are announced on T+1 (after close), the stock gaps at T+2 open. If the gap is down, it can jump the stop — instead of losing 1×ATR you might lose 3×ATR in one night.
- The 1:2 R:R model is calibrated for normal market volatility. Earnings volatility is 3–8× normal — the ATR stop is no longer meaningful.
- **Architecture rule:** `earnings_blackout_flag = 1` blocks new trade entry. The model may still predict a direction, but the pipeline serving layer rejects the prediction as non-actionable. This is documented as a hard gate in the model serving architecture.

#### Indian Quarterly Results Season (Key Calendar Knowledge)
Indian companies follow the April–March financial year. Result announcement seasons are:
- **Q1 (Apr–Jun):** Results announced July–August
- **Q2 (Jul–Sep):** Results announced October–November
- **Q3 (Oct–Dec):** Results announced January–February
- **Q4 (Jan–Mar) and Annual:** Results announced April–June (heaviest season)

During peak result season (October–November and January–February), a large fraction of the universe will have `pre_earnings_zone_flag = 1` simultaneously. The pipeline must handle this — it does not pause; it simply generates fewer actionable predictions during result season, which is the correct conservative behaviour.

Earnings dates are sourced from the yfinance calendar API (Bronze) and joined to Silver as `days_to_next_earnings`. See doc 08 ingestion architecture for the full data source design and Bronze partition structure.

#### Corporate Action Event Features
When a company announces a bonus, split, or dividend, the stock price adjusts mechanically on the ex-date. This price drop is NOT a bearish signal — it is an accounting event. Without flagging these dates, the ML model learns false patterns (e.g., “-50% return = crash” when in fact it was a 1:1 bonus). All Gold rows with corporate action on that date are flagged and excluded from training.

| Feature Name | Calculation | Source | Notes |
| --- | --- | --- | --- |
| corporate_action_flag | 1 if today is an ex-date for any corporate action for this symbol else 0 | Bronze corporate actions table (NSE + yfinance) | Hard mask: if = 1, row is excluded from model training via is_valid_row = false. |
| corporate_action_type | String: `bonus`, `split`, `dividend`, `rights`, `buyback`, null | Bronze corporate actions table | Stored for audit. Model does not receive this as a feature — only the binary flag. |

#### India Macro Event Blackout Features (market_context = india)
The RBI MPC announcement and Union Budget are macro-level binary events that affect entire sectors in the same way an earnings result affects a single stock. These dates are known in advance (RBI publishes the full-year MPC calendar in April each year; budget date is known 30–60 days ahead). Source: see doc 08 India Macro Event Calendar ingestion.

| Feature Name | Calculation | Notes |
| --- | --- | --- |
| days_to_next_macro_event | Trading days from date T until next RBI MPC announcement or Union Budget date | Null if no known event within 60 days. |
| macro_event_blackout_flag | 1 if days_to_next_macro_event is 0, 1, or 2 else 0 | Hard gate at serving layer for rate-sensitive sectors (banking, NBFC, real estate, utilities). |
| macro_event_type | String: `rbi_mpc_announcement`, `union_budget`, null | Context for sector-specific impact assessment. |

Note: The macro event blackout does not apply to all stocks universally. It applies to sectors designated as rate-sensitive in the sector reference table. A pharma stock, for example, is not blacked out on RBI day. This sector sensitivity mapping is maintained in the governance policy document.

---

### Group 8 - Candlestick Pattern Features

Candlestick patterns are binary flags (1 = pattern detected, 0 = not detected) derived from a single day's OHLC values combined with recent trend context. All inputs are from date T only (no look-ahead).

#### Candlestick Geometry Definitions
- body = abs(close - open)
- upper_shadow = high - max(open, close)
- lower_shadow = min(open, close) - low
- candle_range = high - low

#### Trend Context Fields (Required for Pattern Validity)
- recent_downtrend_5d = 1 if close_t < close_t-5 (price lower than 5 days ago)
- recent_uptrend_5d = 1 if close_t > close_t-5 (price higher than 5 days ago)

| Feature Name | Detection Rule | Trend Context Required | Notes |
| --- | --- | --- | --- |
| hammer_flag | lower_shadow >= 2 × body AND upper_shadow <= 0.3 × body AND body > 0 | recent_downtrend_5d = 1 | Bullish reversal at low; long lower wick |
| inverted_hammer_flag | upper_shadow >= 2 × body AND lower_shadow <= 0.3 × body AND body > 0 | recent_downtrend_5d = 1 | Potential bullish reversal; needs confirmation |
| shooting_star_flag | upper_shadow >= 2 × body AND lower_shadow <= 0.3 × body AND body > 0 | recent_uptrend_5d = 1 | Bearish reversal at high; long upper wick |
| bullish_engulfing_flag | close_t > open_t AND open_t < close_t-1 AND close_t > open_t-1 AND body_t > body_t-1 | recent_downtrend_5d = 1 | Today's bullish candle fully engulfs yesterday's bearish candle |
| bearish_engulfing_flag | close_t < open_t AND open_t > close_t-1 AND close_t < open_t-1 AND body_t > body_t-1 | recent_uptrend_5d = 1 | Today's bearish candle fully engulfs yesterday's bullish candle |
| doji_flag | body <= 0.1 × candle_range AND candle_range > 0 | None required | Indecision; open ≈ close; long shadows on both sides |

Notes:
- If candle_range = 0 (no price movement at all), all candlestick flags are set to 0.
- Candlestick patterns are one-day signals; they do not require multi-day lookback beyond the trend context check.
- Trend context is sourced from Group 1 (return_5d): recent_downtrend_5d = 1 if return_5d < 0.

#### Wyckoff Phase Proxy Features (Add Next - Phase B)
Wyckoff cycle theory (accumulation → markup → distribution → markdown) is in the theories playbook but requires specific price-volume context features to approximate. These are not in Phase 1 because they depend on stable OBV and range analysis being validated first. Add in Phase B once OBV features are confirmed stable.

| Feature Name | Approximation Rule | Notes |
| --- | --- | --- |
| wyckoff_accumulation_proxy | price near 20-day low AND obv_slope_5d > 0 AND volume_ratio > 1.0 | Price bottoming with rising OBV and volume = possible accumulation |
| wyckoff_distribution_proxy | price near 20-day high AND obv_slope_5d < 0 AND volume_ratio > 1.0 | Price topping with falling OBV and volume = possible distribution |

These are simplified rule-based proxies, not a full Wyckoff stage classifier. Architecture for a proper multi-stage Wyckoff detector requires its own design document before implementation.

---

### Group 9 - Institutional Positioning Features

Institutional ownership data is sourced from the Bronze fundamentals layer (yfinance `.info`, fetched quarterly). These features answer the question: are large professional investors accumulating or exiting this stock?

**Why this matters for swing trading:** If a stock is heavily held by institutions and institutional ownership drops quarter-over-quarter, it means large players are selling. A buy signal on top of institutional exit is much weaker than a buy signal where institutions are still accumulating.

| Feature Name | Calculation | Lookback Window | Notes |
| --- | --- | --- | --- |
| institutional_ownership_pct | Direct from Bronze fundamentals | Quarterly (forward-filled daily) | % of shares held by all institutions combined. Ranges 0–1. Forward-filled between quarterly updates to ensure no data gap in Gold rows. |
| institutional_ownership_change_qoq | institutional_ownership_pct_current - institutional_ownership_pct_prior_quarter | Quarterly | Positive = institutions buying more. Negative = institutions reducing position. One of the strongest signals for smart money direction. |
| insider_ownership_pct | Direct from Bronze fundamentals | Quarterly (forward-filled daily) | % of shares held by company insiders and promoters. High insider ownership typically signals alignment with shareholders. |
| short_ratio | Direct from Bronze fundamentals | Quarterly (forward-filled daily) | Days to cover short interest. Short_interest / avg_daily_volume. High short ratio = large crowd betting against the stock (squeeze risk if stock rallies). |
| institutional_high_flag | 1 if institutional_ownership_pct > 0.70 else 0 | Quarterly | Binary flag: >70% institutional ownership. If this stock suddenly drops, it will drop hard because institutions all exit at once. Use as a volatility amplification signal, not a quality signal alone. |

#### Limitation: FII vs DII Split
yfinance does not provide the FII (Foreign Institutional Investor) vs DII (Domestic Institutional Investor) breakdown that Indian market quarterly shareholding filings provide. `institutional_ownership_pct` is the aggregate. For stocks that trade on NSE/BSE, a dedicated BSE shareholding data source would be needed via a separate ADR.

#### Forward-Fill Policy
Institutional data is quarterly. The Silver layer forward-fills these fields by propagating the most recent quarterly value to all subsequent daily rows until a new quarterly fetch overrides it. The `institutional_ownership_as_of_date` audit field tracks which quarter's data is in each Gold row.

---

### Group 10 - India-Specific Regulatory Risk Features (market_context = india only)

These features apply **only to Indian NSE/BSE symbols**. They are set to `null` for US-market symbols. They are sourced from the Bronze fundamentals layer (quarterly shareholding filings) and from daily OHLCV pattern analysis (circuit breaker detection).

#### Why These Are Unique to India

**Promoter Pledging:** In India, company promoters (founders, controlling shareholders) often borrow money by pledging their shares as collateral. SEBI requires quarterly disclosure of this. If a promoter has pledged 60% of their shares and the stock falls, the lender will sell those shares forcibly → price accelerates downward in a death spiral. This is one of the most reliable crash predictors for Indian mid-cap stocks and has no direct US equivalent.

**Circuit Breakers:** SEBI assigns each stock to a price band category: 2%, 5%, 10%, or 20% maximum daily move. If the stock hits the upper or lower circuit, trading is halted for the day. A stock in upper circuit (UC) cannot be bought — all orders to buy sit unfilled. A stock in lower circuit (LC) cannot be sold — a catastrophic liquidity trap. An architecture that doesn't model this will generate false signals on circuit-frozen days.

| Feature Name | Calculation | Source | Notes |
| --- | --- | --- | --- |
| promoter_holding_pct | % of total shares held by promoters | BSE/NSE quarterly shareholding filing (via yfinance `.info` `heldPercentInsiders` as proxy; actual BSE filing data via ADR) | Primary signal of founder alignment. High = good. Falling = warning. |
| promoter_pledging_pct | % of promoter-held shares pledged as collateral | BSE quarterly shareholding filing — yfinance does NOT provide this; requires separate source (see note below) | >30% pledging = elevated forced-sell risk. >60% = very high risk. Hard risk flag. |
| promoter_pledging_flag | 1 if promoter_pledging_pct > 30% else 0 | Derived from promoter_pledging_pct | Binary risk flag used in composite scoring and eligibility gate |
| fii_holding_pct | % of shares held by Foreign Institutional Investors | BSE/NSE quarterly shareholding filing (not in yfinance) | Quarter-over-quarter change is more important than the absolute level |
| dii_holding_pct | % of shares held by Domestic Institutional Investors | BSE/NSE quarterly shareholding filing (not in yfinance) | Rising DII + falling FII = domestic buying, foreign selling |
| fii_change_qoq | fii_holding_pct current quarter - fii_holding_pct prior quarter | Derived | Negative = FIIs exiting. Strong leading indicator of price weakness. |
| upper_circuit_flag | 1 if close_t >= open_t × (1 + circuit_band - 0.001) else 0 | Derived from OHLCV; circuit band from NSE reference file | Stock hit or nearly hit upper circuit today. Cannot buy at market close — only sellers can exit. |
| lower_circuit_flag | 1 if close_t <= open_t × (1 - circuit_band + 0.001) else 0 | Derived from OHLCV; circuit band from NSE reference file | Stock hit lower circuit. Cannot sell. Liquidity frozen. |
| circuit_consecutive_5d | Count of upper_circuit or lower_circuit days in past 5 days | Derived | Repeated circuits = extremely illiquid. Swing trading here is not viable. |

#### Data Source Note for Promoter Pledging and FII/DII
yfinance does not provide promoter pledging percentages or the FII/DII ownership split. These come from BSE quarterly shareholding pattern filings. As a Phase 1 approach:
- yfinance `heldPercentInsiders` is used as a proxy for total promoter holding only.
- Promoter pledging and FII/DII split require BSE data. This is publicly available as CSV/Excel downloads from the BSE website. Incorporating it as a structured source requires an ADR. This is a Phase B addition.
- In Phase 1, `promoter_pledging_pct`, `fii_holding_pct`, and `dii_holding_pct` are stored as null. Risk scoring falls back to aggregate institutional ownership only.

#### Circuit Band Reference
NSE publishes the price band category for each stock. The pipeline pulls this reference file weekly (it changes rarely). Categories: 2% / 5% / 10% / 20% / no limit (for large liquid stocks in F&O segment, no circuit applies). This reference must be stored in Bronze as a separate partition and joined to Silver before circuit flag computation.

---

## Feature Computation Order

Features must be computed in this order to prevent dependency errors:

1. Price returns (Group 1) — depends on Silver adj_close only
2. Rolling statistical features (Group 2) — depends on daily returns from Group 1
3. Volume features (Group 4) — depends on Silver volume and adj_close (OBV, A/D line, CLV, MFI all require OHLCV)
4. Volatility features (Group 5) — depends on Silver OHLC and daily log returns
5. Technical indicators (Group 3) — depends on Silver adj_close and Group 5 ATR inputs
6. Regime features (Group 6) — depends on macro Bronze tables merged at Silver stage, filtered by market_context
7. Calendar features (Group 7) — depends on date column only
8. Candlestick patterns (Group 8) — depends on Silver OHLC and Group 1 trend context
9. Institutional positioning features (Group 9) — depends on Bronze fundamentals joined by symbol and forward-filled through Silver
10. India regulatory risk features (Group 10) — depends on Bronze fundamentals + NSE circuit reference; applied only where market_context = india; skipped for US symbols

---

## Feature Window Summary

| Minimum Lookback Required | Feature Groups Enabled |
| --- | --- |
| 5 days | Partial Group 1, partial Group 2 |
| 21 days | Groups 1, 2, 4 (partial), 7 |
| 35 days | Group 3 (MACD) |
| 50 days | Group 3 (SMA-50, sma_cross_signal, swing high/low 20d) |
| 63 days | Full Groups 1–8 (except 52-week features) |
| 252 days | Full Group 3 (52-week high/low, RS rating); Groups 9–10 require at least one quarterly fundamental snapshot |

Minimum history to produce a complete feature row: 63 trading days for all core features. 252 trading days for 52-week and RS features. At least one quarterly fundamental fetch for Groups 9–10. This is the minimum history gate enforced at Silver-to-Gold promotion.

---

## Missing Value Handling Policy

| Scenario | Action |
| --- | --- |
| Single missing adj_close (1 day gap) | Forward-fill up to 3 consecutive days |
| More than 3 consecutive missing adj_close | Mark all features for that date range as invalid; do not forward-fill |
| Missing volume (1 day gap) | Forward-fill up to 2 consecutive days |
| More than 2 consecutive missing volume | Set volume features to null for affected rows; flag row as partially invalid |
| Missing macro data (FRED) | Use last available value for regime features; FRED releases are infrequent |
| Feature value is infinity or NaN after calculation | Mark the entire row as invalid |

Rows marked as invalid are retained in Gold but excluded from model training and inference via the is_valid_row flag (defined in the Silver schema).

---

## Normalization Strategy

### Tree-Based Models (Primary for Phase 1)
- No normalization applied. XGBoost, LightGBM, and Random Forest handle raw feature scales natively.
- Applying normalization to tree-based models is unnecessary and would complicate reproducibility.

### Linear and Distance-Based Models (Future Phase 2)
- Z-score normalization (subtract mean, divide by std) using training-set statistics only.
- Normalization parameters (mean and std) are stored alongside the model artifact for application at inference time.
- Test and inference sets are normalized using training-set statistics, never their own statistics.

---

## Feature Versioning Policy

### What Triggers a New Feature Version
- Any change to a feature's calculation formula, window size, or normalization.
- Addition of a new feature to the Gold schema.
- Removal of a feature from the Gold schema.
- Change to the missing value handling policy.

### How Versioning Works
- Each Gold build is tagged with a feature_version string (example: `v1.0.0`).
- feature_version is recorded in the Gold Iceberg snapshot metadata.
- feature_version is also stored in the model metadata (SQLite) as part of the training record.
- Models trained on feature_version v1.0.0 cannot be used for inference on a Gold snapshot with feature_version v2.0.0.
- A model-feature version mismatch blocks inference and raises an alert.

### Feature Version History
- feature_version v1.0.0: initial Phase 1 feature set as defined in this document.
- Future versions are documented by appending to this section.

---

## Guardrails

### G1 - No Look-Ahead Bias
- Every feature calculation must use only data with date strictly less than T (the prediction date).
- Features that reference same-day open, high, or low prices are only valid because they represent data available before the close. Features referencing close price of date T are prohibited.
- Look-ahead violations are detected by the Gold build job's date-alignment check and halt the pipeline.

### G2 - Adjusted Price Enforcement
- All price-derived features must use adj_close from Silver.
- Features using unadjusted close are rejected at Gold build time.

### G3 - Feature Version Consistency
- A Gold snapshot must carry a single consistent feature_version tag across all rows.
- Mixed-version snapshots are invalid and must be rebuilt.

### G4 - Model-Feature Version Lock
- Inference jobs must verify that the active Gold snapshot's feature_version matches the feature_version recorded in the model metadata.
- Version mismatch blocks inference; this is not a warning, it is a hard stop.

### G5 - Minimum History Gate
- Symbols with fewer than 63 trading days of Silver history produce no feature rows in Gold.
- These symbols are excluded from Gold silently and logged in the build audit record.

### G6 - Invalid Row Exclusion
- Training jobs must filter to is_valid_row = true before fitting any model.
- Training on rows with is_valid_row = false is a pipeline violation.

### G7 - No Silent Feature Changes
- Changing any feature specification (formula, window, or normalization) without incrementing feature_version is prohibited.
- Silent changes that make existing model artifacts inconsistent with the data they were trained on are a reproducibility violation.
