# 12 AWS Free-Tier Cost Model

## Purpose
Estimate monthly AWS resource consumption for the designed 30-symbol swing pipeline, confirm it fits within free-tier limits, identify where limits are tight, and define escalation rules before any cost is incurred.

---

## Free-Tier Reference (Services Used in This Platform)

| AWS Service | Free-Tier Allowance | Time Limit |
| --- | --- | --- |
| EC2 t2.micro | 750 instance-hours per month | 12 months from account creation |
| S3 Storage | 5 GB | 12 months |
| S3 PUT/COPY/POST requests | 2,000 per month | 12 months |
| S3 GET/SELECT requests | 20,000 per month | 12 months |
| Lambda invocations | 1,000,000 per month | Permanent (free forever) |
| Lambda compute | 400,000 GB-seconds per month | Permanent |
| DynamoDB storage | 25 GB | Permanent (free forever) |
| DynamoDB write capacity | 25 WCU | Permanent |
| DynamoDB read capacity | 25 RCU | Permanent |
| API Gateway | 1,000,000 API calls per month | 12 months |
| EventBridge | 14,000,000 custom events per month | Permanent |
| CloudWatch logs | 5 GB ingestion per month | Permanent |
| CloudWatch metrics | 10 custom metrics | Permanent |
| CloudWatch alarms | 10 alarms | Permanent |
| SNS | 1,000 email notifications per month | Permanent |
| AWS Glue Catalog | 1,000,000 objects stored | Permanent |
| SSM Run Command | Free for EC2 managed instances | Permanent |

**Note:** EC2 and S3 free tier is time-limited to 12 months. After 12 months, these services become paid. The billing alarm at $0.10 (defined in ADR-004) will fire long before costs accumulate. After 12 months, evaluate EC2 Spot pricing or migrate heavy compute to the local laptop (already designed in ADR-004).

---

## Monthly Usage Estimates: 30-Symbol Swing Universe

### EC2 t2.micro
- Instance running 24/7: 24 hours × 31 days = 744 hours per month.
- Free tier: 750 hours per month.
- Utilization: 744 / 750 = **99.2% of free tier**.
- Status: within free tier but no headroom. A second EC2 instance would immediately incur cost.
- Guardrail: do not launch a second EC2 instance; all pipeline jobs share the single t2.micro.

### S3 Storage
Estimates for 30-symbol, 10-year backfill plus 12 months of daily data:

| Zone | Estimated Size | Notes |
| --- | --- | --- |
| Bronze OHLCV | ~150 MB | 30 symbols × 2520 days × ~2KB per row in Parquet |
| Bronze macro | ~10 MB | 8 FRED series × 2520 days × ~0.5KB |
| Silver Iceberg | ~300 MB | Bronze × ~2x for Iceberg metadata + cleaned enriched rows |
| Gold Iceberg | ~200 MB | Feature rows are wider; ~250 columns × 30 symbols × 2520 days |
| Model artifacts | ~50 MB | 5 models × ~10 MB each (serialized XGBoost/LightGBM) |
| Universe snapshots (S3 JSON) | ~5 MB | 52 weekly snapshots × ~100KB each |
| Iceberg metadata files | ~50 MB | Manifests, manifest lists, snapshot metadata |
| **Total estimated** | **~765 MB** | Well within 5 GB free tier |

- Utilization: ~765 MB / 5120 MB = **~15% of free tier**.
- Status: comfortable headroom. Alert is set at 80% (4 GB).

### S3 API Requests (PUT/POST)
Daily pipeline writes (Mon-Fri, 22 trading days per month):

| Operation | Frequency | Monthly Count |
| --- | --- | --- |
| Bronze OHLCV write (1 file per day per 10 symbols, batched) | 3 files × 22 days | 66 PUTs |
| Bronze macro write (weekly) | 1 file × 4 weeks | 4 PUTs |
| Silver Iceberg write (1 snapshot per day) | 1 snapshot × 22 days | 22 PUTs (manifest + data files ≈ 5 per snapshot) = ~110 PUTs |
| Gold Iceberg write (1 snapshot per day) | ~8 files per snapshot × 22 days | ~176 PUTs |
| Model artifact write (weekly) | 5 model files × 4 weeks | 20 PUTs |
| Universe snapshot write (weekly) | 1 file × 4 weeks | 4 PUTs |
| **Total estimated** | | **~380 PUTs/month** |

- Utilization: 380 / 2,000 = **~19% of free tier**.
- Status: well within limit. Even with growth to 100 symbols the estimate stays under 2,000.

### S3 API Requests (GET)
Daily pipeline reads (features, inference, sync):

| Operation | Frequency | Monthly Count |
| --- | --- | --- |
| Bronze reads for Silver promotion | ~30 files × 22 days | ~660 GETs |
| Silver reads for Gold promotion | ~30 files × 22 days | ~660 GETs |
| Gold reads for training (weekly) | ~100 files × 4 weeks | ~400 GETs |
| Gold reads for inference (daily) | ~30 files × 22 days | ~660 GETs |
| Model artifact reads for inference | 5 files × 22 days | ~110 GETs |
| Local sync reads | ~50 files × 22 days | ~1,100 GETs |
| **Total estimated** | | **~3,590 GETs/month** |

- Utilization: 3,590 / 20,000 = **~18% of free tier**.
- Status: comfortable.

### Lambda
- Invocations: 5 EventBridge triggers per week × 4 weeks = 20 invocations per month (daily triggers) + 4 weekly triggers × 3 = 12 = ~32 invocations per month.
- Lambda compute: each Lambda runs for under 30 seconds and uses 128 MB RAM.
- Compute: 32 × 30 seconds × 0.128 GB = ~122 GB-seconds per month.
- Free tier: 400,000 GB-seconds. Utilization: **<<1%**.
- Status: negligible Lambda usage; far below any limit.

### DynamoDB
Daily writes per month (22 trading days):

| Table | Writes per Day | Monthly Writes |
| --- | --- | --- |
| predictions | 30 symbols × 1 prediction each | 660 writes |
| pipeline_audit | ~8 job audit records per day | 176 writes |
| trigger audit (Lambda) | ~5 records per day | 110 writes |
| **Total writes** | | **~946 writes/month** |

- Each write is a single item (~1 KB).
- WCU consumed: ~946 writes / 30 days = ~32 writes/day. At a steady rate this is ~0.0004 WCU average (well under 25 WCU sustained).
- Peak WCU: a burst of 30 prediction writes in sequence = 30 WCU. This is at the free-tier limit for a brief burst. Predictions must be written sequentially with a short pause between records to spread WCU load.
- Read utilization: API reads for predictions. Assuming ~10 API calls per day: 10 × 22 = 220 reads per month. Negligible against 25 RCU.
- Status: within free tier. **Write burst design rule: batch predictions are written sequentially, not in parallel, with a 100ms pause between writes.**

### API Gateway
- Assumed usage: personal use only in Phase 1, ~10 manual API calls per day.
- Monthly: 10 × 31 = 310 calls.
- Free tier: 1,000,000 calls per month.
- Utilization: **<<1%**.
- Status: no concern.

### EventBridge
- ~35 scheduled events per month (daily + weekly triggers).
- Free tier: 14,000,000 events per month.
- Utilization: **<<1%**.
- Status: no concern.

### CloudWatch and SNS
- Log ingestion: estimated ~100 MB per month from pipeline logs.
- Custom metrics: ~8 (pipeline job durations, symbol counts, DynamoDB capacity).
- Alarms: ~8 (billing, DynamoDB RCU/WCU, S3 storage, EC2 health, universe size).
- SNS emails: estimated ~5 per month (alerts only).
- All within free-tier limits.

### Glue Catalog
- Iceberg table registrations: ~6 tables (bronze, silver_ohlcv, gold_features, gold_labels, macro, universe).
- Objects: well under 1,000,000 limit.
- Status: no concern.

---

## Free-Tier Risk Summary

| Service | Estimated Utilization | Risk Level | Action |
| --- | --- | --- | --- |
| EC2 t2.micro hours | 99.2% | High after 12 months | Plan local laptop failover (ADR-004); review at month 10 |
| S3 storage | 15% | Low | Alert at 80% (4 GB) |
| S3 PUT requests | 19% | Low | Alert if universe grows beyond 100 symbols |
| S3 GET requests | 18% | Low | Comfortable headroom |
| Lambda invocations | <<1% | None | No action needed |
| DynamoDB WCU (burst) | At limit during burst | Medium | Write predictions sequentially with 100ms pause |
| DynamoDB RCU | <<1% | None | No action needed |
| CloudWatch alarms | 8/10 | Medium | Reserve 2 alarms for future use; do not exceed 10 |
| API Gateway | <<1% | None | No action needed |

---

## Post-12-Month Plan

At the 12-month mark, EC2 and S3 free tiers expire:

| Service | Expected Monthly Cost After Free Tier |
| --- | --- |
| EC2 t2.micro (on-demand) | ~$8.50/month |
| S3 storage at 1 GB | ~$0.02/month |
| S3 API requests at current volume | ~$0.01/month |
| Total estimated | ~$8.53/month |

### Options at 12 Months
1. **Migrate heavy compute to local laptop** (already designed in ADR-004). EC2 is stopped or terminated. Only DynamoDB and S3 remain, which are permanent free tier. Cost drops to ~$0.03/month.
2. **EC2 Spot t2.micro**: approximately $0.004/hour vs $0.0116/hour on-demand. Cost drops to ~$3/month.
3. **Accept the ~$8.50/month cost** if platform is producing value.

The preferred default is Option 1: migrate to local laptop at the 12-month mark. This was designed from the start in ADR-004.

---

## Guardrails

### G1 - Billing Alarm is Mandatory
- A CloudWatch billing alarm at $0.10 must be configured before any AWS resource is created.
- No pipeline runs until this alarm is confirmed active.
- This is the primary defense against accidental cost accumulation.

### G2 - DynamoDB Write Sequencing
- Prediction batch writes must be sequential with a 100ms pause between items.
- Parallel DynamoDB writes that could burst above 25 WCU are a free-tier violation.

### G3 - Single EC2 Instance
- Only one EC2 t2.micro instance runs at any time.
- A second instance would immediately push EC2 hours over the 750-hour free-tier limit.
- Launching a second instance requires explicit architecture review and approval.

### G4 - S3 Write Batching
- Bronze OHLCV writes must batch all 30 symbols into a small number of files per day.
- Writing one file per symbol per day (30 PUT requests/day) would push monthly PUTs toward the 2,000 limit as the platform scales. Batch into cap-tier partitioned files.

### G5 - CloudWatch Alarm Budget
- Maintain a maximum of 10 CloudWatch alarms within the free tier.
- Current planned alarms: billing ($0.10), DynamoDB WCU warning, DynamoDB WCU critical, DynamoDB RCU warning, S3 storage warning, EC2 health, universe size warning, universe size critical = 8 alarms.
- Reserve the remaining 2 for future use. Do not add alarms beyond 10 without retiring an existing one.

### G6 - 12-Month Review Gate
- At month 10 (2 months before EC2 free tier expires), a formal review must be conducted.
- Review must produce a documented decision: migrate to local, switch to Spot, or accept cost.
- This review is a phase gate event and must be recorded in the audit log.
