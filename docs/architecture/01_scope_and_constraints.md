# 01 Scope and Constraints

## Objective
Design an end-to-end platform architecture to predict stock movement and expected returns, then serve outputs as a usable product.

## Market Scope
- **Primary market: Indian equities (NSE and BSE).** The platform is designed India-first. NSE-listed stocks use yfinance suffix `.NS`; BSE-listed stocks use `.BO`.
- **Secondary market: US equities.** US-listed stocks are added as a secondary market with no suffix in yfinance.
- The architecture uses a `market_context` configuration tag on every symbol to control market-specific behaviour: index source, macro data source, cost assumptions, and India-specific risk features.
- All analysis frameworks, technical indicators, ML model design, and pipeline infrastructure are **market-agnostic** and work for both markets without modification.
- Market-specific components (regime index, macro source, cost model, regulatory flags) are configured per symbol through `market_context`, not hardcoded.

## Constraints
- Budget: near-zero using AWS free tier.
- Tooling: open-source stack.
- Source control: GitHub.
- Observability and metrics are required before production maturity.

## Mandatory Segmentation
1. Cap tier segmentation:
- Large cap: low risk
- Mid cap: medium risk
- Small cap: high risk

2. Trading horizon segmentation:
- Intraday
- Swing
- Long

## Phase-1 Focus
- Start with swing horizon only.
- Keep scope to daily bars and batch predictions.
- Avoid high-frequency and complex low-latency execution architecture.

## Success Definition
- Clear, auditable architecture covering data, model, validation, operations, and governance.
- Design supports later implementation without rework to core boundaries.

---

## Guardrails

### G1 - Horizon Scope
- No intraday or long horizon work begins until the swing milestone is fully validated and signed off.
- Any expansion to a new horizon requires a formal architecture amendment before any design or implementation activity.

### G2 - Budget
- No paid data sources, paid APIs, or paid compute resources are used without an explicit architecture review and approval.
- If a free-tier limit is approaching, an alert is raised and a mitigation plan is required before continuing.

### G3 - Segmentation Integrity
- Every dataset, model artifact, prediction, and evaluation report must carry cap_tier and horizon tags.
- Any asset missing these mandatory tags is rejected by the pipeline and not promoted to the next stage.

### G4 - Architecture-First
- No implementation work starts on any component before the architecture for that phase is documented and signed off.
- Informal verbal approvals are not accepted; written sign-off is required.

### G5 - Tooling
- Only open-source tools approved in the architecture are permitted.
- Introduction of a new library or service requires architecture review before use in any layer.
