"""
create_github_epics.py
Creates 5 Epic issues and links the 21 existing Feature issues as sub-issues
(visible in the Relationships panel on each Epic).

Epic hierarchy:
  EPIC-001  Project Setup & Architecture    → #1, #2
  EPIC-002  Market Data Ingestion           → #3, #4, #5, #6, #7, #8, #9, #10, #18
  EPIC-003  Feature Store & Transformation  → #11, #12, #13, #14
  EPIC-004  ML Pipeline & Signal Generation → #15, #16, #17
  EPIC-005  Platform Operations & Go-Live   → #19, #20, #21

Usage: python scripts/setup/create_github_epics.py
"""

import subprocess
import json
import os
import tempfile
import time

GH    = r"C:\Program Files\GitHub CLI\gh.exe"
REPO  = "biteberry/project-intelligent"
OWNER = "biteberry"

# ── Epic definitions ──────────────────────────────────────────────────────────
EPICS = [
    {
        "id":        "EPIC-001",
        "title":     "[EPIC-001] Project Setup & Architecture",
        "labels":    ["type:epic", "phase:0-setup", "comp:docs", "priority:critical"],
        "milestone": "M0: Phase 0 - Architecture and Sign-Off",
        "features":  [1, 2],
        "body": """## Description
Establish the full project foundation: architecture sign-off, environment provisioning,
and all artefacts required to pass the Phase 0 gate review.

## PRD Reference
PRD §1, §2 — Project vision and infrastructure requirements

## Architecture Reference
docs/architecture/01_system_overview.md
docs/architecture/02_data_pipeline_design.md

## Child Features
- [ ] #1 — [FEATURE-001] Architecture Phase Closure
- [ ] #2 — [FEATURE-002] Environment Provisioning

## Acceptance Criteria
- [ ] Phase 0 gate audit document approved
- [ ] All architecture docs merged to main
- [ ] Dev environment reproducible from README
- [ ] configs/position_sizing.yaml committed

## Notes
Guardrail G4: no Phase 1 work begins until this Epic is closed.
""",
    },
    {
        "id":        "EPIC-002",
        "title":     "[EPIC-002] Market Data Ingestion",
        "labels":    ["type:epic", "phase:1-core", "comp:ingestion", "layer:bronze", "priority:critical"],
        "milestone": "M2: Phase 1.2 - Data Ingestion Layer",
        "features":  [3, 4, 5, 6, 7, 8, 9, 10, 18],
        "body": """## Description
Ingest all required market data for the India-first stock prediction pipeline:
NSE OHLCV, delivery %, fundamentals, macro indicators, corporate actions,
earnings calendars, circuit bands, and news sentiment.

## PRD Reference
PRD §3 — Data requirements

## Architecture Reference
docs/architecture/03_data_sources.md
docs/architecture/04_ingestion_layer.md

## Child Features
- [ ] #3  — [FEATURE-003] NSE OHLCV Daily Ingestion (J01)
- [ ] #4  — [FEATURE-004] NSE Delivery Percentage Ingestion (J01)
- [ ] #5  — [FEATURE-005] Quarterly Fundamentals Ingestion (J02)
- [ ] #6  — [FEATURE-006] India Macro Data Ingestion (J03)
- [ ] #7  — [FEATURE-007] Earnings Calendar Ingestion (J03)
- [ ] #8  — [FEATURE-008] Corporate Actions Ingestion (J03)
- [ ] #9  — [FEATURE-009] India Macro Event Calendar (J03)
- [ ] #10 — [FEATURE-010] NSE Circuit Band Ingestion (J03)
- [ ] #18 — [FEATURE-018] Finnhub News Sentiment Ingestion

## Acceptance Criteria
- [ ] All data sources land to Bronze layer on schedule
- [ ] Data quality checks pass for 30-day backfill
- [ ] Ingestion jobs monitored and alerting on failure

## Notes
NSE/BSE primary; US data via market_context flag only.
""",
    },
    {
        "id":        "EPIC-003",
        "title":     "[EPIC-003] Feature Store & Transformation",
        "labels":    ["type:epic", "phase:1-core", "comp:feature-eng", "layer:silver", "priority:critical"],
        "milestone": "M3: Phase 1.3 - Feature Engineering Layer",
        "features":  [11, 12, 13, 14],
        "body": """## Description
Transform raw Bronze-layer data through Silver (cleaned, validated) to Gold
(feature-engineered). Covers 10 feature groups and market regime detection.

## PRD Reference
PRD §4 — Feature engineering requirements

## Architecture Reference
docs/architecture/05_feature_engineering.md
docs/architecture/06_data_schema.md

## Child Features
- [ ] #11 — [FEATURE-011] Silver Layer Transformation (J04)
- [ ] #12 — [FEATURE-012] Feature Engineering Groups 1-5 (J04)
- [ ] #13 — [FEATURE-013] Feature Engineering Groups 6-10 (J04)
- [ ] #14 — [FEATURE-014] Market Regime Detection (J05)

## Acceptance Criteria
- [ ] Silver layer passes null/outlier validation suite
- [ ] All 10 feature groups computed and stored in Gold
- [ ] Market regime labels back-tested for coherence

## Notes
Gold layer is the training input to EPIC-004.
""",
    },
    {
        "id":        "EPIC-004",
        "title":     "[EPIC-004] ML Pipeline & Signal Generation",
        "labels":    ["type:epic", "phase:1-core", "comp:ml-pipeline", "layer:gold", "priority:critical"],
        "milestone": "M4: Phase 1.4 - ML Training Pipeline",
        "features":  [15, 16, 17],
        "body": """## Description
Train ML models on Gold-layer features, select the active stock universe,
and produce daily batch trade signals ranked by predicted return.

## PRD Reference
PRD §5 — Model and signal requirements

## Architecture Reference
docs/architecture/07_ml_model_design.md
docs/architecture/08_inference_pipeline.md

## Child Features
- [ ] #15 — [FEATURE-015] ML Training Pipeline (J06)
- [ ] #16 — [FEATURE-016] Universe Selection and Opportunity Scanner (J07)
- [ ] #17 — [FEATURE-017] Daily Batch Inference and Trade Signals (J08)

## Acceptance Criteria
- [ ] Model trains on full history without data leakage
- [ ] Universe filtered to liquid NSE stocks daily
- [ ] Trade signals generated before market open (09:00 IST)

## Notes
Depends on EPIC-003 Gold layer being stable.
""",
    },
    {
        "id":        "EPIC-005",
        "title":     "[EPIC-005] Platform Operations & Go-Live",
        "labels":    ["type:epic", "phase:1-core", "comp:monitoring", "priority:high"],
        "milestone": "M6: Phase 1.6 - Monitoring and Operations",
        "features":  [19, 20, 21],
        "body": """## Description
Instrument the full pipeline with monitoring and alerting, configure local
backup/failover, and run end-to-end acceptance testing before go-live.

## PRD Reference
PRD §6 — Operational requirements

## Architecture Reference
docs/architecture/11_monitoring_alerting.md
docs/architecture/13_disaster_recovery.md

## Child Features
- [ ] #19 — [FEATURE-019] Monitoring and Observability (J09)
- [ ] #20 — [FEATURE-020] Local Backup and Failover
- [ ] #21 — [FEATURE-021] End-to-End Acceptance Testing and Go-Live

## Acceptance Criteria
- [ ] All pipeline stages emit health metrics
- [ ] Backup verified with restore drill
- [ ] Acceptance test suite green on 5 consecutive trading days

## Notes
This Epic closes Phase 1 and triggers M5 phase gate review.
""",
    },
]


def run_gh(*args):
    result = subprocess.run([GH] + list(args), capture_output=True, text=True)
    return result


def create_epic_issue(epic):
    """Create an Epic issue and return its number and node ID."""
    # Write body to temp file to avoid shell escaping issues
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(epic["body"])
        tmp = f.name

    try:
        cmd = [
            GH, "issue", "create",
            "--repo", REPO,
            "--title", epic["title"],
            "--body-file", tmp,
            "--milestone", epic["milestone"],
        ]
        for label in epic["labels"]:
            cmd += ["--label", label]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR creating {epic['id']}: {result.stderr.strip()}")
            return None, None

        # URL is the last non-empty line, e.g. https://github.com/.../issues/22
        url = result.stdout.strip().split("\n")[-1].strip()
        issue_num = int(url.rstrip("/").split("/")[-1])
        print(f"  Created {epic['id']} → #{issue_num}  {url}")
        return issue_num, url
    finally:
        os.unlink(tmp)


def get_issue_db_id(issue_number):
    """Get the integer database ID for an issue number (required by sub-issues REST API)."""
    result = run_gh(
        "api", f"repos/{REPO}/issues/{issue_number}",
        "--jq", ".id"
    )
    if result.returncode != 0:
        return None
    return int(result.stdout.strip())


def add_sub_issue(parent_number, child_db_id):
    """Link child issue as a sub-issue of parent via REST API (integer ID required)."""
    result = run_gh(
        "api",
        f"repos/{REPO}/issues/{parent_number}/sub_issues",
        "--method", "POST",
        "--field", f"sub_issue_id={child_db_id}",
    )
    return result.returncode == 0


def get_issue_node_id(issue_number):
    """Get the GraphQL node ID for an issue number."""
    result = run_gh("issue", "view", str(issue_number),
                    "--repo", REPO, "--json", "id")
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)["id"]


def add_to_project_board(issue_number, project_id="PVT_kwDOD4jskM4BW8Ri"):
    """Add an issue to the project board."""
    node_id = get_issue_node_id(issue_number)
    if not node_id:
        return False
    query = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId contentId: $contentId }) {
        item { id }
      }
    }
    """
    result = subprocess.run(
        [GH, "api", "graphql",
         "-f", f"query={query}",
         "-f", f"projectId={project_id}",
         "-f", f"contentId={node_id}"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def main():
    print("=== Creating Epic Issues ===\n")

    # Step 1: Gather integer database IDs for all 21 Feature issues up front
    print("Fetching Feature issue database IDs...")
    all_feature_numbers = [n for epic in EPICS for n in epic["features"]]
    db_ids = {}
    for num in sorted(set(all_feature_numbers)):
        did = get_issue_db_id(num)
        db_ids[num] = did
        print(f"  #{num} → {did}")
    print()

    # Step 2: Create each Epic and link its Features
    epic_numbers = {}
    for epic in EPICS:
        print(f"\n--- {epic['id']} ---")
        epic_num, _ = create_epic_issue(epic)
        if epic_num is None:
            continue
        epic_numbers[epic["id"]] = epic_num
        time.sleep(1)

        # Add to project board
        ok = add_to_project_board(epic_num)
        print(f"  Board add → {'OK' if ok else 'FAIL'}")
        time.sleep(0.5)

        # Link Feature issues as sub-issues
        print(f"  Linking sub-issues: {epic['features']}")
        for feat_num in epic["features"]:
            did = db_ids.get(feat_num)
            if not did:
                print(f"    #{feat_num} → SKIP (no db ID)")
                continue
            ok = add_sub_issue(epic_num, did)
            print(f"    #{feat_num} → {'OK' if ok else 'FAIL'}")
            time.sleep(0.3)

    print("\n=== Summary ===")
    for eid, enum in epic_numbers.items():
        print(f"  {eid} → #{enum}")
    print(f"\nDone. View issues: https://github.com/{REPO}/issues")


if __name__ == "__main__":
    main()
