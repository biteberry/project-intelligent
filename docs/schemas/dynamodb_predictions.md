# DynamoDB Table Schema — Predictions

## Table Name
`project-intelligent-predictions`

## Primary Key
- **Partition Key (PK):** `symbol#date` (e.g. `RELIANCE#2026-05-07`)
- **Sort Key (SK):** `horizon#model_version` (e.g. `swing#v1.2`)

## Attributes
| Name                | Type    | Example                | Description                                  |
|---------------------|---------|------------------------|----------------------------------------------|
| predicted_direction | String  | UP                     | Model output: UP, DOWN, or FLAT              |
| confidence_score    | Number  | 0.87                   | Model confidence (0.0–1.0)                   |
| features_hash       | String  | 9f8a7c...              | Hash of input features for traceability      |
| ttl                 | Number  | 1788888888             | Unix epoch seconds for TTL (90-day expiry)   |

## Example Item
```json
{
  "symbol#date": "RELIANCE#2026-05-07",
  "horizon#model_version": "swing#v1.2",
  "predicted_direction": "UP",
  "confidence_score": 0.87,
  "features_hash": "9f8a7c...",
  "ttl": 1788888888
}
```

## GSI Design (if needed)
- **No GSI required for initial use case.**
- If you need to query by model_version or horizon across all symbols, consider:
  - GSI1: PK = `horizon#model_version`, SK = `symbol#date`

---

# DynamoDB Table Schema — Audit

## Table Name
`project-intelligent-audit`

## Primary Key
- **Partition Key (PK):** `job_date` (e.g. `2026-05-07`)
- **Sort Key (SK):** `job_id` (e.g. `daily-swing-20260507T2100Z`)

## Attributes
| Name              | Type    | Example                  | Description                       |
|-------------------|---------|--------------------------|-----------------------------------|
| records_processed | Number  | 100000                   | Number of records processed       |
| error_message     | String  | "Timeout"                | Error message if job failed       |
| duration_seconds  | Number  | 120                      | Job duration in seconds           |

## Example Item
```json
{
  "job_date": "2026-05-07",
  "job_id": "daily-swing-20260507T2100Z",
  "records_processed": 100000,
  "error_message": "",
  "duration_seconds": 120
}
```

## GSI Design (if needed)
- **No GSI required for initial use case.**
- If you need to query by job_id prefix, consider:
  - GSI1: PK = `job_id`, SK = `job_date`

---

# Notes
- Both tables use on-demand (PAY_PER_REQUEST) billing.
- TTL is enabled on the predictions table for 90-day retention.
- All attribute names and types are documented for future reference.
