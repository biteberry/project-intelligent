# Stock Market Prediction Architecture

This file is the entry point to the split architecture documents.

## Primary Architecture Docs
1. docs/architecture/README.md
2. docs/architecture/01_scope_and_constraints.md
3. docs/architecture/02_universe_selection_pre_landing.md
4. docs/architecture/03_data_architecture_medallion.md
5. docs/architecture/04_model_strategy_and_serving.md
6. docs/architecture/05_validation_backtesting_and_risk.md
7. docs/architecture/06_platform_mlops_observability_security.md
8. docs/architecture/07_phased_rollout.md
9. docs/architecture/08_data_ingestion_architecture.md
10. docs/architecture/09_pipeline_orchestration_architecture.md
11. docs/architecture/10_feature_engineering_architecture.md
12. docs/architecture/11_label_engineering_architecture.md
13. docs/architecture/12_aws_cost_model.md
13. docs/architecture/13_github_repository_structure.md
14. docs/architecture/14_operations_and_automation_guide.md
## Analysis Architecture Docs
1. docs/analysis/fundamental_analysis_architecture.md
2. docs/analysis/technical_analysis_architecture.md
3. docs/analysis/quantitative_analysis_architecture.md
4. docs/analysis/factor_analysis_architecture.md
5. docs/analysis/sentiment_analysis_architecture.md
6. docs/analysis/macroeconomic_analysis_architecture.md
7. docs/analysis/regime_analysis_architecture.md
8. docs/analysis/market_microstructure_analysis_architecture.md
9. docs/analysis/theories_and_algorithm_playbook.md

## Product Requirements Document
- docs/prd/PRD_v1.0.md — Version 1.0, 2026-05-07. Covers 20 functional requirements, 7 NFRs, data requirements, risk register, and Phase 1 definition of done.

## Project Management
- docs/project-management/github_project_setup_guide.md — GitHub JIRA-equivalent setup: repo creation, 27-label taxonomy, 8 milestones, GitHub Projects v2 board, 3 issue templates, full issue breakdown (FEATURE-001 to FEATURE-021).
- .github/ISSUE_TEMPLATE/feature.md — Feature (epic) issue template
- .github/ISSUE_TEMPLATE/story.md — Story issue template
- .github/ISSUE_TEMPLATE/task.md — Task issue template
- .github/ISSUE_TEMPLATE/bug.md — Bug issue template

## Current Program Position
- Architecture phase complete.
- Swing horizon is the first target.
- Medallion architecture is mandatory.
- Cap-tier segmentation is mandatory.

## Architectural Decision Records
- docs/adr/ADR-001-kafka-decision.md
- docs/adr/ADR-002-iceberg-decision.md
- docs/adr/ADR-003-database-decision.md
- docs/adr/ADR-004-backup-and-failover.md
- docs/adr/ADR-005-news-api-decision.md — Finnhub as primary sentiment source; RSS fallback.
