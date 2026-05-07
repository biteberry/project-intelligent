# Sentiment Analysis Architecture

## Purpose
Capture short-horizon narrative shifts not yet reflected in price.

## Sources (Free-Tier Friendly)

### News API Source Decision (ADR Required Before Implementation)
A specific free news API must be selected before sentiment ingestion is implemented. An ADR (ADR-005) is required. The following candidates are evaluated at architecture level:

| Candidate | Free Tier | Pre-Computed Sentiment | API Key Required | Notes |
| --- | --- | --- | --- | --- |
| Finnhub | 60 calls/minute, unlimited news | Yes (pre-scored polarity) | Yes (free registration) | Best fit: provides company news with sentiment score already attached |
| Alpha Vantage | 25 calls/day (free) | Yes (NEWS_SENTIMENT endpoint) | Yes (free registration) | Very tight daily limit; may not cover 30 symbols adequately |
| NewsAPI | 100 requests/day, 1 month history | No (raw articles only) | Yes (free registration) | Requires NLP processing layer; history limit is a problem for backfill |
| Yahoo Finance RSS | Unlimited (unofficial) | No (raw headlines only) | No | No official API contract; brittle; not recommended for production |

**Recommended primary candidate: Finnhub**
- Provides symbol-level news with pre-computed sentiment scores (bullish/bearish/neutral + score).
- 60 calls/minute is sufficient for 30 symbols in a batch job.
- Free tier has no daily call cap, only a rate limit.
- Sentiment scores are pre-computed server-side; no NLP library needed in Phase 1.

**Decision: ADR-005 signed off.** Finnhub is the selected primary source. See docs/adr/ADR-005-news-api-decision.md for the full evaluation.

### Scope
- News articles linked to specific symbols in the active universe.
- Financial headlines and brief summaries only; full article text is not fetched.

## Processing Logic
1. Text cleaning and symbol linking
2. Polarity score and confidence score
3. Recency decay weighting
4. News intensity and novelty scoring

## Risk Controls
- Use sentiment as auxiliary signal in phase 1.
- Down-weight sentiment during low coverage or noisy periods.

## Guardrails

### G1 - Coverage Gate
- If fewer than 2 news articles are available for a symbol in the past 5 trading days, the sentiment score is set to neutral and marked as low-coverage.
- Low-coverage scores are not estimated; they are neutralized and flagged.

### G2 - Noise Period Dampening
- During market-wide high-news-volume events, sentiment scores across all symbols are automatically down-weighted in the composite.
- The dampening rule is predefined and does not require manual intervention.

### G3 - Symbol Linkage
- Only articles with confirmed symbol linkage are used in score computation.
- Unlinked or ambiguously linked articles are discarded and logged.

### G4 - Recency Cutoff
- Articles older than 5 trading days have zero contribution to the current sentiment score.
- Stale articles are excluded, not down-weighted.

### G5 - Auxiliary Signal Only
- Sentiment score alone must not drive inclusion or exclusion from the universe.
- It is a composite weight input only and must not be used as a standalone gate.

### G6 - Confidence Floor
- Sentiment confidence below 0.4 results in the score being marked unreliable.
- Unreliable sentiment scores are excluded from the composite ranking for that symbol on that date.

## Output Fields
- sentiment_score
- sentiment_confidence
- news_intensity
- sentiment_as_of_date

---

## Sentiment Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Sentiment Signal | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Headline polarity score | Positive, negative, neutral label | 4 | 2 | 3 | 2.50 | Must-have now |
| News intensity | Article count per symbol per day | 3 | 1 | 3 | 2.60 | Must-have now |
| Recency-weighted sentiment | Polarity with exponential decay | 4 | 2 | 3 | 2.50 | Must-have now |
| Novelty flag | First-occurrence vs repeat news | 3 | 3 | 2 | 1.50 | Add next |
| Event-type tagging | Earnings, M&A, guidance, litigation | 4 | 3 | 2 | 1.80 | Add next |
| Social media sentiment | Crowd-sourced signal aggregation | 3 | 4 | 1 | 1.00 | Add later |
| Earnings call tone | NLP on call transcripts | 4 | 5 | 1 | 0.90 | Add later |

Interpretation:
- Priority score >= 2.00: must-have for swing now.
- Priority score 1.20 to 1.99: add next.
- Priority score < 1.20: add later.

## Sentiment Architecture Backlog for Swing

Must-have now:
- Headline polarity score.
- News intensity count.
- Recency-weighted sentiment score.

Add next:
- Novelty flag.
- Event-type tagging.

Add later:
- Social media sentiment.
- Earnings call NLP tone.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Recency-weighted polarity: 50%
- News intensity: 30%
- Novelty and event flag: 20% (once available)
