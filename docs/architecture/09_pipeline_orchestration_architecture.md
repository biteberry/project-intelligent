# 09 Pipeline Orchestration Architecture

## Purpose
Define the job chain, trigger design, execution environment, dependency model, failure handling, and orchestration guardrails for the full data and ML pipeline.

---

## Execution Environment Split

The pipeline is split between two execution environments by job type:

| Environment | Role | Justification |
| --- | --- | --- |
| AWS Lambda | Triggers, lightweight coordination, status checks, API serving | Serverless, zero idle cost, scales to zero |
| EC2 t3.micro | Heavy compute: Bronze→Silver, Silver→Gold, model training, daily sync | Needs 1 GB RAM, file system access, Python libraries, long run time |

Lambda has a 15-minute timeout and 1 GB RAM ceiling. Bronze→Silver promotion, feature engineering, and model training all exceed these limits for a 30-symbol universe. These jobs run directly on EC2, triggered via Lambda invoking an EC2 Systems Manager Run Command.


---

## Pipeline Job Catalog

| Job ID | Name | Environment | Trigger | Outputs |
| --- | --- | --- | --- | --- |
| J01 | universe_selection | EC2 | EventBridge (weekly, Sunday 14:00 UTC) | S3 universe snapshot, DynamoDB audit record |
| J02 | market_data_ingestion | EC2 | EventBridge (daily Mon-Fri, 21:00 UTC) | Bronze OHLCV Parquet files, DynamoDB audit record |
| J03 | macro_data_ingestion | EC2 | EventBridge (weekly, Sunday 15:00 UTC) | Bronze macro Parquet files, DynamoDB audit record |
| J04 | bronze_to_silver | EC2 | Triggered by J02 completion | Silver Iceberg snapshot, DynamoDB audit record |
| J05 | silver_to_gold | EC2 | Triggered by J04 completion | Gold Iceberg snapshot, DynamoDB audit record |
| J06 | model_training | EC2 | EventBridge (weekly, Sunday 16:00 UTC) or manual trigger | Model artifact in S3, metadata in SQLite, DynamoDB audit record |
| J07 | batch_inference | EC2 | Triggered by J05 completion (if new Gold snapshot) | Predictions in DynamoDB, DynamoDB audit record |
| J08 | local_sync | EC2 | Triggered by J07 completion | Local PostgreSQL updated, local S3 mirror updated |
| J09 | universe_new_symbol_backfill | EC2 | Triggered by J01 when new symbols added | Bronze backfill for new symbols |

---

## Daily Pipeline Flow (Monday through Friday)

```
EventBridge 21:00 UTC
    └── J02 market_data_ingestion (EC2)
            └── on success → J04 bronze_to_silver (EC2)
                    └── on success → J05 silver_to_gold (EC2)
                            └── on success → J07 batch_inference (EC2)
                                    └── on success → J08 local_sync (EC2)
```

Each job writes its status (success or failure) to DynamoDB audit before the next job is triggered. If any job fails, the chain stops at that point. Downstream jobs do not run on upstream failure.

---

## Weekly Pipeline Flow (Sunday)

```
EventBridge 14:00 UTC
    └── J01 universe_selection (EC2)
            └── on success with new symbols → J09 new_symbol_backfill (EC2)
            └── on completion (with or without new symbols) → (daily pipeline resumes Monday)

EventBridge 15:00 UTC
    └── J03 macro_data_ingestion (EC2)

EventBridge 16:00 UTC
    └── J06 model_training (EC2)
            └── on success → model artifact written to S3
            └── on success → J08 local_sync (EC2) to pull new model artifact
```

Model training runs weekly regardless of whether a new Gold snapshot was created that week. Training always references the most recently promoted Gold snapshot version. If no new Gold snapshot exists, training is skipped and an informational log is written.

---

## Trigger Architecture

### EventBridge Rules

| Rule Name | Schedule | Target |
| --- | --- | --- |
| daily-ingestion-trigger | cron(0 21 ? * MON-FRI *) | Lambda: invoke EC2 SSM run command for J02 |
| weekly-universe-trigger | cron(0 14 ? * SUN *) | Lambda: invoke EC2 SSM run command for J01 |
| weekly-macro-trigger | cron(0 15 ? * SUN *) | Lambda: invoke EC2 SSM run command for J03 |
| weekly-training-trigger | cron(0 16 ? * SUN *) | Lambda: invoke EC2 SSM run command for J06 |

### Lambda Role in Orchestration
Lambda functions act as thin coordinators only:
- Read the EventBridge trigger and validate schedule context.
- Send an SSM Run Command to EC2 to start the target job script.
- Write a trigger audit record to DynamoDB.
- Lambda does not run any data processing logic itself in Phase 1.

### EC2 Job Execution
- Jobs run as Python scripts directly on the EC2 instance.
- Each job script is a single entry point with well-defined inputs and outputs.
- Scripts read the active universe and latest snapshot references from DynamoDB at start time.
- Scripts write their completion status and outputs to DynamoDB audit at end time.

---

## Job Dependency Model

### Status Check Before Downstream Trigger
Each job reads the DynamoDB audit table to confirm upstream job status before starting:
- J04 checks J02 completed successfully today.
- J05 checks J04 completed successfully today.
- J07 checks J05 completed successfully today and a new Gold snapshot exists.
- J08 checks J07 completed successfully today.

### Downstream Job Skip Conditions
- If the upstream job failed today, the downstream job writes a "skipped due to upstream failure" audit record and exits cleanly.
- Skipped jobs do not trigger further downstream jobs.
- CloudWatch alert is raised when a skip occurs.

---

## Step Functions Evaluation

### Why Step Functions is Not Used in Phase 1
- AWS Step Functions standard workflows cost $0.025 per 1000 state transitions.
- Daily pipeline: approximately 10 state transitions × 22 trading days = 220 transitions per month.
- Weekly pipeline: approximately 20 state transitions × 4 weeks = 80 transitions per month.
- Total: ~300 transitions per month = ~$0.0075 per month. Below billing alarm but still a paid service.
- The DynamoDB-status-check pattern achieves the same dependency management at zero additional cost.
- Step Functions is a valid upgrade path if pipeline complexity grows significantly (see Revisit Trigger below).

### Revisit Trigger for Step Functions
- Revisit if the job count exceeds 15 and the manual status-check pattern becomes error-prone.
- Revisit at intraday phase when sub-minute orchestration precision is needed.

---

## Failure Handling

| Failure Scenario | Response | Alert |
| --- | --- | --- |
| J02 ingestion fails | Stop chain, log, alert | CloudWatch alarm + SNS email |
| J04 bronze-to-silver fails | Stop chain, log, alert | CloudWatch alarm + SNS email |
| J05 silver-to-gold fails | Stop chain, log, alert | CloudWatch alarm + SNS email |
| J06 training fails | Log failure, retain previous model in serving | CloudWatch alarm + SNS email |
| J07 inference fails | Log failure, serve stale predictions with staleness flag | CloudWatch alarm + SNS email |
| J08 sync fails | Log failure, retry next day | CloudWatch warning |
| Lambda invocation fails | Retry twice via EventBridge built-in retry, then alert | CloudWatch alarm + SNS email |
| EC2 instance stopped | Lambda SSM command fails, alert fires | CloudWatch alarm + SNS email |

### Stale Prediction Policy
- If J07 inference does not run today (upstream failure or inference failure), predictions from the previous run are served.
- All prediction responses include a prediction_date field; consumers can detect staleness by comparing prediction_date to the current date.
- Predictions older than 2 trading days are flagged with a stale=true field in the API response.

---

## EC2 Instance Management

### Instance State
- EC2 t3.micro runs continuously (24/7) to remain within the 750-hour free-tier monthly allocation.
- Stopping and starting the instance does not save cost within free tier; it only risks missing scheduled job windows.
- Instance must be running at all scheduled trigger windows.

### Process Management
- Each job script is executed by the SSM Run Command as a foreground process.
- No systemd services or cron jobs on EC2; all scheduling is owned by EventBridge.
- Only one pipeline job runs on EC2 at a time; concurrent execution is not permitted in Phase 1 due to RAM constraints.

### EC2 Health Check
- A lightweight CloudWatch agent runs on EC2 reporting CPU, memory, and disk metrics.
- CloudWatch alarm fires if the instance is unreachable for more than 10 minutes during a scheduled window.

---

## Pipeline Run ID Design
Every job instance is assigned a run_id at start time:
- Format: `{job_id}_{YYYYMMDD}_{HHMMSS}` (example: `J02_20260507_210015`)
- run_id is written to: DynamoDB audit record, Bronze partition path (ingestion_run_id field), model artifact path prefix.
- run_id enables full lineage tracing from a prediction back through inference → gold snapshot → silver snapshot → bronze partition → ingestion run.

---

## Guardrails

### G1 - No Concurrent Pipeline Jobs
- Only one job runs on EC2 at any time.
- If a previous job is still running when a new trigger fires, the new trigger writes a "skipped due to active job" audit record and exits.
- This prevents RAM contention and partial writes on t3.micro.

### G2 - Upstream Status Gate
- Every job in the daily chain must read the DynamoDB audit table and confirm upstream job success before proceeding.
- A job that starts without confirming upstream success is a pipeline violation.

### G3 - Audit Record Mandatory
- Every job must write a DynamoDB audit record at completion (success or failure).
- A job that exits without writing an audit record is treated as failed by all downstream jobs.

### G4 - EC2 Availability
- EC2 t2.micro must be running at all scheduled EventBridge trigger windows.
- An EC2 instance in stopped state at trigger time is treated as a pipeline failure and raises an alert.
- Manual instance stops during scheduled windows require advance notification and a mitigation plan.

### G5 - Lambda Thin Proxy
- Lambda functions in this pipeline must not contain data processing logic.
- Lambda is restricted to: reading trigger context, sending SSM Run Command, writing trigger audit record.
- Any data processing logic found in a Lambda function is moved to EC2 before deployment.

### G6 - Stale Model Age
- The J07 inference job checks model training date before running.
- If the active model was trained on a Gold snapshot older than 30 days, inference is blocked and an alert fires.
- This enforces the model age guardrail defined in 04_model_strategy_and_serving.md G7.

### G7 - Local Sync Must Follow Inference
- J08 local sync must run after every successful J07 inference run.
- A day where inference succeeds but local sync is skipped is a backup policy violation and must be resolved within 24 hours.
