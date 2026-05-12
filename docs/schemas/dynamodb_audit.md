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
- Table uses on-demand (PAY_PER_REQUEST) billing.
- All attribute names and types are documented for future reference.
