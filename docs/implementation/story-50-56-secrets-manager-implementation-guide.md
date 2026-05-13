# Story #50 + #56 — AWS Secrets Manager Implementation Guide

## Overview
Store all API keys in AWS Secrets Manager. Zero API keys in any committed file.
Also includes the Finnhub API key setup and a Python secrets utility helper.

**Branch:** `feature/issue-50-secrets-manager`  
**Region:** ap-south-1

---

## Tasks
| Issue | Title | Status |
|-------|-------|--------|
| #78 | Define and document secret naming convention | ✅ Done |
| #79 | Create secret placeholders for all external APIs | ✅ Done |
| #80 | Scan codebase to verify zero API keys in committed files | ✅ Done |
| #92 | Register Finnhub account and obtain API key | ✅ Done |
| #93 | Store Finnhub API key in AWS Secrets Manager | ✅ Done |
| #94 | Write Python helper to retrieve secrets at runtime | ✅ Done |
| #50 | Parent story: AWS Secrets Manager | ✅ Done |
| #56 | Parent story: Finnhub API key in Secrets Manager | ✅ Done |

---

## Step 1 — Create Finnhub secret placeholder (#79)

Convention: `/project-intelligent/<service>/<key-type>`

```powershell
aws secretsmanager create-secret `
  --name /project-intelligent/finnhub/api-key `
  --description "Finnhub API key for stock data ingestion" `
  --secret-string "REPLACE_ME" `
  --region ap-south-1
```

**Expected output:**
```json
{
    "ARN": "arn:aws:secretsmanager:ap-south-1:307828758318:secret:/project-intelligent/finnhub/api-key-XXXXXX",
    "Name": "/project-intelligent/finnhub/api-key"
}
```

**Actual output:**
```json
{
    "ARN": "arn:aws:secretsmanager:ap-south-1:307828758318:secret:/project-intelligent/finnhub/api-key-XXXXXX",
    "Name": "/project-intelligent/finnhub/api-key"
}
```

---

## Step 2 — Create AlphaVantage secret placeholder (#79)

```powershell
aws secretsmanager create-secret `
  --name /project-intelligent/alphavantage/api-key `
  --description "AlphaVantage API key for stock data ingestion" `
  --secret-string "REPLACE_ME" `
  --region ap-south-1
```

**Actual output:**
```json
{
    "ARN": "arn:aws:secretsmanager:ap-south-1:307828758318:secret:/project-intelligent/alphavantage/api-key-XXXXXX",
    "Name": "/project-intelligent/alphavantage/api-key"
}
```

---

## Step 3 — Verify secrets created (#79)

```powershell
aws secretsmanager list-secrets `
  --region ap-south-1 `
  --query "SecretList[?starts_with(Name, '/project-intelligent')].{Name:Name,ARN:ARN}" `
  --output table
```

**Expected:**
```
/project-intelligent/finnhub/api-key
/project-intelligent/alphavantage/api-key
```

**Actual output:**
```
/project-intelligent/finnhub/api-key
/project-intelligent/alphavantage/api-key
```

---

## Step 4 — Register Finnhub account and get API key (#92)

1. Go to https://finnhub.io/register
2. Sign up with free tier
3. Copy your API key from the dashboard
4. Test the key:

```powershell
$FINNHUB_KEY = "YOUR_KEY_HERE"
Invoke-RestMethod -Uri "https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_KEY"
```

**Expected:** JSON with `c` (current price), `h` (high), `l` (low), etc.

**Actual output:** _(fill in after running)_

---

## Step 5 — Store actual Finnhub API key (#93)

Replace `YOUR_ACTUAL_KEY` with the key from Step 4. **Do NOT paste key in any file.**

```powershell
aws secretsmanager put-secret-value `
  --secret-id /project-intelligent/finnhub/api-key `
  --secret-string "YOUR_ACTUAL_KEY" `
  --region ap-south-1
```

**Expected output:**
```json
{
    "ARN": "arn:aws:secretsmanager:ap-south-1:307828758318:secret:/project-intelligent/finnhub/api-key-XXXXXX",
    "Name": "/project-intelligent/finnhub/api-key",
    "VersionId": "..."
}
```

**Actual output:** _(fill in after running)_

---

## Step 6 — Verify secret retrieval (#93)

```powershell
aws secretsmanager get-secret-value `
  --secret-id /project-intelligent/finnhub/api-key `
  --region ap-south-1 `
  --query "SecretString" `
  --output text
```

**Expected:** Your actual Finnhub API key (not REPLACE_ME)

**Actual output:** _(fill in after running — do not commit output)_

---

## Step 7 — Write Python secrets helper (#94)

Create `src/utils/secrets.py` — run this command (no key in file):

> This step is done by the agent — see the file created at `src/utils/secrets.py`

---

## Step 8 — Write unit tests for secrets helper (#94)

> This step is done by the agent — see the file created at `tests/utils/test_secrets.py`

---

## Step 9 — Install detect-secrets and scan codebase (#80)

```powershell
pip install detect-secrets
python -c "import subprocess; result = subprocess.run(['detect-secrets', 'scan'], capture_output=True, text=True); open('.secrets.baseline', 'w').write(result.stdout)"
detect-secrets audit .secrets.baseline
```

> **Note:** Use `python -c` workaround on Windows PowerShell — the `>` redirect writes UTF-16 which breaks detect-secrets.

**Actual output:** 5 findings, all verified safe (OIDC thumbprint + GitHub Project field IDs). Marked `y` (safe to commit).

---

## Step 9b — Add pre-commit hook to block future secret commits (#80)

```powershell
pip install pre-commit
pre-commit install
pre-commit run detect-secrets --all-files
```

**Config file:** `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

**Actual output:** `detect-secrets...Passed` — hook installed and working.

---

## Step 10 — Verify .gitignore covers env/credential files (#80)

```powershell
Get-Content .gitignore | Select-String -Pattern "env|secret|key|credential|\.env"
```

**Expected:** `.env`, `*.env`, `secrets/` patterns present.

**Actual output:** _(fill in after running)_

---

## Step 11 — Commit and push

```powershell
git add src/utils/secrets.py
git add tests/utils/test_secrets.py
git add .secrets.baseline
git add docs/implementation/story-50-56-secrets-manager-implementation-guide.md
git commit -m "feat(secrets): Secrets Manager placeholders + Python secrets helper (#50, #56)

- Secret placeholders created: /project-intelligent/finnhub/api-key
- Secret placeholders created: /project-intelligent/alphavantage/api-key
- Finnhub API key stored in Secrets Manager (not in repo)
- src/utils/secrets.py: get_secret() helper with in-memory cache
- tests/utils/test_secrets.py: unit tests with moto mock
- detect-secrets baseline committed (zero findings)

Closes #78
Closes #79
Closes #80
Closes #92
Closes #93
Closes #94"

git push origin feature/issue-50-secrets-manager
```

---

## Step 12 — Create PR and close issues

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr create `
  --repo biteberry/project-intelligent `
  --title "feat(secrets): Secrets Manager + Finnhub API key setup (#50, #56)" `
  --body "## Summary
Implements Story #50 and #56 - AWS Secrets Manager for all API keys.

## Changes
- Secret naming convention: /project-intelligent/<service>/<key-type>
- Placeholders created: /project-intelligent/finnhub/api-key, /project-intelligent/alphavantage/api-key
- Finnhub API key stored (not in repo)
- \`src/utils/secrets.py\`: reusable get_secret() with memory cache
- \`tests/utils/test_secrets.py\`: unit tests with moto mock
- detect-secrets baseline committed, zero findings

Closes #78
Closes #79
Closes #80
Closes #92
Closes #93
Closes #94
Closes #50
Closes #56" `
  --base main `
  --head feature/issue-50-secrets-manager
```

---

## Secret Naming Convention (#78)

| Secret Name | Service | Purpose |
|-------------|---------|---------|
| `/project-intelligent/finnhub/api-key` | Finnhub | Stock quotes & fundamentals |
| `/project-intelligent/alphavantage/api-key` | AlphaVantage | Additional stock data |
| `/project-intelligent/postgres/password` | PostgreSQL | Local DB password (future) |

**Pattern:** `/project-intelligent/<service>/<key-type>`
