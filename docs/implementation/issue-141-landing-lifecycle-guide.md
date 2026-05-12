# Issue #141 — Fix Landing S3 Lifecycle: Glacier after 90 days, Retain 1 Year

**Repo:** biteberry/project-intelligent  
**Issue:** [#141](https://github.com/biteberry/project-intelligent/issues/141)  
**Milestone:** M1: Phase 1.1 — Environment Provisioning  
**Priority:** Critical  

---

## What You Will Learn

- What S3 Lifecycle rules are and how they reduce storage cost
- The difference between lifecycle **Transition** and **Expiration**
- How Object Lock COMPLIANCE interacts with lifecycle rules
- How to update a lifecycle configuration and apply it to AWS

---

## Background — Key Concepts

### What is an S3 Lifecycle Rule?
A set of automated instructions that tell S3 what to do with objects as they age.
Two main actions:
- **Transition** — move objects to a cheaper storage class after N days
- **Expiration** — permanently delete objects after N days

### S3 Storage Classes (cheapest to most expensive for cold data)

| Class | Use Case | Cost/GB/month |
|---|---|---|
| S3 Standard | Frequently accessed | $0.023 |
| S3 Standard-IA | Infrequently accessed | $0.0125 |
| **S3 Glacier Flexible Retrieval** | Archive, rarely accessed | **$0.004** |

### Why Glacier for Landing?
Raw ingested files land in the Landing bucket and are immediately processed into
Bronze/Silver. After processing, they are rarely accessed again — but they must
be retained for 1 year for audit and reprocessing. Glacier is ~6x cheaper than
S3 Standard for this cold storage.

### Critical: How Object Lock Interacts with Lifecycle

| Lifecycle Action | With Object Lock COMPLIANCE | Result |
|---|---|---|
| Transition (Standard → Glacier) | ✅ Allowed | Objects move to Glacier after 90 days |
| Expiration (delete after N days) | ❌ Blocked until retention expires | S3 ignores expiry rule until 365-day lock expires |

**Conclusion:** We set the Glacier transition in the lifecycle rule. We do NOT set
an expiry rule — Object Lock already handles the 365-day minimum retention.

### What is currently wrong in `landing-lifecycle.json`?
The existing rule `ExpireRawFilesAfter30Days` **deletes** objects after 30 days.
This conflicts with:
- The 365-day COMPLIANCE lock (Object Lock would block it anyway)
- Architecture requirement to retain 1 year minimum
- Architecture requirement to transition to Glacier at 90 days (not delete)

---

## Prerequisites

Set your variables in PowerShell (run these in every new terminal session):

```powershell
$accountId = "307828758318"
$region = "ap-south-1"
$landingBucket = "project-intelligent-landing-$accountId"
```

Check the current lifecycle rule on the bucket:

```powershell
aws s3api get-bucket-lifecycle-configuration --bucket $landingBucket
```

You should see the old 30-day expiry rule. That confirms what needs to be replaced.

---

## Step 1 — Update `landing-lifecycle.json`

Open the file `infra/s3/landing-lifecycle.json` and **replace its entire contents** with:

```json
{
    "Rules": [
        {
            "ID": "GlacierTransitionAfter90Days",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
```

**What changed:**

| Before | After |
|---|---|
| Rule ID: `ExpireRawFilesAfter30Days` | Rule ID: `GlacierTransitionAfter90Days` |
| Action: `Expiration` after 30 days (delete) | Action: `Transitions` after 90 days (move to Glacier) |
| No retention guarantee | Retention enforced by Object Lock (365 days) |

> **Why no Expiration rule?** Object Lock COMPLIANCE already enforces 365-day retention.
> Adding a conflicting lifecycle expiry would either be ignored by S3 or cause confusion.
> One source of truth: Object Lock owns the retention period.

---

## Step 2 — Apply the Updated Lifecycle to AWS

Navigate to the infra/s3 folder:

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT\infra\s3
```

Apply the updated lifecycle configuration:

```powershell
aws s3api put-bucket-lifecycle-configuration `
  --bucket $landingBucket `
  --lifecycle-configuration file://landing-lifecycle.json
```

No output = success.

---

## Step 3 — Verify the Updated Lifecycle

```powershell
aws s3api get-bucket-lifecycle-configuration --bucket $landingBucket
```

**Expected output:**

```json
{
    "Rules": [
        {
            "ID": "GlacierTransitionAfter90Days",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
```

Confirm:
- `ExpireRawFilesAfter30Days` is **gone**
- `GlacierTransitionAfter90Days` is **present**
- `StorageClass` is `GLACIER`
- `Days` is `90`

---

## Step 4 — Document the Storage Cost Estimate

The issue requires a cost estimate to be documented. Here is the calculation:

### Phase 0 (now) — test objects only
- Data volume: < 1 KB
- Cost: **$0.00** (within Free Tier and too small to meter)

### Phase 1 onwards — real market data estimate

Assume ~500 MB of raw OHLCV data per month ingested.

| Period | Storage Class | Volume | Cost/month |
|---|---|---|---|
| Day 0–90 | S3 Standard | 500 MB | ~$0.012 |
| Day 90+ | S3 Glacier | 500 MB | ~$0.002 |
| **Saving vs keeping in Standard** | | | **~$0.010/month** |

At scale (e.g., 10 GB/month ingestion after 1 year):

| Scenario | Cost/month |
|---|---|
| All in S3 Standard forever | ~$0.23 |
| Glacier after 90 days | ~$0.04 |
| **Saving** | **~$0.19/month** |

> Glacier retrieval cost: $0 (Bulk retrieval, 5–12 hours). For reprocessing jobs
> that are not time-sensitive, Bulk retrieval is free and sufficient.

---

## Step 5 — Commit and Push

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT

git add infra/s3/landing-lifecycle.json
git commit -m "fix(issue-141): update landing lifecycle - remove 30-day expiry, add Glacier transition at 90 days"
git push
```

---

## Step 6 — Tick Acceptance Criteria and Close Issue

After all steps are verified, run:

```powershell
gh issue comment 141 --repo biteberry/project-intelligent --body "All acceptance criteria completed:

- [x] 30-day expiry rule removed from Landing bucket lifecycle configuration
- [x] Glacier transition rule set: 90 days after object creation
- [x] Minimum 365-day retention confirmed via Object Lock COMPLIANCE (governs deletion; lifecycle expiry intentionally omitted as it conflicts with Object Lock)
- [x] aws s3api get-bucket-lifecycle-configuration confirms GlacierTransitionAfter90Days rule
- [x] S3 cost estimate documented in implementation guide: ~$0.002/GB/month in Glacier vs $0.023/GB/month in Standard (~6x saving)

Note: Lifecycle expiry rule deliberately excluded. Object Lock COMPLIANCE retention (365 days) is the authoritative retention control. A conflicting lifecycle expiry would be blocked by Object Lock anyway."

gh issue close 141 --repo biteberry/project-intelligent
```

---

## Checklist — Acceptance Criteria

- [ ] 30-day expiry rule removed from Landing bucket lifecycle configuration
- [ ] Glacier transition rule set: 90 days after object creation
- [ ] Minimum 365-day retention confirmed (via Object Lock)
- [ ] `aws s3api get-bucket-lifecycle-configuration` confirms updated rule
- [ ] S3 storage cost estimate documented

---

## Summary of Files Changed

| File | Action |
|---|---|
| `infra/s3/landing-lifecycle.json` | Replace 30-day expiry rule with 90-day Glacier transition |

---

## Key Concepts Recap

| Term | Meaning |
|---|---|
| Lifecycle Transition | Automatically move objects to a cheaper storage class after N days |
| Lifecycle Expiration | Automatically delete objects after N days |
| S3 Glacier | Cold archive storage — 6x cheaper than S3 Standard, retrieval takes hours |
| Object Lock + Lifecycle | Lock owns deletion; lifecycle owns storage class transitions |
| Bulk Retrieval | Free Glacier retrieval (5–12 hours) — sufficient for reprocessing |
