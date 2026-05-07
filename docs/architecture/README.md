# Stock Prediction Architecture - Document Map

This folder is the architecture source of truth for the project.

## Read Order
1. 01_scope_and_constraints.md
2. 02_universe_selection_pre_landing.md
3. 03_data_architecture_medallion.md
4. 04_model_strategy_and_serving.md
5. 05_validation_backtesting_and_risk.md
6. 06_platform_mlops_observability_security.md
7. 07_phased_rollout.md
8. 08_data_ingestion_architecture.md
9. 09_pipeline_orchestration_architecture.md
10. 10_feature_engineering_architecture.md
11. 11_label_engineering_architecture.md
12. 12_aws_cost_model.md
13. 13_github_repository_structure.md
14. 14_operations_and_automation_guide.md

## Analysis Framework Documents
- ../analysis/fundamental_analysis_architecture.md
- ../analysis/technical_analysis_architecture.md
- ../analysis/quantitative_analysis_architecture.md
- ../analysis/factor_analysis_architecture.md
- ../analysis/sentiment_analysis_architecture.md
- ../analysis/macroeconomic_analysis_architecture.md
- ../analysis/regime_analysis_architecture.md
- ../analysis/market_microstructure_analysis_architecture.md
- ../analysis/theories_and_algorithm_playbook.md

## Program Guardrails
- Architecture-first, no implementation in this phase.
- AWS free-tier friendly choices only.
- Mandatory segmentation:
  - Cap tier: large, mid, small
  - Trading horizon: intraday, swing, long
- Mandatory medallion data architecture: bronze, silver, gold.

## Architectural Decision Records (ADR)
All technology adoption or rejection decisions are documented as ADRs.
- ../adr/ADR-001-kafka-decision.md — Kafka deferred; using EventBridge + S3 + Lambda for batch pipeline.
- ../adr/ADR-002-iceberg-decision.md — Iceberg adopted for Silver and Gold layers; Bronze stays plain parquet.
- ../adr/ADR-003-database-decision.md — PostgreSQL deferred; DynamoDB for predictions and audit logs; SQLite for model metadata.
- ../adr/ADR-004-backup-and-failover.md — AWS cloud primary; local laptop secondary with daily sync; full failover capability.
- ../adr/ADR-005-news-api-decision.md — Finnhub as primary sentiment source; pre-computed scores; RSS fallback.
