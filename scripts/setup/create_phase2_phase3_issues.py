"""
Create Phase 2 and Phase 3 placeholder Epics and Features.

Steps:
1. Create milestones M8 (Phase 2) and M9 (Phase 3)
2. Create EPIC-006, EPIC-007
3. Create FEATURE-022 through FEATURE-028
4. Add each to the project board
5. Set Phase, Priority, Level, Component fields
6. Link Features as sub-issues of their parent Epic
"""

import subprocess, json, urllib.request, urllib.error, time

TOKEN = subprocess.check_output(
    [r"C:\Program Files\GitHub CLI\gh.exe", "auth", "token"], text=True
).strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}

REPO       = "biteberry/project-intelligent"
OWNER      = "biteberry"
REPO_NAME  = "project-intelligent"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

# Project field IDs
PHASE_FIELD_ID    = "PVTSSF_lADOD4jskM4BW8RizhSMsc8"
PHASE_OPTIONS     = {"Phase 0": "ba73d962", "Phase 1": "c9906945", "Phase 2": "223f510f"}
PRIORITY_FIELD_ID = "PVTSSF_lADOD4jskM4BW8RizhSMqPA"
PRIORITY_OPTIONS  = {"P0": "79628723", "P1": "0a877460", "P2": "da944a9c"}
LEVEL_FIELD_ID    = "PVTSSF_lADOD4jskM4BW8RizhSNAoA"
LEVEL_OPTIONS     = {"Epic": "c8bd0023", "Feature": "2af2dcd4", "Story": "5a0d22fc", "Task": "818c6625"}
STATUS_FIELD_ID   = "PVTSSF_lADOD4jskM4BW8RizhSMqHY"
STATUS_BACKLOG    = "f75ad846"


def rest(method, path, body=None):
    url = f"https://api.github.com/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def graphql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body, headers=HEADERS, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def create_milestone(title, description, due_date):
    print(f"  Creating milestone: {title}")
    m = rest("POST", f"repos/{OWNER}/{REPO_NAME}/milestones", {
        "title": title, "description": description, "due_on": due_date,
    })
    return m["number"]


def create_issue(title, body, labels, milestone_number):
    print(f"  Creating issue: {title}")
    issue = rest("POST", f"repos/{OWNER}/{REPO_NAME}/issues", {
        "title": title, "body": body,
        "labels": labels, "milestone": milestone_number,
    })
    return issue["number"], issue["node_id"]


def add_to_project(issue_node_id):
    resp = graphql("""
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
    """, {"projectId": PROJECT_ID, "contentId": issue_node_id})
    return resp["data"]["addProjectV2ItemById"]["item"]["id"]


def set_field(item_id, field_id, option_id):
    graphql("""
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId itemId: $itemId fieldId: $fieldId
            value: { singleSelectOptionId: $optionId }
          }) { projectV2Item { id } }
        }
    """, {"projectId": PROJECT_ID, "itemId": item_id,
          "fieldId": field_id, "optionId": option_id})


def add_sub_issue(parent_number, child_db_id):
    body = json.dumps({"sub_issue_id": child_db_id}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/issues/{parent_number}/sub_issues",
        data=body, headers=HEADERS, method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return True
    except urllib.error.HTTPError as e:
        print(f"    sub-issue link failed: {e.read().decode()}")
        return False


def get_db_id(issue_node_id):
    resp = graphql("{ node(id: \"%s\") { ... on Issue { databaseId } } }" % issue_node_id)
    return resp["data"]["node"]["databaseId"]


def setup_issue(issue_number, issue_node_id, phase, priority, level):
    """Add to board and set all fields."""
    item_id = add_to_project(issue_node_id)
    set_field(item_id, PHASE_FIELD_ID,    PHASE_OPTIONS[phase])
    set_field(item_id, PRIORITY_FIELD_ID, PRIORITY_OPTIONS[priority])
    set_field(item_id, LEVEL_FIELD_ID,    LEVEL_OPTIONS[level])
    set_field(item_id, STATUS_FIELD_ID,   STATUS_BACKLOG)
    print(f"    → Board: {phase} | {priority} | {level} | Backlog ✓")
    return item_id


# ─── ISSUE DEFINITIONS ────────────────────────────────────────────────────────

PHASE2_EPIC_BODY = """\
## Summary
Phase 2 enhancements — extended coverage and new signal types after Phase 1 swing baseline is validated.

## Scope
All Phase 2 features are explicitly deferred from Phase 1 (see PRD §6 Out of Scope).
Work on this Epic begins only after the Phase 1 Definition of Done checklist is signed off.

## Child Features
- #F022 Long-Horizon Signal Generation
- #F023 BSE Shareholding / FII-DII Exact Split
- #F024 Advanced Wyckoff Stage Classifier
- #F025 Sector Rotation Strategy
- #F026 Mobile App / Web Dashboard

## Entry Criteria
- [ ] Phase 1 Definition of Done checklist fully signed off
- [ ] Separate ADR written for each new data source or architecture change
"""

PHASE3_EPIC_BODY = """\
## Summary
Phase 3 advanced ML and NLP capabilities — high complexity, high data cost items deferred from Phase 1.

## Scope
All Phase 3 features require new ADRs and significant infrastructure changes.
Work begins only after Phase 2 is stable.

## Child Features
- #F027 NLP on Earnings Call Transcripts
- #F028 Hidden Markov Market Regime Model

## Entry Criteria
- [ ] Phase 2 fully validated in production
- [ ] ADR written and approved for NLP data pipeline
- [ ] Cost/benefit analysis completed for transcript data sourcing
"""

FEATURES = [
    # (number_label, title, body, labels, phase, level, epic_ref, component)
    (
        "FEATURE-022",
        "[FEATURE-022] Long-Horizon Signal Generation",
        """\
## Summary
Generate swing signals with weekly-to-monthly horizon (weeks to months lookback) using existing Gold layer features.

## Parent Epic
Part of EPIC-006 (Phase 2 Enhancements)

## Why Deferred
PRD §6: Architecture guardrail G1 requires swing horizon fully validated before extending to longer horizons.

## Acceptance Criteria (placeholder)
- [ ] New feature groups defined for weekly/monthly aggregation
- [ ] Walk-forward validation extended to longer horizons
- [ ] Separate model trained and promoted via promotion gate

## Labels
`deferred` `phase:2-enhance` `type:feature`
""",
        ["type:feature", "deferred", "phase:2-enhance"],
        "Phase 2", "Feature",
    ),
    (
        "FEATURE-023",
        "[FEATURE-023] BSE Shareholding Data: FII/DII Exact Split",
        """\
## Summary
Ingest BSE shareholding filings to get exact FII/DII ownership split per symbol (quarterly).

## Parent Epic
Part of EPIC-006 (Phase 2 Enhancements)

## Why Deferred
PRD §6: Requires a new ADR for BSE as a new data source. yfinance cannot provide exact split.

## Acceptance Criteria (placeholder)
- [ ] ADR written and approved for BSE data source integration
- [ ] BSE shareholding parser implemented and tested
- [ ] FII/DII split stored in Silver layer
- [ ] Feature group updated to use exact split vs proxy

## Labels
`deferred` `phase:2-enhance` `type:feature` `comp:ingestion`
""",
        ["type:feature", "deferred", "phase:2-enhance", "comp:ingestion"],
        "Phase 2", "Feature",
    ),
    (
        "FEATURE-024",
        "[FEATURE-024] Advanced Wyckoff Stage Classifier",
        """\
## Summary
Full Wyckoff stage classification (Accumulation / Markup / Distribution / Markdown) beyond the OBV proxy used in Phase 1.

## Parent Epic
Part of EPIC-006 (Phase 2 Enhancements)

## Why Deferred
PRD §6: OBV proxy is sufficient for Phase 1. Full classifier requires labelled training data and is high complexity.

## Acceptance Criteria (placeholder)
- [ ] Wyckoff stage labelling methodology documented in ADR
- [ ] Historical stage labels generated for training
- [ ] Classifier trained and back-tested
- [ ] Integrated into feature pipeline replacing OBV proxy

## Labels
`deferred` `phase:2-enhance` `type:feature` `comp:feature-eng`
""",
        ["type:feature", "deferred", "phase:2-enhance", "comp:feature-eng"],
        "Phase 2", "Feature",
    ),
    (
        "FEATURE-025",
        "[FEATURE-025] Sector Rotation Strategy",
        """\
## Summary
Detect sector momentum cycles and rotate universe selection based on sector relative strength.

## Parent Epic
Part of EPIC-006 (Phase 2 Enhancements)

## Why Deferred
PRD §6: Phase 2 expansion after swing baseline validated. Requires sector-level feature groups not in Phase 1.

## Acceptance Criteria (placeholder)
- [ ] Sector classification mapped to NSE universe
- [ ] Sector relative strength feature group added to Gold layer
- [ ] Universe scanner updated to weight by sector momentum
- [ ] Back-test demonstrates improvement over Phase 1 baseline

## Labels
`deferred` `phase:2-enhance` `type:feature` `comp:universe`
""",
        ["type:feature", "deferred", "phase:2-enhance", "comp:universe"],
        "Phase 2", "Feature",
    ),
    (
        "FEATURE-026",
        "[FEATURE-026] Mobile App / Web Dashboard",
        """\
## Summary
Lightweight web dashboard to visualise trade signals, portfolio positions, and model performance metrics.

## Parent Epic
Part of EPIC-006 (Phase 2 Enhancements)

## Why Deferred
PRD §6: Single operator platform in Phase 1 — no UI needed. Phase 2 product skeleton once signals are validated.

## Acceptance Criteria (placeholder)
- [ ] Architecture ADR written for frontend stack
- [ ] Signal dashboard showing open positions and latest predictions
- [ ] Model performance metrics (precision, recall, Sharpe) displayed
- [ ] Deployed on EC2 or serverless with auth

## Labels
`deferred` `phase:2-enhance` `type:feature`
""",
        ["type:feature", "deferred", "phase:2-enhance"],
        "Phase 2", "Feature",
    ),
    (
        "FEATURE-027",
        "[FEATURE-027] NLP on Earnings Call Transcripts",
        """\
## Summary
Extract sentiment and topic signals from NSE earnings call transcripts using NLP/LLM pipeline.

## Parent Epic
Part of EPIC-007 (Phase 3 Advanced ML & NLP)

## Why Deferred
PRD §6: Complexity 5, data cost high. Transcript sourcing requires paid API or scraping with legal review.

## Acceptance Criteria (placeholder)
- [ ] Transcript data source identified, cost approved, ADR written
- [ ] NLP pipeline (sentiment + topic extraction) implemented
- [ ] Earnings sentiment feature added to Gold layer
- [ ] Walk-forward back-test shows lift over Phase 1 baseline

## Labels
`deferred` `type:feature` `comp:ingestion` `comp:feature-eng`
""",
        ["type:feature", "deferred", "comp:ingestion"],
        "Phase 2", "Feature",  # board only has Phase 0/1/2 options; use Phase 2 + deferred label
    ),
    (
        "FEATURE-028",
        "[FEATURE-028] Hidden Markov Market Regime Model",
        """\
## Summary
Replace the Phase 1 rule-based market regime classifier with a probabilistic Hidden Markov Model (HMM).

## Parent Epic
Part of EPIC-007 (Phase 3 Advanced ML & NLP)

## Why Deferred
PRD §6: Rule-based classifier is sufficient for Phase 1. HMM adds complexity with uncertain lift until baseline validated.

## Acceptance Criteria (placeholder)
- [ ] ADR written comparing rule-based vs HMM approaches
- [ ] HMM trained on historical regime data
- [ ] A/B comparison back-test vs Phase 1 rule-based regime
- [ ] HMM integrated into feature pipeline if back-test shows >5% lift

## Labels
`deferred` `type:feature` `comp:ml-pipeline`
""",
        ["type:feature", "deferred", "comp:ml-pipeline"],
        "Phase 2", "Feature",
    ),
]


def main():
    # ── Step 1: Create milestones ──────────────────────────────────────────────
    print("\n=== Step 1: Create Milestones ===")
    m8 = create_milestone(
        "M8: Phase 2 - Enhancements & Extended Coverage",
        "Phase 2 features: long-horizon signals, BSE data, Wyckoff, sector rotation, web dashboard",
        "2027-06-30T00:00:00Z",
    )
    m9 = create_milestone(
        "M9: Phase 3 - Advanced ML & NLP",
        "Phase 3 features: NLP on transcripts, Hidden Markov regime model",
        "2028-06-30T00:00:00Z",
    )
    print(f"  M8 (Phase 2) = milestone #{m8}")
    print(f"  M9 (Phase 3) = milestone #{m9}")

    # ── Step 2: Create EPIC-006 ────────────────────────────────────────────────
    print("\n=== Step 2: Create EPIC-006 (Phase 2) ===")
    epic6_num, epic6_node = create_issue(
        "[EPIC-006] Phase 2 — Enhancements & Extended Coverage",
        PHASE2_EPIC_BODY,
        ["type:feature", "deferred", "phase:2-enhance"],
        m8,
    )
    print(f"  Created #epic6_num={epic6_num}")
    setup_issue(epic6_num, epic6_node, "Phase 2", "P2", "Epic")

    # ── Step 3: Create EPIC-007 ────────────────────────────────────────────────
    print("\n=== Step 3: Create EPIC-007 (Phase 3) ===")
    epic7_num, epic7_node = create_issue(
        "[EPIC-007] Phase 3 — Advanced ML & NLP",
        PHASE3_EPIC_BODY,
        ["type:feature", "deferred"],
        m9,
    )
    print(f"  Created #epic7_num={epic7_num}")
    setup_issue(epic7_num, epic7_node, "Phase 2", "P2", "Epic")

    # ── Step 4: Create Features ────────────────────────────────────────────────
    print("\n=== Step 4: Create Features ===")
    feature_issues = []  # (number, node_id, label, parent_epic_num)

    epic6_features = ["FEATURE-022", "FEATURE-023", "FEATURE-024", "FEATURE-025", "FEATURE-026"]

    for feat in FEATURES:
        label, title, body, labels, phase, level = feat
        parent_epic = epic6_num if label in epic6_features else epic7_num
        milestone = m8 if label in epic6_features else m9

        num, node = create_issue(title, body, labels, milestone)
        print(f"  Created #{num}: {title[:55]}")
        setup_issue(num, node, phase, "P2", level)
        feature_issues.append((num, node, label, parent_epic))
        time.sleep(0.3)  # rate limit courtesy

    # ── Step 5: Link Features as sub-issues of Epics ──────────────────────────
    print("\n=== Step 5: Link sub-issues ===")
    for num, node, label, parent_epic in feature_issues:
        db_id = get_db_id(node)
        ok = add_sub_issue(parent_epic, db_id)
        status = "✓" if ok else "✗"
        print(f"  #{num} ({label}) → Epic #{parent_epic}  {status}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"""
=== Done! ===
Milestones created:  M8 (Phase 2) #{m8},  M9 (Phase 3) #{m9}
EPIC-006 (Phase 2):  #{epic6_num}
EPIC-007 (Phase 3):  #{epic7_num}
Features created:    {', '.join('#' + str(n) for n, _, _, _ in feature_issues)}
""")


if __name__ == "__main__":
    main()
