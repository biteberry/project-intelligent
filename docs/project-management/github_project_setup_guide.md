# GitHub Project Management Setup Guide
## PROJECT INTELLIGENT — JIRA-Equivalent Workflow on GitHub
**Date:** 2026-05-07
**Status:** Step-by-step setup reference

---

## Overview — JIRA to GitHub Mapping

| JIRA Concept | GitHub Equivalent | Notes |
|---|---|---|
| **Project** | GitHub Repository | One repo = one project |
| **Board / Backlog** | GitHub Project (v2) | Kanban + table view |
| **Phase** | GitHub Milestone (Phase label group) | e.g., "Phase 0", "Phase 1" |
| **Milestone** | GitHub Milestone | e.g., "M2: Data Ingestion Layer" |
| **Epic / Feature** | GitHub Issue (type: `feature`) | Parent issue — contains Stories |
| **Story** | GitHub Issue (type: `story`) | Linked to parent Feature via body |
| **Task** | GitHub Issue (type: `task`) | Linked to parent Story via body |
| **Bug** | GitHub Issue (type: `bug`) | Linked to Story or Task |
| **Label** | GitHub Label | Multi-axis tagging |
| **Sprint** | GitHub Milestone | Time-boxed iteration |
| **Acceptance Criteria** | Issue body checklist `- [ ]` | Inline with each issue |
| **Priority** | GitHub Label (priority:xxx) | Critical / High / Medium / Low |

---

## Part 1 — Create the GitHub Repository

### Step 1.1 — Create Repository

1. Go to [github.com](https://github.com) → sign in
2. Click **+** (top right) → **New repository**
3. Fill in:
   - **Repository name:** `project-intelligent`
   - **Description:** `India-first NSE/BSE swing trade signal platform powered by ML`
   - **Visibility:** `Private` (your personal trading data — keep it private)
   - **Initialize repository:** ✅ (tick this)
   - **Add a README:** ✅
   - **Add .gitignore:** choose `Python`
   - **License:** None (personal project)
4. Click **Create repository**

### Step 1.2 — Clone to Local Machine

Open PowerShell in your workspace folder:

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS
git clone https://github.com/<YOUR_GITHUB_USERNAME>/project-intelligent.git PROJECT_INTELLIGENT_GIT
```

> **Note:** The existing `PROJECT_INTELLIGENT` folder has your architecture docs. In Step 3.2 we will push those docs into this new repo.

### Step 1.3 — Initialize the Existing Folder as a Git Repo

If you prefer to work directly in the existing folder:

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT
git init
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/project-intelligent.git
git add .
git commit -m "chore: initial commit — architecture docs and PRD"
git branch -M main
git push -u origin main
```

---

## Part 2 — Set Up GitHub Labels

Labels are the backbone of the entire hierarchy. Create all labels before creating any issue.

### Step 2.1 — Open Label Manager

Go to your repo → **Issues** → **Labels** → **New label**

### Step 2.2 — Complete Label Set

Create every label below. Colors are chosen to visually separate label categories at a glance.

#### Type Labels (what kind of item is this?)

| Label Name | Color | Purpose |
|---|---|---|
| `type:feature` | `#0052CC` (dark blue) | Parent epic — groups stories |
| `type:story` | `#0075CA` (medium blue) | User story — groups tasks |
| `type:task` | `#BFD4F2` (light blue) | Smallest unit of work |
| `type:bug` | `#D73A4A` (red) | Defect found during testing |
| `type:spike` | `#E4E669` (yellow) | Research / investigation |
| `type:doc` | `#EDEDED` (grey) | Documentation only |
| `type:infra` | `#006B75` (teal) | AWS / environment setup |

#### Phase Labels (which phase does this belong to?)

| Label Name | Color | Purpose |
|---|---|---|
| `phase:0-setup` | `#F9D0C4` (light pink) | Architecture, PRD, environment provisioning |
| `phase:1-core` | `#FBCA04` (yellow) | Core pipeline implementation (all jobs) |
| `phase:2-enhance` | `#0E8A16` (green) | Phase 2 enhancements (FII/DII, BSE, etc.) |

#### Component Labels (which part of the system?)

| Label Name | Color | Purpose |
|---|---|---|
| `comp:ingestion` | `#B60205` (dark red) | J01-J03 — data ingestion |
| `comp:feature-eng` | `#D93F0B` (orange) | J04 — feature engineering |
| `comp:ml-pipeline` | `#E99695` (salmon) | J06 — model training |
| `comp:inference` | `#F9D0C4` (peach) | J07-J08 — prediction + signals |
| `comp:universe` | `#5319E7` (purple) | J01 — universe selection + scanner |
| `comp:monitoring` | `#1D76DB` (blue) | J09 — observability + alerts |
| `comp:infra` | `#006B75` (teal) | AWS, GitHub Actions, local setup |
| `comp:data-store` | `#0052CC` (navy) | DynamoDB, S3, PostgreSQL |
| `comp:docs` | `#EDEDED` (grey) | Architecture docs, PRD, ADRs |

#### Priority Labels

| Label Name | Color | Purpose |
|---|---|---|
| `priority:critical` | `#B60205` (dark red) | Blocks all other work |
| `priority:high` | `#D93F0B` (orange) | Must complete this milestone |
| `priority:medium` | `#FBCA04` (yellow) | Should complete this milestone |
| `priority:low` | `#C2E0C6` (light green) | Nice to have |

#### State Labels (special conditions)

| Label Name | Color | Purpose |
|---|---|---|
| `blocked` | `#B60205` (dark red) | Cannot proceed — waiting on something |
| `needs-review` | `#FBCA04` (yellow) | Needs platform owner decision |
| `deferred` | `#EDEDED` (grey) | Explicitly moved to a later phase |
| `wontfix` | `#EDEDED` (grey) | Decided not to implement |

> **Tip:** Use `<hex-color>` in the color field when creating labels. GitHub accepts hex codes directly.

---

## Part 3 — Set Up GitHub Milestones

Milestones are your time-boxed phases. Every issue belongs to exactly one milestone.

### Step 3.1 — Open Milestone Manager

Go to your repo → **Issues** → **Milestones** → **New milestone**

### Step 3.2 — Create All Milestones

| Milestone ID | Title | Purpose | Due Date Suggestion |
|---|---|---|---|
| M0 | `Phase 0 — Architecture & Sign-Off` | Close architecture phase, PRD sign-off, Phase 0 gate | 2026-05-15 |
| M1 | `Phase 1.1 — Environment Provisioning` | AWS infra, GitHub repo, PostgreSQL schema, secrets | 2026-05-31 |
| M2 | `Phase 1.2 — Data Ingestion Layer` | J01 + J03 — OHLCV, fundamentals, delivery %, macro | 2026-06-30 |
| M3 | `Phase 1.3 — Feature Engineering Layer` | J04 — all 10 feature groups in Gold layer | 2026-07-31 |
| M4 | `Phase 1.4 — ML Training Pipeline` | J06 — model training, walk-forward validation, promotion gate | 2026-08-31 |
| M5 | `Phase 1.5 — Inference & Signal Generation` | J07 + J08 — predictions, serving gates, trade signals | 2026-09-30 |
| M6 | `Phase 1.6 — Monitoring & Operations` | J09 — CloudWatch, SNS alerts, audit trail, daily ops routine | 2026-10-31 |
| M7 | `Phase 1.7 — Acceptance Testing & Go-Live` | End-to-end validation, Definition of Done checklist | 2026-11-30 |

> **How to fill in a milestone:**
> - Title: exactly as shown above
> - Description: one sentence of purpose
> - Due date: your target date — can be adjusted any time

---

## Part 4 — Set Up GitHub Projects (Board)

GitHub Projects (v2) is your JIRA board. It gives you kanban, table view, custom fields, and filters.

### Step 4.1 — Create a Project

1. Go to your GitHub profile → **Projects** tab → **New project**
2. Choose **Board** template (kanban view)
3. Name: `PROJECT INTELLIGENT`
4. Click **Create project**

### Step 4.2 — Set Up Board Columns (Status)

Delete any default columns and create exactly these 6:

| Column | Meaning |
|---|---|
| `📋 Backlog` | Created but not scheduled for current milestone |
| `🔜 Ready` | Scheduled, all dependencies met, ready to start |
| `🔧 In Progress` | Actively being worked on |
| `👀 In Review` | Done — needs platform owner review or testing |
| `✅ Done` | Fully complete, acceptance criteria met |
| `🚫 Blocked` | Cannot progress — dependency or decision needed |

### Step 4.3 — Add Custom Fields

In the Project view → **+ field** (top right of table view) → add these fields:

| Field Name | Field Type | Values |
|---|---|---|
| `Phase` | Single select | Phase 0, Phase 1, Phase 2 |
| `Component` | Single select | Ingestion, Feature-Eng, ML-Pipeline, Inference, Universe, Monitoring, Infra, Data-Store, Docs |
| `Priority` | Single select | Critical, High, Medium, Low |
| `Milestone` | (auto — linked to GitHub Milestone) | — |
| `Story Points` | Number | Effort estimate (optional) |
| `Job` | Single select | J01, J02, J03, J04, J05, J06, J07, J08, J09, N/A |

### Step 4.4 — Link Your Repository to the Project

Inside the Project → **Settings** (⚙️) → **Linked repositories** → **Add repository** → select `project-intelligent`

---

## Part 5 — Issue Structure and Templates

### Step 5.1 — How Issues Link to Each Other

GitHub has no native parent-child hierarchy in free accounts. Use this convention in every issue body:

**In a Feature issue body:**
```markdown
## Child Stories
- [ ] #<story-issue-number> — Story title
- [ ] #<story-issue-number> — Story title
```

**In a Story issue body:**
```markdown
## Parent Feature
Part of #<feature-issue-number>

## Child Tasks
- [ ] #<task-issue-number> — Task title
- [ ] #<task-issue-number> — Task title
```

**In a Task issue body:**
```markdown
## Parent Story
Part of #<story-issue-number>

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2
```

When you reference `#123` in an issue body, GitHub auto-links and shows it in the referenced issue's timeline. This gives you bidirectional traceability.

### Step 5.2 — Create Issue Templates

Create three issue templates so every new issue is consistent.

Create the folder `.github/ISSUE_TEMPLATE/` in your repo and add three files:

#### File 1: `.github/ISSUE_TEMPLATE/feature.md`
```markdown
---
name: Feature
about: A feature (epic) that groups related stories
title: "[FEATURE] "
labels: type:feature
assignees: ''
---

## Description
<!-- What is this feature and why does it exist? Map to PRD FR-XX. -->

## PRD Reference
FR-XX

## Child Stories
<!-- List stories that belong to this feature. Update as issues are created. -->
- [ ] #<!-- issue number --> — story title

## Acceptance Criteria
- [ ] All child stories are closed
- [ ] Feature is tested end-to-end

## Notes
<!-- Architecture doc references, ADRs, design decisions -->
```

#### File 2: `.github/ISSUE_TEMPLATE/story.md`
```markdown
---
name: Story
about: A user story — a slice of a feature
title: "[STORY] "
labels: type:story
assignees: ''
---

## User Story
As a platform owner, I need _____ so that _____.

## Parent Feature
Part of #<!-- feature issue number -->

## Child Tasks
<!-- List tasks that implement this story. Update as issues are created. -->
- [ ] #<!-- issue number --> — task title

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2

## Notes
<!-- Links to architecture docs, schema references, config file names -->
```

#### File 3: `.github/ISSUE_TEMPLATE/task.md`
```markdown
---
name: Task
about: A concrete implementation task linked to a story
title: "[TASK] "
labels: type:task
assignees: ''
---

## What needs to be done
<!-- Clear, specific implementation description -->

## Parent Story
Part of #<!-- story issue number -->

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2
- [ ] unit test passes
- [ ] no errors in CloudWatch / local log

## Files Affected
<!-- List the source files, configs, or docs this task will create or modify -->

## Notes
```

---

## Part 6 — Full Issue Breakdown for PROJECT INTELLIGENT

This is the complete backlog, pre-broken down. Create these issues in order — Features first, then Stories, then Tasks. Fill in issue numbers as you create them.

---

### PHASE 0 — Architecture & Sign-Off (Milestone M0)

#### FEATURE-001: Architecture Phase Closure
Labels: `type:feature` `phase:0-setup` `comp:docs` `priority:critical`

| # | Type | Title |
|---|---|---|
| | Story | Phase 0 gate audit document |
| | Story | PRD v1.0 sign-off and approval |
| | Story | configs/position_sizing.yaml creation |
| | Story | Push all architecture docs to GitHub repo |

---

#### FEATURE-002: Environment Provisioning (Milestone M1)
Labels: `type:feature` `phase:0-setup` `comp:infra` `priority:critical`

| # | Type | Title |
|---|---|---|
| | Story | GitHub repository setup (this guide) |
| | Story | AWS IAM roles and least-privilege policies |
| | Story | AWS S3 bucket creation (Bronze/Silver/Gold/Artifacts) |
| | Story | AWS DynamoDB table creation (predictions + audit) |
| | Story | AWS EventBridge rules creation (daily + weekly triggers) |
| | Story | AWS Lambda dispatcher function creation |
| | Story | AWS CloudWatch alarms and SNS email alerts |
| | Story | AWS Secrets Manager — API key storage |
| | Story | AWS Glue Catalog setup for Iceberg |
| | Story | EC2 t2.micro setup and Python environment |
| | Story | Local PostgreSQL schema creation (ADR-003) |
| | Story | GitHub Actions CI setup (linting + test runner) |
| | Story | Finnhub API key registration and secrets storage |

---

### PHASE 1 — CORE PIPELINE (Milestones M2 through M7)

---

#### FEATURE-003: NSE OHLCV Daily Ingestion — J01 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:critical`
PRD: FR-01

| # | Type | Title |
|---|---|---|
| | Story | yfinance OHLCV fetcher with .NS suffix support |
| | Story | Bronze Parquet writer (partitioned by date/symbol) |
| | Story | Retry logic for failed symbol fetches (max 3) |
| | Story | Ticker suffix routing table (.NS / .BO / none) |
| | Story | DynamoDB job audit record write for J01 |
| | Story | SNS alert on J01 failure |

---

#### FEATURE-004: NSE Delivery Percentage Ingestion — J01 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:critical`
PRD: FR-02

| # | Type | Title |
|---|---|---|
| | Story | NSE bhav copy CSV downloader (daily URL pattern) |
| | Story | Delivery % Bronze writer (partitioned by date) |
| | Story | Join delivery % to OHLCV record by symbol + date |
| | Story | Alert when bhav copy unavailable (market holiday detection) |

---

#### FEATURE-005: Quarterly Fundamentals Ingestion — J02 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:high`
PRD: FR-03

| # | Type | Title |
|---|---|---|
| | Story | yfinance .info fundamentals fetcher |
| | Story | yfinance .financials / .balance_sheet / .cashflow fetcher |
| | Story | Bronze fundamentals Parquet writer (partitioned by quarter) |
| | Story | Staleness check — skip if last fetch < 30 days old |
| | Story | Institutional ownership fields extraction |

---

#### FEATURE-006: India Macro Data Ingestion — J03 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:high`
PRD: FR-04

| # | Type | Title |
|---|---|---|
| | Story | RBI repo rate fetcher (RBI public portal) |
| | Story | India 10Y / 2Y bond yield fetcher |
| | Story | India VIX daily fetcher (yfinance ^INDIAVIX) |
| | Story | Nifty 50 daily fetcher (yfinance ^NSEI) |
| | Story | Bronze macro Parquet writer (partitioned by date) |

---

#### FEATURE-007: Earnings Calendar Ingestion — J03 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:high`
PRD: FR-05

| # | Type | Title |
|---|---|---|
| | Story | NSE board meeting dates scraper (weekly) |
| | Story | Bronze earnings calendar Parquet writer |
| | Story | Silver enrichment: days_to_next_earnings, days_since_last_earnings |
| | Story | earnings_blackout_flag computation (±2 trading days) |

---

#### FEATURE-008: Corporate Actions Ingestion — J03 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:high`
PRD: FR-06

| # | Type | Title |
|---|---|---|
| | Story | yfinance .actions fetcher (bonus, split, dividend) |
| | Story | Bronze corporate actions Parquet writer |
| | Story | Silver enrichment: corporate_action_flag computation |
| | Story | Training exclusion gate: is_valid_row = false on ex-dates |

---

#### FEATURE-009: India Macro Event Calendar — J03 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:medium`
PRD: FR-07

| # | Type | Title |
|---|---|---|
| | Story | RBI MPC / Budget date static calendar file (annual update) |
| | Story | Silver enrichment: days_to_next_macro_event |
| | Story | macro_event_blackout_flag computation for rate-sensitive sectors |

---

#### FEATURE-010: NSE Circuit Band Ingestion — J03 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:high`
PRD: FR-13

| # | Type | Title |
|---|---|---|
| | Story | NSE circuit band reference file auto-fetcher (weekly) |
| | Story | Bronze circuit bands Parquet writer |
| | Story | Silver enrichment: upper_circuit_flag / lower_circuit_flag |

---

#### FEATURE-011: Silver Layer Transformation — J04 (Milestone M2)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:critical`
PRD: FR-01 through FR-07

| # | Type | Title |
|---|---|---|
| | Story | Bronze → Silver transformation job runner |
| | Story | Schema validation on Silver write |
| | Story | Iceberg table management for Silver (PyIceberg + Glue) |
| | Story | market_context field propagation on every Silver row |
| | Story | Data quality audit: null check, row count comparison |

---

#### FEATURE-012: Feature Engineering — Group 1-5 (Milestone M3)
Labels: `type:feature` `phase:1-core` `comp:feature-eng` `priority:critical`
PRD: FR-08

| # | Type | Title |
|---|---|---|
| | Story | Group 1: price return features (1d/5d/10d/21d/63d) |
| | Story | Group 2: rolling statistical features (mean/std/skew/kurt) |
| | Story | Group 3: technical indicators (RSI/MACD/ATR/BB/SMA) |
| | Story | Group 3: 52-week high/low proximity features |
| | Story | Group 3: RS vs Nifty 50 / S&P 500 (market_context-aware) |
| | Story | Group 3: support and resistance level features |
| | Story | Group 4: volume behaviour (OBV/AD/MFI/CLV/buy-pressure) |
| | Story | Group 4: NSE delivery % features (delivery_pct_ratio, spike flag) |
| | Story | Group 5: volatility features (realized vol, Garman-Klass) |

---

#### FEATURE-013: Feature Engineering — Group 6-10 (Milestone M3)
Labels: `type:feature` `phase:1-core` `comp:feature-eng` `priority:critical`
PRD: FR-08, FR-09

| # | Type | Title |
|---|---|---|
| | Story | Group 6: regime descriptor features (market_context-aware sources) |
| | Story | Group 7: calendar + earnings event features (all 8 fields) |
| | Story | Group 7: corporate action flag propagation from Silver |
| | Story | Group 7: macro event blackout flag propagation |
| | Story | Group 8: candlestick pattern features (5 patterns) |
| | Story | Group 9: institutional positioning features |
| | Story | Group 10: India regulatory risk features (NSE-only) |
| | Story | Gold layer writer (Iceberg + Glue Catalog) |
| | Story | Look-ahead bias audit script |

---

#### FEATURE-014: Market Regime Detection — J05 (Milestone M3)
Labels: `type:feature` `phase:1-core` `comp:feature-eng` `priority:high`
PRD: FR-09

| # | Type | Title |
|---|---|---|
| | Story | Regime classifier: bull_trend / bear_trend / sideways / high_vol |
| | Story | 3-day stability buffer (no single-day regime flip) |
| | Story | Regime label written to Gold and DynamoDB |
| | Story | market_context-aware index and VIX source routing |

---

#### FEATURE-015: ML Training Pipeline — J06 (Milestone M4)
Labels: `type:feature` `phase:1-core` `comp:ml-pipeline` `priority:critical`
PRD: FR-10, FR-11

| # | Type | Title |
|---|---|---|
| | Story | Gold snapshot loader with walk-forward splitter |
| | Story | Label computation: label_direction_1d |
| | Story | Corporate action row exclusion gate in training set |
| | Story | XGBoost / LightGBM baseline trainer |
| | Story | Walk-forward out-of-sample accuracy evaluation |
| | Story | Model metadata writer (feature_version, label_version, snapshot_id) |
| | Story | Model promotion gate: ≥2% accuracy improvement check |
| | Story | Model artifact writer to S3 |
| | Story | MLflow / SQLite experiment tracker |

---

#### FEATURE-016: Universe Selection and Scoring — J07 (Milestone M5)
Labels: `type:feature` `phase:1-core` `comp:universe` `priority:critical`
PRD: FR-15, FR-16, FR-17

| # | Type | Title |
|---|---|---|
| | Story | Fundamental scoring module (25% weight) |
| | Story | Technical scoring module (35% weight) |
| | Story | Quant scoring module (25% weight) |
| | Story | Sentiment scoring module (Finnhub, 5% weight) |
| | Story | Risk penalty module (10%) — manipulation score integration |
| | Story | Regime-conditional weight table application |
| | Story | Hard eligibility gate: liquidity, price floor, manipulation_risk_score |
| | Story | Cap-tier quota enforcement (large/mid/small) |
| | Story | Universe snapshot writer to S3 |
| | Story | Opportunity scanner (700-symbol daily scan) |
| | Story | manipulation_risk_score computation (6 components) |
| | Story | Scanner watchlist writer to S3 |

---

#### FEATURE-017: Daily Batch Inference — J08 (Milestone M5)
Labels: `type:feature` `phase:1-core` `comp:inference` `priority:critical`
PRD: FR-12, FR-13, FR-14

| # | Type | Title |
|---|---|---|
| | Story | Gold feature loader for active universe symbols |
| | Story | Model artifact loader from S3 |
| | Story | Prediction batch runner (1-day direction + confidence) |
| | Story | Serving gate: earnings blackout check (non-overridable) |
| | Story | Serving gate: circuit breaker check (NSE) |
| | Story | Serving gate: macro event blackout check |
| | Story | Serving gate: confidence floor check |
| | Story | Serving gate: model staleness check (>30 days) |
| | Story | Trade signal computation (entry, stop, target, position size) |
| | Story | DynamoDB prediction writer (all fields including suppression reason) |

---

#### FEATURE-018: Finnhub News Sentiment Ingestion (Milestone M5)
Labels: `type:feature` `phase:1-core` `comp:ingestion` `priority:medium`
PRD: FR-12 (sentiment input to scoring)

| # | Type | Title |
|---|---|---|
| | Story | Finnhub API client with 60-call/min rate limiter |
| | Story | bullishPercent / bearishPercent / buzz field extraction |
| | Story | Bronze sentiment Parquet writer (partitioned by date) |
| | Story | Silver sentiment enrichment per symbol |

---

#### FEATURE-019: Monitoring and Observability — J09 (Milestone M6)
Labels: `type:feature` `phase:1-core` `comp:monitoring` `priority:high`
PRD: FR-19, FR-20

| # | Type | Title |
|---|---|---|
| | Story | CloudWatch alarms: AWS billing ($0.10 threshold) |
| | Story | CloudWatch alarms: DynamoDB RCU/WCU (80% free-tier) |
| | Story | CloudWatch alarms: S3 storage (80% of 5GB) |
| | Story | CloudWatch alarms: pipeline job failure (J01-J09) |
| | Story | CloudWatch alarms: model staleness (>30 days) |
| | Story | SNS email subscription setup |
| | Story | DynamoDB job audit record schema and writer |
| | Story | Manual override log writer (universe change / model rollback) |
| | Story | 365-day audit retention policy |

---

#### FEATURE-020: Local Backup and Failover (Milestone M6)
Labels: `type:feature` `phase:1-core` `comp:data-store` `priority:high`
PRD: FR-18

| # | Type | Title |
|---|---|---|
| | Story | S3 → local daily sync script (Bronze/Silver/Gold + artifacts) |
| | Story | DynamoDB → PostgreSQL daily sync script |
| | Story | PostgreSQL failover schema validation test |
| | Story | Local pipeline environment smoke test script |
| | Story | Failover runbook documentation (ADR-004 reference) |

---

#### FEATURE-021: End-to-End Acceptance Testing (Milestone M7)
Labels: `type:feature` `phase:1-core` `comp:monitoring` `priority:critical`
PRD: Definition of Done (Section 9)

| # | Type | Title |
|---|---|---|
| | Story | DoD-01: Full pipeline runs end-to-end without manual intervention |
| | Story | DoD-02: ≥95% symbol OHLCV coverage on 5 consecutive trading days |
| | Story | DoD-03: Delivery % non-null for ≥90% NSE rows |
| | Story | DoD-04: At least one model trained and promoted to production |
| | Story | DoD-05: All 5 serving gates tested with known suppression cases |
| | Story | DoD-06: Trade signals include entry/stop/target/position size for 100% served predictions |
| | Story | DoD-07: AWS billing alarm fires in test (simulated spend event) |
| | Story | DoD-08: PostgreSQL sync verified ≤2 calendar days behind DynamoDB |
| | Story | DoD-09: Failover drill completed within 2 hours |
| | Story | DoD-10: Full pipeline history reconstructable from DynamoDB audit records |

---

## Part 7 — Day-to-Day Workflow

Once everything is set up, this is how you work every day:

### Creating a New Issue

1. Go to your repo → **Issues** → **New issue**
2. Pick the correct template (Feature / Story / Task)
3. Fill in: title, description, acceptance criteria
4. Set: **Labels** (type + phase + comp + priority), **Milestone**, **Assignee** (yourself)
5. Add to **GitHub Project** (drag to `📋 Backlog`)

### Starting Work on a Task

1. Move the issue card from `📋 Backlog` → `🔜 Ready` → `🔧 In Progress`
2. Create a branch: `git checkout -b task/<issue-number>-short-description`
3. Commit with reference: `git commit -m "feat: implement yfinance OHLCV fetcher closes #42"`
4. Push and open a Pull Request linking `Closes #42` in the PR body

### Closing a Task

1. Merge the PR — GitHub auto-closes the linked issue
2. Move parent Story: check off the task in the Story's body `- [x] #42`
3. When all child tasks are closed, close the Story
4. When all child Stories are closed, close the Feature

### Sunday Review Ritual (30 min)

1. Open GitHub Project board
2. Filter by `🚫 Blocked` — resolve blockers or update notes
3. Filter by `👀 In Review` — approve or request changes
4. Plan next 3-5 tasks for the week — move from Backlog to Ready
5. Update any issue notes from your scanner/ops review findings

---

## Part 8 — Recommended Creation Order

Create issues in this exact order to ensure parent links are valid when you create child issues:

```
Step 1: Create all FEATURE issues (FEATURE-001 to FEATURE-021) → note their numbers
Step 2: Create all STORY issues → add parent feature link #<number>
Step 3: Create TASK issues as you start each Story → add parent story link
```

Do not create all tasks upfront. Create Tasks for the next 1-2 Stories only — requirements often evolve.

---

## Summary Checklist

- [ ] GitHub repo created and existing docs pushed
- [ ] All labels created (7 type + 3 phase + 9 comp + 4 priority + 4 state = 27 labels)
- [ ] All 8 milestones created (M0-M7)
- [ ] GitHub Project (v2) created with 6 columns and 6 custom fields
- [ ] 3 issue templates created under `.github/ISSUE_TEMPLATE/`
- [ ] FEATURE-001 through FEATURE-021 created as issues
- [ ] Stories for M0 and M1 created under FEATURE-001 and FEATURE-002
- [ ] First task created and moved to In Progress
