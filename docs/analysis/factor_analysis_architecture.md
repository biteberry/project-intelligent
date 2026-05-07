# Factor Analysis Architecture

## Purpose
Evaluate stocks using known risk premia to support explainable selection decisions.

## Primary Factors
1. Value
2. Momentum
3. Quality
4. Size
5. Low volatility

## Architecture Logic
- Compute cross-sectional factor ranks within comparable universe buckets.
- Normalize factor exposures to avoid single-factor dominance.
- Monitor factor crowding and concentration risk.

## Use in Selection
- Combine factor_score with technical and fundamental layers.
- Apply factor constraints so final universe stays diversified.

## Guardrails

### G1 - Cross-Sectional Integrity
- Factor ranks must be computed within a consistent universe snapshot at each date.
- Mixing factor ranks from different universe vintages or dates is not permitted.

### G2 - Normalization Before Composite
- Raw factor values must be normalized or cross-sectionally ranked before entering the composite score.
- Unnormalized raw values in the composite are rejected.

### G3 - Factor Concentration Limit
- No single factor may contribute more than 40% weight in the composite factor score without a documented architecture review and approval.

### G4 - Cap-Tier Separation
- Factor ranks must be computed separately within each cap tier to avoid size bias contaminating cross-tier comparisons.
- Pooled ranking across cap tiers without tier-separation is not accepted.

### G5 - Crowding Alert
- If the top decile of any factor contains more than 40% of symbols from a single sector, a crowding alert is raised.
- Crowded factors are down-weighted automatically until the concentration resolves.

### G6 - As-Of Date Provenance
- Every factor score record must carry a factor_as_of_date.
- Scores without date provenance are rejected from selection.

## Output Fields
- factor_score
- value_exposure
- momentum_exposure
- quality_exposure
- size_exposure
- low_vol_exposure
- factor_as_of_date

---

## Factor Decision Matrix for Swing Prioritization

Scoring scale:
- Usefulness for swing: 1 (low) to 5 (high)
- Complexity to compute: 1 (low) to 5 (high)
- Data availability on free sources: 1 (hard) to 5 (easy)

Weighted priority formula:
Priority Score = 0.50 x Usefulness + 0.30 x Data Availability - 0.20 x Complexity

| Factor | Sub-signals Included | Usefulness | Complexity | Data Availability | Priority Score | Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Momentum | 1m and 3m return rank, trend persistence | 5 | 2 | 5 | 3.70 | Must-have now |
| Low volatility | Realized vol rank, beta proxy | 5 | 2 | 5 | 3.70 | Must-have now |
| Quality | ROE rank, margin consistency | 4 | 2 | 4 | 2.80 | Must-have now |
| Value | P/E and EV/EBITDA cross-sectional rank | 4 | 2 | 4 | 2.80 | Must-have now |
| Size | Market cap tier (large/mid/small) | 3 | 1 | 5 | 2.80 | Must-have now |
| Factor crowding check | Factor concentration and overlap monitor | 3 | 3 | 4 | 2.10 | Add next |
| Factor regime sensitivity | Factor performance by regime state | 4 | 4 | 4 | 2.40 | Add next |
| Composite factor tilt | Combined multi-factor rank score | 5 | 3 | 4 | 3.10 | Must-have now |

Interpretation:
- Priority score >= 2.80: must-have for swing now.
- Priority score 2.20 to 2.79: add next.
- Priority score < 2.20: add later.

## Factor Architecture Backlog for Swing

Must-have now:
- Momentum factor rank.
- Low volatility factor rank.
- Quality factor rank.
- Value factor rank.
- Size tier (already captured in cap_tier field).
- Composite multi-factor rank score.

Add next:
- Factor regime sensitivity (factor performance by regime).
- Factor crowding monitor.

## Weight Allocation in Composite Universe Score (Swing Baseline)
- Momentum: 30%
- Low volatility: 25%
- Quality: 20%
- Value: 15%
- Size: 10%
