# ADR-005: News and Sentiment Data Source Decision

## Status
Accepted — Finnhub as primary sentiment source; RSS feed as zero-cost fallback.

## Date
2026-05-07

## Context
The sentiment analysis framework (docs/analysis/sentiment_analysis_architecture.md) requires a source of news headlines and sentiment scores for symbols in the active universe. The source must:
- Provide symbol-level news linkage (not generic market news).
- Offer sufficient daily article coverage for a 30-symbol swing universe.
- Be free or free-tier with no time-limited cost risk.
- Operate within the project's open-source, near-zero-cost constraint.

In Phase 1, sentiment is an auxiliary signal weighted at 5% in the composite universe score. The data requirement is modest: a daily headline count and a polarity direction per symbol.

---

## Decision Drivers
- Budget: free or permanently free API tier. No paid subscription.
- Coverage: must reach all 30 symbols with at least 1 article per symbol per week.
- Operational simplicity: pre-computed sentiment scores preferred to avoid adding an NLP library dependency in Phase 1.
- Rate limit: must support fetching 30 symbols sequentially within a daily batch window.
- Reliability: must have a stable API contract; unofficial scraping approaches are rejected.

---

## Options Evaluated

### Option 1 — Finnhub (Selected as Primary)
- Free tier: 60 API calls per minute, no daily call cap.
- Company news endpoint: `/company-news?symbol=AAPL&from=2026-05-01&to=2026-05-07`
- Sentiment endpoint: `/news-sentiment?symbol=AAPL` — returns a pre-computed bullish/bearish score and article count.
- API key required: free registration at finnhub.io.
- Pre-computed sentiment: yes. Returns `bullishPercent`, `bearishPercent`, and `buzz` (news volume score) per symbol.
- Coverage: good for US large-cap and mid-cap; variable for small-cap.
- No NLP library needed in Phase 1; sentiment scores are server-computed.
- Rate limit design: 30 symbols × 2 API calls (news + sentiment) = 60 calls per batch run. Fits within 60 calls/minute with sequential fetching and a 1-second pause between symbols.
- Verdict: **selected as primary source**. Best fit for free-tier sentiment without NLP overhead.

### Option 2 — Alpha Vantage NEWS_SENTIMENT
- Free tier: 25 API calls per day.
- Provides symbol-level news with pre-computed sentiment and relevance scores.
- 25 calls/day is insufficient for 30 symbols (each symbol needs at least 1 call).
- Would require multi-day batching just to cover the full universe once — not acceptable for daily freshness.
- Verdict: rejected. Daily call limit is too tight for a 30-symbol universe.

### Option 3 — NewsAPI
- Free tier: 100 requests/day, 1 month of article history.
- Provides raw article text; no pre-computed sentiment.
- Requires a sentiment NLP library (e.g., VADER or transformers) to extract polarity — adds a dependency not justified in Phase 1.
- 1-month history limit blocks historical sentiment backfill.
- Verdict: rejected. History limit and NLP dependency are blockers for Phase 1.

### Option 4 — Yahoo Finance RSS (via feedparser)
- No API key required. Publicly available RSS feeds per ticker.
- Not an official API; Yahoo Finance can remove or change RSS structure at any time without notice.
- No pre-computed sentiment; raw headlines only.
- Verdict: rejected as primary. Too brittle for production. Retained as zero-cost fallback only (see below).

### Option 5 — SEC EDGAR RSS (for filing events)
- Official, free, reliable.
- Covers SEC filings only (10-K, 10-Q, 8-K, insider transactions) — not daily news sentiment.
- Useful as an event-type signal in future phases but not suitable as a sentiment source.
- Verdict: not applicable for sentiment in Phase 1. Noted for future event-tagging feature.

---

## Decision
**Primary source: Finnhub free tier.**

| Concern | Resolution |
| --- | --- |
| API key required | Free registration; key stored in AWS Secrets Manager; never in code |
| Small-cap coverage gaps | If a symbol has zero articles, sentiment is set to neutral and marked low-coverage per sentiment guardrail G1 |
| Finnhub rate limit | 30 symbols × 2 calls = 60 calls per batch; fits within 60 calls/minute with 1-second pause between symbols |
| Pre-computed score accuracy | Acceptable for Phase 1 auxiliary signal; NLP upgrade is a Phase 3 option |

**Fallback: Yahoo Finance RSS via feedparser.**
- Activated only if Finnhub becomes unavailable (API outage or free tier removed).
- Fallback provides raw headlines only; sentiment score falls back to neutral until Finnhub is restored.
- Fallback is never the primary path; it is a graceful degradation mode.

---

## Finnhub Fields Used

### From `/news-sentiment?symbol=`

| Field | Type | Used As |
| --- | --- | --- |
| buzz.articlesInLastWeek | integer | news_intensity feature |
| buzz.weeklyAverage | float | baseline news volume for novelty detection |
| sentiment.bullishPercent | float | raw bullish score (0–1) |
| sentiment.bearishPercent | float | raw bearish score (0–1) |
| sentiment.score | float | net sentiment: bullishPercent - bearishPercent |

### Derived Fields Written to Bronze

| Field | Derivation |
| --- | --- |
| sentiment_score | sentiment.score from Finnhub (bullish - bearish) |
| sentiment_direction | 1 if sentiment_score > 0.1, -1 if < -0.1, 0 otherwise |
| news_intensity | buzz.articlesInLastWeek |
| news_coverage_flag | low if articlesInLastWeek < 2, else normal |
| sentiment_source | "finnhub" |
| fetch_date | UTC date of the API call |
| ingestion_run_id | pipeline run ID |

---

## Bronze Partition for Sentiment Data

```
s3://project-intelligent-bronze/
  sentiment/
    source=finnhub/
      symbol=AAPL/
        fetch_date=2026-05-07/
          sentiment.parquet
```

---

## Fetch Cadence
- Daily: fetch sentiment for all active universe symbols after market close, as part of the J02 ingestion job (or a separate J02b step).
- Sequential fetch with a 1-second pause between symbols to respect the 60 calls/minute rate limit.
- If a symbol fetch fails all retries, sentiment is set to neutral and marked as low-coverage for that day. Pipeline continues.

---

## API Key Security
- Finnhub API key is stored in AWS Secrets Manager under the key name `project-intelligent/finnhub-api-key`.
- The key is never written to any repository file, config file, or log output.
- Pipeline code reads the key from Secrets Manager at runtime using IAM role access.
- On local laptop failover, the key is read from a local `.env` file that is gitignored.

---

## Consequences

### Positive
- Zero cost: Finnhub free tier has no daily call cap and no time limit.
- No NLP library needed in Phase 1: sentiment scores are pre-computed server-side.
- Covers 30-symbol universe within the rate limit with sequential fetching.
- Pre-scored fields (bullishPercent, bearishPercent) are directly usable as features.

### Negative
- Small-cap symbols may have low or zero article coverage; sentiment defaults to neutral for these.
- Finnhub score methodology is a black box; the exact NLP model used is not disclosed.
- If Finnhub changes its free tier terms, a replacement source evaluation is required.

---

## Revisit Trigger
- Revisit if Finnhub removes or restricts its free sentiment endpoint.
- Revisit in Phase 3 when adding event-type tagging (earnings, M&A, guidance) — may require a secondary source or NLP layer.
- Revisit if small-cap coverage gaps cause the sentiment signal to be unreliable for that cap tier.

---

## Guardrails

### G1 - API Key Must Never Be in Code
- Any commit containing a Finnhub API key pattern is blocked by the pre-commit hook defined in doc 13.
- If accidentally committed, the key must be rotated immediately.

### G2 - Coverage Gate Alignment
- The low-coverage rule (< 2 articles in last week → neutral score) defined in sentiment_analysis_architecture.md G1 must be enforced using the news_intensity field from Finnhub.
- Pipeline must not pass a sentiment score for a low-coverage symbol to the composite scorer without the low-coverage flag.

### G3 - Fallback Is Neutral, Not Estimated
- When Finnhub is unavailable and the RSS fallback is active, all sentiment scores are set to 0 (neutral) and marked as fallback_mode = true.
- Estimated or interpolated sentiment scores during fallback mode are not permitted.

### G4 - Rate Limit Respect
- Sentiment fetch jobs must not exceed 60 API calls per minute.
- Parallel fetching that could exceed the rate limit is a guardrail violation.
