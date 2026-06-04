# 08 Data Ingestion Architecture

## Purpose
Define how raw market and macro data enters the data platform, covering the Landing layer (first point of arrival), source selection, historical backfill design, incremental daily ingestion, adjusted price policy, deduplication, and failure handling.

---

## Ingestion Flow Overview

```
External Sources → [Lambda/Glue Fetcher] → Landing Layer (S3, raw)
                                                  ↓
                                         [Ingestion ETL, G0 gate]
                                                  ↓
                                         Bronze Layer (S3, Parquet)
                                                  ↓
                                         Silver Layer (S3, Iceberg)
                                                  ↓
                                         Gold Layer (S3, Iceberg)
```

- **Landing Layer** (`s3://project-intelligent-landing/`) — raw, unmodified files as received from each source. Write-once, Object Lock COMPLIANCE. No transformation applied.
- **Bronze Layer** — validated, partitioned Parquet snapshots. Only records passing the G0 quality gate are written here.
- See `03_data_architecture_medallion.md` for full Landing and Bronze layer specification.

---

## Data Sources

### Primary Market Data Source: yfinance
- Wrapper for Yahoo Finance historical and reference data.
- Free, no API key required, no rate-limit contract.
- Provides OHLCV, adjusted close, splits, dividends, and basic fundamentals.
- Acceptable for swing batch pipeline; not suitable for intraday latency requirements.

#### Ticker Suffix Convention by Market
| Market | Exchange | yfinance Suffix | Example |
| --- | --- | --- | --- |
| India | NSE (National Stock Exchange) | `.NS` | `RELIANCE.NS`, `TCS.NS`, `INFY.NS` |
| India | BSE (Bombay Stock Exchange) | `.BO` | `RELIANCE.BO`, `TCS.BO` |
| USA | NYSE / NASDAQ | None | `AAPL`, `MSFT`, `GOOGL` |

NSE is preferred over BSE for Indian stocks where both are available — NSE has higher liquidity and more consistent data coverage in yfinance. Each symbol record in the universe carries a `market_context` field (`india` or `us`) and an `exchange` field (`NSE`, `BSE`, `NYSE`, `NASDAQ`).

### Macro Data Source: FRED (Federal Reserve Economic Data)
- Free public API from the Federal Reserve Bank of St. Louis.
- API key required (free registration).
- Provides US economic release data with official timestamps.
- Pull cadence: weekly on Sunday or on data release schedule.
- **Scope: US market_context symbols only.** Indian symbols use RBI macro data (see below).

### Macro Data Source: RBI (Reserve Bank of India) — India market_context
- The Reserve Bank of India publishes key rate and economic data publicly.
- Data series required: RBI repo rate (policy rate), India 10Y government bond yield, India 2Y government bond yield, India CPI (sourced from MOSPI via RBI database).
- Free. No API key for public data pages. Pull cadence: weekly.
- **Strategy in Phase 1:** Repo rate changes infrequently (bi-monthly RBI MPC meetings). A weekly scrape of the RBI database website (`rbi.org.in/scripts/PublicationsView.aspx`) is sufficient. India VIX (ticker `^INDIAVIX` in yfinance) is pulled daily alongside Nifty 50 (`^NSEI`).
- Any new source requires an ADR before adoption.

### No Other Sources in Phase 1
- Third-party premium data providers are not used.
- Any new source requires an ADR before adoption.

---

## Fundamental Data Fields Ingested (yfinance)

Fundamental data is required by the fundamental analysis framework (P/E, Debt/Equity, ROE, cash flow, etc.). yfinance provides this via its `.info`, `.financials`, `.balance_sheet`, and `.cashflow` endpoints.

### Fetch Method
- yfinance `.info` — company profile, current P/E, market cap, forward P/E, sector
- yfinance `.financials` — annual income statement (revenue, operating income, net income, EPS)
- yfinance `.balance_sheet` — annual balance sheet (total debt, equity, current assets, current liabilities)
- yfinance `.cashflow` — annual cash flow (operating cash flow, free cash flow)

### Fundamental Fields Stored in Bronze

| Field | Source | Cadence | Notes |
| --- | --- | --- | --- |
| symbol | context | Quarterly | Ticker |
| report_date | yfinance | Quarterly | Most recent fiscal period end date |
| market_cap | .info | Quarterly | Market capitalization |
| pe_ratio_ttm | .info | Quarterly | Trailing 12-month P/E ratio |
| pe_ratio_forward | .info | Quarterly | Forward P/E ratio |
| revenue_ttm | .financials | Quarterly | Trailing 12-month revenue |
| net_income_ttm | .financials | Quarterly | Trailing 12-month net income |
| eps_ttm | .financials | Quarterly | Trailing 12-month EPS |
| gross_margin | .financials | Quarterly | Gross profit / revenue |
| operating_margin | .financials | Quarterly | Operating income / revenue |
| net_margin | .financials | Quarterly | Net income / revenue |
| total_debt | .balance_sheet | Quarterly | Total short-term + long-term debt |
| total_equity | .balance_sheet | Quarterly | Total shareholders equity |
| debt_to_equity | derived | Quarterly | total_debt / total_equity |
| current_ratio | .balance_sheet | Quarterly | Current assets / current liabilities |
| roe | derived | Quarterly | net_income_ttm / total_equity |
| operating_cashflow | .cashflow | Quarterly | Operating cash flow |
| free_cashflow | .cashflow | Quarterly | Operating cash flow - capex |
| sector | .info | Quarterly | GICS sector label |
| industry | .info | Quarterly | GICS industry label |
| institutional_ownership_pct | .info | Quarterly | Aggregate % of shares held by all institutions (13F filers). Source key: institutionPercent. This is a combined figure — does NOT split FII vs DII. See limitation note below. |
| insider_ownership_pct | .info | Quarterly | % of shares held by company insiders and promoters. Source key: heldPercentInsiders. |
| short_ratio | .info | Quarterly | Days to cover short interest (short_interest / avg_daily_volume). Higher value = larger short position relative to liquidity. Source key: shortRatio. |
| ingestion_timestamp | context | Quarterly | UTC timestamp of fetch |
| ingestion_run_id | context | Quarterly | Pipeline run ID |

### Important Limitation: FII vs DII Split
yfinance reports **aggregate institutional ownership** only — it does not separate Foreign Institutional Investors (FII) from Domestic Institutional Investors (DII). This distinction is a regulatory concept in Indian markets (BSE/NSE), where companies file quarterly shareholding patterns that break ownership into Promoter, FII, DII, and Retail buckets.

If the universe is extended to Indian-listed stocks (NSE/BSE), a separate data source is required:
- BSE shareholding pattern data (publicly available quarterly on BSE website)
- NSE corporate governance disclosures
- This would require a dedicated ADR before adoption as it involves a new source, a new ingestion pipeline branch, and different field semantics.

For the current Phase 1 scope (US-listed stocks via yfinance), `institutional_ownership_pct` is the closest available proxy. A sudden quarter-over-quarter drop in this field signals institutional selling, regardless of whether the sellers are foreign or domestic.

### Cadence
- Full fetch: quarterly, aligned with earnings reporting seasons (January, April, July, October).
- Triggered by job J01 (universe selection) to ensure fresh fundamentals are available before scoring.
- Incremental check: if a symbol's earnings date has passed since the last fetch, a targeted re-fetch is triggered.

### Fundamental Data Partition in Landing and Bronze
```
s3://project-intelligent-landing/
  source=yfinance/
    date=2026-04-15/
      AAPL_fundamentals.json       ← raw API response, untouched

s3://project-intelligent-bronze/
  fundamentals/
    source=yfinance/
      symbol=AAPL/
        fetch_date=2026-04-15/
          fundamentals.parquet
```

### Known Limitations of yfinance Fundamentals
- yfinance does not provide guaranteed quarterly point-in-time data. It reflects the most recent available report.
- For strict point-in-time backtesting, use the report_date field to ensure no future-quarter data is used.
- If a field is missing (e.g., some small-cap companies have sparse data), the field is stored as null. The fundamental analysis scoring module handles nulls per its own guardrails (G1 mandatory field gate).

---

## Quarterly Results Calendar Ingestion (yfinance Earnings Dates)

### Why This Matters
Indian companies are required to inform NSE/BSE in advance of any board meeting where quarterly financial results will be discussed. NSE publishes these board meeting dates publicly — this means we know **in advance** which stocks are going to announce results and on what date. This is the primary source for the earnings event features.

### Behaviour Around Quarterly Results
There are two distinct price patterns that occur around result announcements:

**Pre-result drift (2–10 days before):**
- Market participants who have studied the company start positioning — buying if they expect a good result, selling if they expect a miss.
- Volume typically increases 3–5 days before announcement.
- This creates a directional drift before the event. The model must know a result is approaching to interpret this volume/price behaviour correctly.

**Post-result gap (next trading day after announcement):**
- Results are typically announced after market hours (after 3:30 PM IST) or on holidays.
- The stock opens the next day with a gap — up if results beat expectations, down if they miss.
- If we are in an open swing position when results are announced, this gap can jump the stop loss (gap-down past stop = larger loss than expected). This is why a blackout rule is needed.

### Data Source for NSE: NSE Corporate Filings API

NSE publishes board meeting intimation data at: `https://www.nseindia.com/companies-listing/corporate-filings-board-meetings`

### Data Source for NSE: yfinance

The pipeline retrieves upcoming earnings dates natively via `yfinance.Ticker(symbol).calendar` (which relies on `lxml` for internal parsing) instead of building a complex and brittle scraper for the NSE corporate filings site. This approach provides a unified interface for both US and India market contexts.

The pipeline pulls the payload and flattens it:

- Extracts `Earnings Date` from the calendar dictionary.
- If multiple dates exist, it identifies the nearest upcoming date.
- Saves the JSON payload into the Landing bucket before parsing.

**API Limit Mitigation:** Rate-limiting via `tenacity` retry logic to avoid Yahoo Finance IP blocking.

### Data Source for US: yfinance `.calendar`
- `yfinance.Ticker(symbol).calendar` returns the next expected earnings date for US stocks.
- Reliable for large-cap US stocks. Patchy for small-cap.
- Pull weekly alongside fundamental fetch.

### Earnings Calendar Fields Stored in Bronze

| Field | Type | Notes |
| --- | --- | --- |
| symbol | string | NSE ticker (no suffix in calendar — mapped to `.NS` in pipeline) |
| board_meeting_date | date | Date of the board meeting where results will be discussed |
| result_type | string | `quarterly` or `annual` |
| quarter_label | string | E.g., `Q3FY26`, `Q4FY25` |
| intimation_date | date | Date NSE received the board meeting notice |
| source | string | `nse_board_meeting` or `yfinance_calendar` |
| fetch_date | date | Date this record was pulled by the pipeline |
| ingestion_run_id | string | Pipeline run ID for traceability |

### Earnings Calendar Landing and Bronze Partition Design
```
s3://project-intelligent-landing/
  source=nse_board_meetings/
    date=2026-05-04/
      board_meetings_20260504.json  ← raw NSE API/scrape response

s3://project-intelligent-bronze/
  earnings_calendar/
    market_context=india/
      fetch_date=2026-05-04/
        earnings_calendar.parquet
    market_context=us/
      fetch_date=2026-05-04/
        earnings_calendar.parquet
```

### Silver Enrichment
The Silver stage joins the earnings calendar to the daily OHLCV symbol table and computes:
- `days_to_next_earnings` — number of trading days from date T until the next board meeting date.
- `days_since_last_earnings` — number of trading days from the most recent past board meeting date until T.
- These two fields are available on every Silver row for every symbol with a known calendar entry.

### Coverage Gaps
- Coverage for Indian stocks via Yahoo Finance is historically robust, but may occasionally lag behind immediate NSE portal updates.
- If a symbol has no upcoming calendar entry, `days_to_next_earnings` is set to null. The feature engineering layer treats null as "unknown" and the earnings blackout rule defaults to safe (no blackout if date unknown, but model receives a `earnings_date_unknown_flag = 1`).
- Newly listed companies may not have historical calendar entries — they are excluded from earnings event features until at least one quarter of history is available.

---

## NSE Bhav Copy Ingestion — Delivery Percentage (India Only)

### Why Delivery Percentage Is Critical
NSE publishes the **equity bhav copy** (daily market activity file) every trading day. It contains, for every NSE-listed stock, the total traded volume AND the delivery volume (shares that actually changed hands as settled delivery, not intraday). The delivery percentage = delivery volume / total traded volume × 100.

This is one of the most powerful India-specific signals:
- **High delivery % (60–90%)** = real buyers are accumulating. Institutions and long-term investors are taking delivery. This is genuine accumulation.
- **Low delivery % (5–20%)** = almost all activity is intraday. Speculators are trading but no one is actually holding overnight. The volume surge is noise, not conviction.
- OBV, A/D line, and CLV cannot make this distinction. They see total volume. Only delivery % separates real ownership change from intraday noise.

**Practical example:** A stock with volume 10× its average but only 8% delivery = pump by intraday traders. A stock with volume 3× its average and 75% delivery = FII/DII is buying and holding. The signals are opposite despite both having a volume spike.

### Data Source
- NSE publishes the bhav copy daily in CSV format.
- URL pattern: `https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv`
- Free. No login or API key required.
- File contains: symbol, ISIN, open, high, low, close, last, prevclose, tottrdqty (total traded quantity), tottrdval (total traded value), timestamp, totaltrades, deliveryqty, deliveryperc.
- Pull after market close each trading day (after 6:00 PM IST, files are usually available by 7:00 PM IST).

### Delivery Percentage Fields in Bronze

| Field | Type | Notes |
| --- | --- | --- |
| symbol | string | NSE symbol (no suffix) |
| trade_date | date | Trading date |
| total_traded_qty | integer | Total shares traded (intraday + delivery) |
| delivery_qty | integer | Shares that resulted in settled delivery |
| delivery_pct | float | delivery_qty / total_traded_qty × 100. Range 0–100. |
| source | string | Always `nse_bhav_copy` |
| ingestion_timestamp | timestamp | UTC timestamp of fetch |
| ingestion_run_id | string | Pipeline run ID |

### Bronze Partition
```
s3://project-intelligent-bronze/
  delivery/
    market_context=india/
      trade_date=2026-05-07/
        bhav_delivery.parquet
```

---

## Corporate Actions Ingestion (Bonus, Rights, Dividend Ex-Date)

### Why This Is Critical for Model Integrity
Corporate actions cause mechanical price changes that are NOT market signals:
- **Bonus shares (e.g., 1:1 bonus):** On the record date, the price is halved automatically because the number of shares doubles. A model that sees -50% `return_1d` on this day will learn a catastrophically wrong pattern.
- **Stock split (e.g., 2:1 split):** Same effect — price halved, shares doubled. yfinance adjusts `adj_close` historically, but the unadjusted `open`, `high`, `low` stored in Bronze will show the post-split price, creating a one-day discontinuity.
- **Rights issue:** Existing shareholders get new shares at a discount. Ex-rights price drops.
- **Dividend ex-date:** Price drops by approximately the dividend amount on ex-date. A ₹5 dividend on a ₹100 stock = -5% that day, which is not bearish. The model must know this is an ex-dividend drop.

**All rows in Gold for a corporate action date must be flagged.** These rows should be excluded from ML model training.

### Data Source
- yfinance provides corporate actions via `yfinance.Ticker(symbol).actions` — returns a DataFrame of historical dividends and splits.
- NSE also publishes corporate action calendar at: `https://www.nseindia.com/companies-listing/corporate-filings-actions`
- Pull weekly for upcoming actions; retrospective adjustment confirmed via yfinance actions history.

### Corporate Actions Fields in Bronze

| Field | Type | Notes |
| --- | --- | --- |
| symbol | string | NSE or US ticker |
| ex_date | date | The date the action takes effect (price adjusts on this date) |
| action_type | string | `bonus`, `split`, `dividend`, `rights`, `buyback` |
| action_ratio | string | E.g., `1:1` for 1:1 bonus, `2:1` for 2:1 split, `5.00` for ₹5 dividend |
| source | string | `yfinance_actions` or `nse_corporate_calendar` |
| fetch_date | date | Date record was pulled |
| ingestion_run_id | string | Pipeline run ID |

### Silver Enrichment
The Silver stage joins corporate actions to the daily OHLCV table and computes:
- `corporate_action_flag` — 1 if the date matches any ex_date for this symbol, else 0.
- `corporate_action_type` — the action type string, null if no action.

### Gold Impact
- Any Gold feature row where `corporate_action_flag = 1` is automatically excluded from model training (added to is_valid_row = false conditions).
- These rows are retained in Gold for completeness and audit; they are simply masked from training.

---

## India Macro Event Calendar (RBI MPC + Union Budget)

### Why This Matters
Just as earnings events create binary uncertainty for individual stocks, certain macro events create binary uncertainty for entire sectors or the entire market:

**RBI MPC (Monetary Policy Committee) meetings:** Held 6 times a year (February, April, June, August, October, December). The RBI announces the repo rate decision after the meeting. Repo rate changes directly affect:
- Banking and NBFC stocks (interest margin impact)
- Real estate stocks (home loan rate impact)
- Utilities and infrastructure (borrowing cost impact)
On RBI announcement days, these sectors can gap 3–5% in either direction.

**Union Budget:** Announced once a year in February (and occasionally interim budgets before elections). The budget announces tax changes, sector subsidies, infrastructure spending, customs duties. Sectors directly impacted include: PSU banks, defence, infrastructure, EV/auto, FMCG (GST changes), pharma. On budget day, stocks in targeted sectors can move 5–15%.

### Data Source
- RBI MPC meeting dates are published by RBI in advance for the entire year. Source: `rbi.org.in/scripts/BS_PressReleaseDisplay.aspx` — pull annually and store as a reference table.
- Union Budget date is announced by the Finance Ministry (typically known 30–60 days in advance). Pull from publicly available government calendar.
- Both are infrequent and manually maintained as a reference file updated once a year.

### India Macro Event Fields in Bronze

| Field | Type | Notes |
| --- | --- | --- |
| event_date | date | Date the event occurs |
| event_type | string | `rbi_mpc_announcement`, `union_budget`, `rbi_mpc_meeting_day` |
| sectors_impacted | string | Comma-separated list of primarily impacted sectors |
| notes | string | Brief description (e.g., "Rate cut expected") |
| source | string | `rbi_calendar` or `finance_ministry_calendar` |
| ingestion_run_id | string | Pipeline run ID |

### Silver and Gold Enrichment
- `days_to_next_macro_event` — trading days until next RBI MPC announcement or budget day.
- `macro_event_blackout_flag` — 1 if days_to_next_macro_event is 0, 1, or 2 else 0.
- `macro_event_type` — the event type string, null if no upcoming event within window.
- These fields follow the exact same blackout architecture as the earnings blackout.

---

## OHLCV Bronze Schema

| Field | Type | Notes |
| date | date | Trading date (UTC normalized) |
| open | float | Unadjusted open price |
| high | float | Unadjusted high price |
| low | float | Unadjusted low price |
| close | float | Unadjusted close price |
| adj_close | float | Split and dividend adjusted close |
| volume | integer | Daily traded volume |
| source | string | Always "yfinance" in Phase 1 |
| ingestion_timestamp | timestamp | UTC timestamp when record was written to Bronze |
| ingestion_run_id | string | Pipeline run ID for traceability |

Both unadjusted and adjusted prices are stored in Bronze. Unadjusted prices are preserved for research and audit. Silver and Gold use adjusted prices for all calculations.

---

## Macro Data Fields Ingested (FRED)

| Series ID | Description | Cadence |
| --- | --- | --- |
| DGS10 | 10-Year Treasury Yield | Daily (business days) |
| FEDFUNDS | Federal Funds Effective Rate | Monthly |
| CPIAUCSL | CPI All Items | Monthly |
| UNRATE | Unemployment Rate | Monthly |
| GDP | Real GDP Growth | Quarterly |
| VIXCLS | CBOE VIX Index | Daily (business days) |
| SP500 | S&P 500 Index Level | Daily (business days) |
| T10Y2Y | 10-Year minus 2-Year Treasury Spread | Daily (business days) |

Macro series are stored as separate Bronze tables, not merged with OHLCV at ingestion time. Merging happens at Silver enrichment stage.

---

## Historical Backfill Design

### Target History Window
- 10 years of daily OHLCV data per symbol (approximately 2520 trading days).
- This provides sufficient history for walk-forward backtesting across multiple market regimes.
- Minimum required history before a symbol is eligible for training: 252 trading days (one year).

### Backfill Execution Plan
- Backfill runs once at project initialization.
- Backfill uses the same Bronze write path as daily incremental ingestion; there is no separate backfill-only code path.
- Backfill is partitioned by year to create manageably sized files.
- After backfill completes, normal daily incremental ingestion begins the next trading day.

### Backfill Idempotency
- Backfill jobs are fully idempotent.
- If a year-partition file already exists for a symbol, the backfill job skips that partition.
- Re-running a backfill never overwrites existing Bronze data.

---

## Daily Incremental Ingestion Design

### Schedule
- Runs Monday through Friday after US market close.
- Scheduled trigger: EventBridge at 21:00 UTC (5:00 PM US Eastern, accounting for after-hours data availability).
- Pulls the most recent trading day's OHLCV for all symbols in the active universe.

### Incremental Scope
- Only symbols in the current active universe selection are ingested each day.
- Symbols removed from the universe stop receiving daily updates; their historical data is retained in Bronze.
- New symbols added to the universe receive a targeted backfill job before their first daily ingestion.

### New Symbol Backfill on Universe Refresh
- When a weekly universe refresh adds a new symbol, a targeted backfill job runs before the next daily ingestion cycle.
- This ensures the new symbol has at least 252 trading days in Bronze before Silver and Gold promotion.
- If a new symbol cannot reach 252 days of history, it is ineligible for training and is flagged in the audit log.

---

## Adjusted Price Policy

### Bronze Layer
- Both unadjusted prices (open, high, low, close) and adjusted close are stored.
- Raw unadjusted prices are preserved for audit, research, and corporate action analysis.

### Silver and Gold Layers
- All price-derived calculations use adjusted close as the basis.
- Open, high, low prices in Silver are stored as-is from Bronze.
- Feature calculations (returns, rolling statistics, volatility) use adj_close only.
- This ensures that stock splits and dividend payments do not create artificial price discontinuities in features and labels.

### Corporate Action Handling
- yfinance provides backward-adjusted close prices automatically.
- No manual corporate action adjustment is performed.
- When a split or dividend occurs, yfinance revises historical adjusted close values; the next daily ingestion will pick up the revised history as a new date-partitioned file.
- This means Bronze contains both the old and new adjusted history as separate ingestion-date partitions. Silver always promotes from the latest ingestion partition.

---

## Deduplication Rule

### Primary Key
- Bronze deduplication key: symbol + date + source.
- A record with the same symbol, date, and source as an existing Bronze record is considered a duplicate.

### Deduplication Policy
- Before writing to Bronze, the ingestion job checks whether a record with the same key already exists.
- If a duplicate is detected, the new record is skipped and logged.
- Deduplication violations are not errors; they are logged as informational events for audit.
- Deduplication is enforced at the Bronze write step, not at the source fetch step.

### Correction Policy
- If a Bronze record is later found to contain incorrect data (e.g., wrong adjusted close due to a data provider error), the correction is handled by re-ingesting the affected date partition with a new ingestion_timestamp and run_id.
- The incorrect record is retained; the corrected record is added as a newer partition.
- Silver promotion always selects the latest valid ingestion partition per symbol and date.

---

## Rate Limiting and Retry Strategy

### yfinance
- No official rate limit documented by Yahoo Finance.
- Observed behaviour: aggressive parallel requests cause temporary HTTP 429 throttling.
- Design rule: fetch symbols sequentially, not in parallel, within a single invocation.
- Batch size per Lambda invocation: maximum 10 symbols to stay within Lambda timeout limits.
- Retry policy: 3 attempts with exponential backoff (2s, 4s, 8s) on any HTTP error.
- If all 3 retries fail for a symbol, log the failure, skip the symbol for today, and raise a CloudWatch alert.
- Missed symbols are retried in the next daily run automatically.

### FRED
- Official rate limit: 120 requests per minute per API key.
- Macro series are few and infrequent; rate limiting is not a practical concern.
- Retry policy: 3 attempts with exponential backoff on HTTP error.

---

## Bronze Partition Design

```
s3://project-intelligent-bronze/
  market/
    source=yfinance/
      symbol=AAPL/
        year=2024/
          ingestion_date=2024-12-31/
            ohlcv.parquet
  macro/
    source=fred/
      series=DGS10/
        year=2024/
          fetch_date=2024-12-31/
            data.parquet
```

- Partition by source, symbol (or series), year, and ingestion_date.
- Year partition enables efficient backfill management and storage cost tracking.
- Ingestion_date partition enables identification of the latest ingest for each symbol and date.

---

## Failure Handling

| Failure Type | Response | Alert |
| --- | --- | --- |
| Symbol fetch fails all retries | Skip symbol, log to audit, continue pipeline | CloudWatch alert with symbol name |
| All symbols fail | Abort daily run, log full failure | CloudWatch critical alert |
| Duplicate detected | Skip write, log as informational | None |
| Bronze write fails | Abort run, do not proceed to Silver | CloudWatch critical alert |
| FRED fetch fails | Skip macro update for today, log | CloudWatch alert |

---

## Guardrails

### G1 - Source Approval
- yfinance and FRED are the only approved ingestion sources for Phase 1.
- Any new data source requires a formal ADR before ingestion code is written.

### G2 - Adjusted Price Policy Enforcement
- Silver and Gold layer jobs must read adj_close for all price-derived calculations.
- Any feature or label that directly reads unadjusted close from Silver or Gold is rejected at code review.

### G3 - Backfill Idempotency
- Backfill jobs must check for existing partitions before writing.
- A backfill job that overwrites an existing Bronze partition is a pipeline violation and must be corrected immediately.

### G4 - Minimum History Gate
- A symbol with fewer than 252 days of Bronze history must not be promoted to Silver or Gold for model training.
- This gate is enforced at the Bronze-to-Silver promotion step.

### G5 - Ingestion Run Audit
- Every ingestion run must write a structured audit record to DynamoDB: run_id, symbol count attempted, symbol count succeeded, symbol count failed, duration, and timestamp.
- An ingestion run without an audit record is flagged as non-compliant.

### G6 - No Manual Writes to Bronze
- No human identity is permitted to write directly to the Bronze S3 zone.
- All Bronze data enters through the pipeline ingestion job identity only.
- Violations are detected by CloudWatch S3 event logging and trigger an immediate alert.

### G7 - Retry Limit Respect
- Ingestion jobs must not exceed 3 retry attempts per symbol per run.
- Aggressive retry loops that cause yfinance throttling are a pipeline violation and must be corrected before the next run.
