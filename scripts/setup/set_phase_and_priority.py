"""
Bulk-set Phase field on all project items based on their GitHub milestone,
then update Priority to match (Phase 0 → P0, Phase 1 → P1, Phase 2 → P2).

Phase mapping (from milestone name):
  M0 / Phase 0  → Phase 0 → P0
  M1–M7 / Phase 1.x → Phase 1 → P1
  Phase 2 / deferred → Phase 2 → P2
  Epics with no milestone but #22 → Phase 0, others → Phase 1
"""

import subprocess, json, urllib.request, urllib.error

TOKEN = subprocess.check_output(
    [r"C:\Program Files\GitHub CLI\gh.exe", "auth", "token"], text=True
).strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}

PROJECT_ID   = "PVT_kwDOD4jskM4BW8Ri"

PHASE_FIELD_ID    = "PVTSSF_lADOD4jskM4BW8RizhSMsc8"
PHASE_OPTIONS     = {"Phase 0": "ba73d962", "Phase 1": "c9906945", "Phase 2": "223f510f"}

PRIORITY_FIELD_ID = "PVTSSF_lADOD4jskM4BW8RizhSMqPA"
PRIORITY_OPTIONS  = {"P0": "79628723", "P1": "0a877460", "P2": "da944a9c"}

PHASE_TO_PRIORITY = {"Phase 0": "P0", "Phase 1": "P1", "Phase 2": "P2"}

# Manual overrides for issues where milestone alone isn't enough
# key = issue number, value = "Phase 0" | "Phase 1" | "Phase 2"
MANUAL_PHASE = {
    # Epics
    22: "Phase 0",  # [EPIC-001] Project Setup & Architecture
    23: "Phase 1",  # [EPIC-002] Market Data Ingestion
    24: "Phase 1",  # [EPIC-003] Feature Store & Transformation
    25: "Phase 1",  # [EPIC-004] ML Pipeline & Signal Generation
    26: "Phase 1",  # [EPIC-005] Platform Operations & Go-Live
    # Features
    1:  "Phase 0",  # [FEATURE-001] Architecture Phase Closure
    2:  "Phase 1",  # [FEATURE-002] Environment Provisioning
    3:  "Phase 1",  4:  "Phase 1",  5:  "Phase 1",
    6:  "Phase 1",  7:  "Phase 1",  8:  "Phase 1",
    9:  "Phase 1",  10: "Phase 1",  11: "Phase 1",
    12: "Phase 1",  13: "Phase 1",  14: "Phase 1",
    15: "Phase 1",  16: "Phase 1",  17: "Phase 1",
    18: "Phase 2",  # [FEATURE-018] Finnhub News Sentiment — deferred
    19: "Phase 1",  20: "Phase 1",  21: "Phase 1",
    # Phase 0 stories/tasks (M0 milestone)
    27: "Phase 0",  28: "Phase 0",  29: "Phase 0",  30: "Phase 0",
    31: "Phase 0",  32: "Phase 0",  33: "Phase 0",  34: "Phase 0",
    35: "Phase 0",  36: "Phase 0",  37: "Phase 0",  38: "Phase 0",
    39: "Phase 0",  40: "Phase 0",  41: "Phase 0",  42: "Phase 0",
    43: "Phase 0",
}


def graphql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body, headers=HEADERS, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get_all_items():
    query = """
    query($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
            nodes {
              id
              content {
                ... on Issue {
                  number title
                  milestone { title }
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field { ... on ProjectV2SingleSelectField { name } }
                  }
                }
              }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """
    items, cursor = [], None
    while True:
        resp = graphql(query, {"projectId": PROJECT_ID, "cursor": cursor})
        page = resp["data"]["node"]["items"]
        items.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return items


def set_field(item_id, field_id, option_id):
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId itemId: $itemId fieldId: $fieldId
        value: { singleSelectOptionId: $optionId }
      }) { projectV2Item { id } }
    }
    """
    graphql(mutation, {
        "projectId": PROJECT_ID, "itemId": item_id,
        "fieldId": field_id, "optionId": option_id,
    })


def determine_phase(number, milestone_title):
    # Manual override takes priority
    if number in MANUAL_PHASE:
        return MANUAL_PHASE[number]
    # Derive from milestone name
    if milestone_title:
        t = milestone_title.lower()
        if "phase 0" in t or "m0" in t:
            return "Phase 0"
        if "phase 2" in t or "phase b" in t or "phase c" in t:
            return "Phase 2"
        if "phase 1" in t or any(f"m{i}" in t for i in range(1, 8)):
            return "Phase 1"
    # Default: all active work is Phase 1
    return "Phase 1"


def main():
    print("Fetching all project items...")
    items = get_all_items()
    print(f"Total items: {len(items)}\n")

    print(f"{'#':<6} {'Current Phase':<14} {'New Phase':<12} {'Priority':<10} Title")
    print("-" * 90)

    counts = {"Phase 0": 0, "Phase 1": 0, "Phase 2": 0}
    updates = []

    for item in items:
        issue = item.get("content") or {}
        number = issue.get("number")
        title  = issue.get("title", "(no title)")
        milestone = (issue.get("milestone") or {}).get("title", "")

        fv = {f.get("field", {}).get("name"): f.get("name")
              for f in item["fieldValues"]["nodes"] if f.get("field")}
        current_phase = fv.get("Phase", "")

        phase = determine_phase(number or 0, milestone)
        priority = PHASE_TO_PRIORITY[phase]
        counts[phase] += 1

        print(f"#{str(number):<5} {current_phase or '(none)':<14} {phase:<12} {priority:<10} {title[:45]}")
        updates.append((item["id"], phase, priority, number, title))

    print(f"\nSummary: Phase 0={counts['Phase 0']}  Phase 1={counts['Phase 1']}  Phase 2={counts['Phase 2']}")
    print(f"\nApplying Phase + Priority to {len(updates)} items...\n")

    for item_id, phase, priority, number, title in updates:
        try:
            set_field(item_id, PHASE_FIELD_ID, PHASE_OPTIONS[phase])
            set_field(item_id, PRIORITY_FIELD_ID, PRIORITY_OPTIONS[priority])
            print(f"  #{str(number):<4} → {phase}  {priority}  ✓")
        except Exception as e:
            print(f"  #{str(number):<4} FAILED: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
