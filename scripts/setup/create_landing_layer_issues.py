"""
Create new GitHub issues for Landing layer gaps and fix known problems.
"""
import subprocess

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "biteberry/project-intelligent"

def gh(*args):
    result = subprocess.run([GH] + list(args), capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("STDERR:", result.stderr.strip())
    return result.stdout.strip()

issues = [
    {
        "title": "[TASK] Enable S3 Object Lock COMPLIANCE mode on Landing bucket",
        "body": """## Parent Story
Part of #45

## Description
The Landing layer bucket must use S3 Object Lock in COMPLIANCE mode to enforce write-once,
read-many semantics. This is different from GOVERNANCE mode (which can be overridden by root)
and different from versioning (which does not prevent deletion).

COMPLIANCE mode ensures raw ingested files cannot be deleted or modified by ANY principal,
including root, for the full retention period. This satisfies audit and reprocessing requirements
documented in `docs/architecture/03_data_architecture_medallion.md`.

**Steps:**
- Enable Object Lock on `project-intelligent-landing-<acct>` bucket
- Set default retention: COMPLIANCE mode, 365 days
- Verify with: `aws s3api get-object-lock-configuration --bucket project-intelligent-landing-<acct>`
- Update IAM policy to ensure no DeleteObject on Landing bucket

**Note:** Object Lock must be enabled at bucket creation time. If the bucket was created without
Object Lock, it must be recreated. Confirm before proceeding.

## Acceptance Criteria
- [ ] Object Lock enabled on Landing bucket in COMPLIANCE mode
- [ ] Default retention period set to 365 days
- [ ] `aws s3api get-object-lock-configuration` confirms COMPLIANCE mode
- [ ] IAM policy explicitly denies `s3:DeleteObject` on Landing bucket for all principals
- [ ] Fetcher Lambda/EC2 role can PutObject (new objects only), not overwrite

## Files to Create or Modify
- `infra/iam/ec2-instance-policy.json` (add explicit Deny DeleteObject on Landing)
- `infra/s3/landing-object-lock.md` (document the Object Lock configuration)

## Test Approach
Attempt to delete a test object from Landing bucket — must be denied for all IAM identities.
""",
        "labels": ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "milestone": "M1: Phase 1.1 - Environment Provisioning",
    },
    {
        "title": "[TASK] Fix Landing S3 lifecycle: Glacier after 90 days, retain 1 year",
        "body": """## Parent Story
Part of #45

## Background
Issue #65 (now closed) configured the Landing lifecycle to **expire objects after 30 days**.
This conflicts with the updated architecture in `docs/architecture/03_data_architecture_medallion.md`
which requires:
- Transition to S3 Glacier after **90 days** (not expiry — data must be retained for reprocessing)
- Minimum **1-year retention** for audit compliance

## What needs to be done
Update the Landing bucket lifecycle rule:
- Remove the existing 30-day expiry rule
- Add a transition rule: objects → S3 Glacier Flexible Retrieval after 90 days
- Add a minimum retention policy: objects retained for minimum 365 days before any expiry

**Note:** If Object Lock COMPLIANCE is enabled (see sibling task), expiry rules are governed by
the Object Lock retention period, not lifecycle. Confirm interaction before applying.

## Acceptance Criteria
- [ ] 30-day expiry rule removed from Landing bucket lifecycle configuration
- [ ] Glacier transition rule set: 90 days after object creation
- [ ] Minimum 365-day retention confirmed (via Object Lock or lifecycle expiry)
- [ ] `aws s3api get-bucket-lifecycle-configuration` confirms updated rule
- [ ] S3 storage cost estimate documented (Glacier vs S3 Standard pricing delta)

## Files to Create or Modify
- `infra/s3/landing-lifecycle.json` (updated lifecycle rule)
- `docs/architecture/03_data_architecture_medallion.md` is already updated

## Test Approach
Upload a test object, verify transition rule is applied by checking object storage class after 90 days
(or simulate via `aws s3api put-object` with backdated metadata).
""",
        "labels": ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "milestone": "M1: Phase 1.1 - Environment Provisioning",
    },
    {
        "title": "[STORY] G0 Quality Gate: Landing → Bronze ingestion validator",
        "body": """## User Story
As a data platform owner, I need a G0 quality gate that validates all raw data in the Landing
layer before promoting it to Bronze, so that Bronze remains a clean, trusted, immutable snapshot
with no corrupt or invalid records.

## Parent Feature
Part of #1 (FEATURE-001 Architecture Phase Closure) and relates to FEATURE-003 to FEATURE-010
(all ingestion features)

## Architecture Reference
- `docs/architecture/03_data_architecture_medallion.md` — G0 gate definition
- `docs/architecture/08_data_ingestion_architecture.md` — Ingestion flow overview

## What the G0 gate must do
1. Read raw files from `s3://project-intelligent-landing/source=<src>/date=<date>/`
2. Validate mandatory fields: symbol, date, open, high, low, close, volume
3. Reject negative prices or volumes
4. Reject records where high < low
5. Reject future-dated records (> today + 1 business day)
6. Reject symbols not in the approved universe list
7. Reject batches where missing-field ratio > 5%
8. Deduplicate on symbol + date combination
9. Write passing records to Bronze as Parquet
10. Write failing records to `s3://project-intelligent-landing/quarantine/date=<date>/`
11. Log every run to DynamoDB audit table (run_id, job_id, pass_count, reject_count, timestamp)

## Acceptance Criteria
- [ ] All child tasks closed
- [ ] G0 gate rejects 100% of records with missing mandatory fields
- [ ] G0 gate rejects entire batch if missing-field ratio > 5%
- [ ] Rejected records appear in quarantine prefix, never in Bronze
- [ ] Every run logged in DynamoDB audit table

## Child Tasks
- [ ] Implement G0 gate validation logic (Python)
- [ ] Implement quarantine prefix writer for rejected records
- [ ] Integrate G0 gate into J02 daily ingestion job
- [ ] Write unit tests for all G0 validation rules
""",
        "labels": ["type:story", "phase:0-setup", "comp:infra", "priority:critical"],
        "milestone": "M1: Phase 1.1 - Environment Provisioning",
    },
    {
        "title": "[TASK] Implement G0 gate validation logic (Landing → Bronze)",
        "body": """## Parent Story
Part of G0 Quality Gate story (see parent)

## Description
Write the Python module that implements the G0 quality gate. This is the core validator
that runs between the Landing layer and Bronze for every ingestion job.

## File to create
`pipeline/ingestion/g0_gate.py`

## Validation rules to implement
```python
# 1. Mandatory fields check
MANDATORY_FIELDS = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']

# 2. Reject negative prices / volumes
assert open > 0, high > 0, low > 0, close > 0, volume >= 0

# 3. Reject high < low
assert high >= low

# 4. Reject future dates (today + 1 business day tolerance)

# 5. Reject symbols not in universe list

# 6. Missing field ratio <= 5% per batch

# 7. Deduplicate on symbol + date
```

## Quarantine handling
- Rejected records → `s3://project-intelligent-landing/quarantine/date=<YYYY-MM-DD>/source=<src>/`
- Log rejection reason per record

## DynamoDB audit log entry
```json
{
  "run_id": "<uuid>",
  "job_id": "G0",
  "source": "<source_name>",
  "date": "<YYYY-MM-DD>",
  "input_count": 100,
  "pass_count": 98,
  "reject_count": 2,
  "quarantine_path": "s3://...quarantine/...",
  "status": "PASS|FAIL",
  "timestamp": "<ISO8601>"
}
```

## Acceptance Criteria
- [ ] `pipeline/ingestion/g0_gate.py` created
- [ ] All 7 validation rules implemented
- [ ] Quarantine writer implemented
- [ ] DynamoDB audit record written on every run
- [ ] `python -m pytest tests/test_g0_gate.py` passes

## Test Approach
Unit tests in `tests/test_g0_gate.py` covering all edge cases.
""",
        "labels": ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "milestone": "M1: Phase 1.1 - Environment Provisioning",
    },
    {
        "title": "[TASK] Write unit tests for all G0 gate validation rules",
        "body": """## Parent Story
Part of G0 Quality Gate story (see parent)

## Description
Write a comprehensive pytest test suite for the G0 quality gate module
(`pipeline/ingestion/g0_gate.py`). Every validation rule must have at least one
positive test (should pass) and one negative test (should reject).

## File to create
`tests/test_g0_gate.py`

## Test cases required
| Rule | Pass case | Fail case |
|---|---|---|
| Mandatory fields | All fields present | Missing `volume` |
| Negative prices | All prices > 0 | `close = -1.5` |
| High < low | high=105, low=100 | high=99, low=100 |
| Future date | today's date | tomorrow + 2 days |
| Symbol not in universe | valid symbol | unknown symbol |
| Missing field ratio | 2% nulls | 6% nulls |
| Deduplication | unique symbol+date | duplicate symbol+date |
| Quarantine write | N/A | verify quarantine S3 path written |
| DynamoDB audit log | N/A | verify audit record structure |

## Acceptance Criteria
- [ ] `tests/test_g0_gate.py` created with all 9 test groups
- [ ] `python -m pytest tests/test_g0_gate.py -v` passes with 0 failures
- [ ] Test coverage for `g0_gate.py` >= 90% (verified via `pytest --cov`)

## Test Approach
Use pytest with mocked S3 (moto) and mocked DynamoDB (moto) for isolation.
""",
        "labels": ["type:task", "phase:0-setup", "comp:infra", "priority:high"],
        "milestone": "M1: Phase 1.1 - Environment Provisioning",
    },
]

print("=== Creating new GitHub issues for Landing layer gaps ===\n")
created = []
for issue in issues:
    label_args = []
    for label in issue["labels"]:
        label_args += ["--label", label]
    
    output = gh(
        "issue", "create",
        "--repo", REPO,
        "--title", issue["title"],
        "--body", issue["body"],
        "--milestone", issue["milestone"],
        *label_args
    )
    created.append((issue["title"], output))
    print(f"Created: {issue['title']}")
    print(f"  URL: {output}\n")

print("\n=== Done. Issues created: ===")
for title, url in created:
    print(f"  {url} — {title}")
