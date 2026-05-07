# ADR-001: Kafka Adoption Decision

## Status
Deferred - revisit at intraday phase entry

## Date
2026-05-07

## Context
The platform requires a data transport and pipeline orchestration layer for ingesting market data, triggering transformations, and delivering predictions. Apache Kafka was evaluated as a candidate for this role.

The current phase focuses on swing trading with daily OHLCV bar ingestion running on a near-zero budget using AWS free tier only.

## Decision Drivers
- Budget: near-zero, AWS free tier only.
- Data frequency: daily bars only for swing and long horizons.
- Pipeline pattern: batch pull from free data sources (yfinance, FRED).
- Prediction serving: batch inference once per day.
- Team size and operational complexity: small, architecture-first platform engineering approach.

## Options Evaluated

### Option 1 - Apache Kafka Self-Managed on EC2
- Free software license.
- Requires minimum 2 to 4 GB RAM per broker.
- AWS free tier EC2 (t2.micro) provides only 1 GB RAM.
- Running Kafka on t2.micro is operationally unstable and not viable.
- Verdict: not viable on free tier.

### Option 2 - AWS MSK (Managed Kafka)
- Fully managed service on AWS.
- Not included in AWS free tier.
- Minimum cost approximately $0.21 per broker per hour.
- Monthly cost would exceed the zero-budget constraint immediately.
- Verdict: rejected due to cost.

### Option 3 - Confluent Cloud Free Tier
- Kafka-as-a-service with a free tier offering.
- Free tier limit: 5 GB storage, limited throughput, no SLA.
- Suitable only for learning and prototyping.
- Not suitable for reliable daily production pipelines.
- Verdict: acceptable for learning only, not for production architecture.

### Option 4 - AWS EventBridge + S3 + Lambda (Selected for Now)
- Fully serverless and batch-oriented.
- AWS free tier covers the usage volumes for daily swing pipeline.
- EventBridge schedules daily ingestion trigger at no cost within free-tier limits.
- Lambda handles lightweight orchestration within free-tier invocation limits.
- S3 stores bronze, silver, and gold data within free-tier storage limits.
- No streaming infrastructure to manage.
- Verdict: selected for swing and long horizon phases.

## Decision
Kafka is not adopted at this time.

The current architecture uses EventBridge for scheduling, Lambda for orchestration, and S3 for medallion storage. This is sufficient for the daily batch pattern required by the swing trading model.

## Rationale
Kafka solves a real-time streaming problem. The swing architecture is a batch problem. Introducing Kafka now would add significant operational complexity and cost with no benefit to the current pipeline design.

## Consequences

### Positive
- Zero additional infrastructure cost.
- No operational overhead of managing Kafka brokers.
- Pipeline remains simple and debuggable.
- Architecture stays within free-tier budget constraint.

### Negative
- No real-time event streaming capability in current design.
- Intraday expansion will require a streaming transport layer to be designed and introduced.
- Migrating from batch-pull to event-driven streaming will require pipeline rework at that time.

## Revisit Trigger
Revisit this decision at the start of the intraday horizon phase with the following questions:
1. Is the free tier budget still a hard constraint?
2. Is Confluent Cloud free tier sufficient for intraday bar volume?
3. Is there an alternative lightweight streaming option (e.g., AWS Kinesis free tier, Redis Streams) that fits the budget better than Kafka?

## Alternatives to Consider at Intraday Phase
- AWS Kinesis Data Streams: 1 shard free for 12 months under new account free tier.
- Confluent Cloud free tier: for low-volume intraday prototyping only.
- Redis Streams on EC2 micro: lightweight in-process stream for small bar volumes.
- Self-managed Kafka on a larger EC2: only if budget constraint is lifted.

## References
- Architecture constraint: docs/architecture/01_scope_and_constraints.md
- Data pipeline design: docs/architecture/03_data_architecture_medallion.md
- Phased rollout: docs/architecture/07_phased_rollout.md
