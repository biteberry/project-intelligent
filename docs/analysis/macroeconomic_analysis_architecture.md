# Macroeconomic Analysis Architecture

## Purpose
Incorporate macro environment context that influences sector and style performance.

## Macro Domains
1. Rates and yield curve
2. Inflation trend
3. Growth activity proxies
4. Labor market health
5. Liquidity and policy stance

## Architecture Logic
- Build macro regime tags and map them to sector sensitivity profiles.
- Use macro as context feature, not sole selector, for swing horizon.

## Data Cadence
- Weekly to monthly updates depending on indicator release frequency.

## Guardrails

### G1 - Data Freshness
- Macro indicators with a release lag greater than 30 calendar days must be flagged as lagging and their weight in the composite reduced proportionally.

### G2 - Source Reliability
- Only official or established free sources (FRED, central bank publications, government statistical releases) are used.
- Unverified third-party sources are rejected.

### G3 - Conflicting Signal Review
- When two or more macro domains send conflicting directional signals, the macro regime tag is placed in a conflict state.
- Conflict state is logged and a human review is triggered before the tag is used in composite scoring.

### G4 - Staleness Gate
- A macro_regime tag older than 35 calendar days is treated as stale.
- Stale macro tags cause the composite to use a neutral macro weight until the tag is refreshed.

### G5 - Context Only
- Macro signals must not directly select or exclude symbols from the universe.
- They operate as weighting context and regime adjustment within the composite only.

### G6 - Single-Indicator Override Ban
- No single macro indicator may override a composite regime tag without a documented justification and approver sign-off.
- Single-indicator overrides without documentation are rejected.

## Output Fields
- macro_regime
- macro_tailwind_score
- rate_sensitivity_score
- inflation_sensitivity_score
- macro_as_of_date

---

## Macroeconomic Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Macro Signal | Sub-factors Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Rate and yield curve state | Short and long rate trend, curve slope | 5 | 2 | 5 | 3.70 | Must-have now |
| Inflation trend | CPI trend direction and velocity | 4 | 2 | 5 | 3.10 | Must-have now |
| Macro regime tag | Expansion, contraction, stagflation label | 5 | 3 | 4 | 2.90 | Must-have now |
| Liquidity and policy stance | Central bank posture proxy | 4 | 3 | 4 | 2.60 | Must-have now |
| Growth activity proxy | PMI or coincident indicator trend | 4 | 2 | 4 | 2.80 | Must-have now |
| Labor market health | Unemployment trend direction | 3 | 2 | 5 | 2.60 | Add next |
| Sector macro sensitivity map | Rate and inflation sensitivity by sector | 4 | 3 | 3 | 2.30 | Add next |
| Yield spread risk | Credit spread trend proxy | 3 | 3 | 3 | 1.80 | Add later |

Interpretation:
- Priority score >= 2.60: must-have for swing now.
- Priority score 2.00 to 2.59: add next.
- Priority score < 2.00: add later.

## Macroeconomic Architecture Backlog for Swing

Must-have now:
- Rate and yield curve state.
- Inflation trend label.
- Macro regime tag (expansion, contraction, stagflation).
- Liquidity and policy stance proxy.
- Growth activity indicator.

Add next:
- Labor market health signal.
- Sector macro sensitivity mapping.

Add later:
- Credit spread and yield spread risk overlay.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Macro regime tag: 35%
- Rate and yield curve state: 25%
- Inflation trend: 20%
- Growth activity proxy: 20%
