"""
Bulk-set Priority on all project items that have no Priority assigned.

Priority logic:
  - Epic  → P0
  - Feature → P0 (Phase 0) or P1 (Phase 1) or P2 (Phase 2)
  - Story / Task → P0 (Phase 0) or P1 (Phase 1) or P2 (Phase 2)
  - No Level set → P1 default
"""

import subprocess, json, sys

TOKEN = subprocess.check_output(
    [r"C:\Program Files\GitHub CLI\gh.exe", "auth", "token"], text=True
).strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}

PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"
PRIORITY_FIELD_ID = "PVTSSF_lADOD4jskM4BW8RizhSMqPA"
PRIORITY_OPTIONS = {"P0": "79628723", "P1": "0a877460", "P2": "da944a9c"}

import urllib.request, urllib.error

def graphql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers=HEADERS,
        method="POST",
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
              content { ... on Issue { number title } }
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
    items = []
    cursor = None
    while True:
        resp = graphql(query, {"projectId": PROJECT_ID, "cursor": cursor})
        page = resp["data"]["node"]["items"]
        items.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return items


def set_priority(item_id, priority_label):
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId
        itemId: $itemId
        fieldId: $fieldId
        value: { singleSelectOptionId: $optionId }
      }) { projectV2Item { id } }
    }
    """
    graphql(mutation, {
        "projectId": PROJECT_ID,
        "itemId": item_id,
        "fieldId": PRIORITY_FIELD_ID,
        "optionId": PRIORITY_OPTIONS[priority_label],
    })


def determine_priority(level, phase):
    if level == "Epic":
        return "P0"
    if phase == "Phase 0":
        return "P0"
    if phase == "Phase 1":
        return "P1"
    if phase == "Phase 2":
        return "P2"
    # No phase set — use level to guess
    if level == "Feature":
        return "P1"
    return "P1"  # default


def main():
    print("Fetching project items...")
    items = get_all_items()
    print(f"Total items: {len(items)}")

    no_priority = []
    for item in items:
        fields = {fv.get("field", {}).get("name"): fv.get("name")
                  for fv in item["fieldValues"]["nodes"] if fv.get("field")}
        priority = fields.get("Priority")
        level = fields.get("Level", "")
        phase = fields.get("Phase", "")
        issue = item.get("content") or {}
        number = issue.get("number", "?")
        title = issue.get("title", "(no title)")

        if not priority:
            no_priority.append({
                "id": item["id"],
                "number": number,
                "title": title,
                "level": level,
                "phase": phase,
            })

    print(f"\nItems with no Priority: {len(no_priority)}")
    print(f"{'#':<6} {'Level':<10} {'Phase':<12} {'Assign':<8} Title")
    print("-" * 80)

    for item in no_priority:
        p = determine_priority(item["level"], item["phase"])
        print(f"#{item['number']:<5} {item['level']:<10} {item['phase']:<12} {p:<8} {item['title'][:55]}")

    if not no_priority:
        print("All items already have Priority set!")
        return

    print(f"\nSetting priorities on {len(no_priority)} items...")
    for item in no_priority:
        p = determine_priority(item["level"], item["phase"])
        try:
            set_priority(item["id"], p)
            print(f"  #{item['number']:>4} → {p}  ({item['title'][:50]})")
        except Exception as e:
            print(f"  #{item['number']:>4} FAILED: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
