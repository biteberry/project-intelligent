"""
create_hierarchy_view.py
1. Creates a "Type" single-select field (Epic/Feature/Story/Task)
2. Adds all 43 issues to the project (idempotent) and sets their Type
3. Creates a new "Hierarchy" table view grouped by Type

This gives a clear tiered view:
  [Epic]    EPIC-001 #22 ▶ … EPIC-005 #26
  [Feature] FEATURE-001 #1 ▶ … FEATURE-021 #21
  [Story]   STORY-001 #27 ▶ … STORY-004 #30
  [Task]    TASK-001 #31 … TASK-013 #43

Click ▶ on any item to drill into its children.

Run: python scripts/setup/create_hierarchy_view.py
"""

import subprocess
import json
import time
import sys

GH         = r"C:\Program Files\GitHub CLI\gh.exe"
REPO       = "biteberry/project-intelligent"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"
OWNER      = "biteberry"

# Issue number ranges per type
TYPE_ISSUES = {
    "Epic":    list(range(22, 27)),   # #22–#26
    "Feature": list(range(1,  22)),   # #1–#21
    "Story":   list(range(27, 31)),   # #27–#30
    "Task":    list(range(31, 44)),   # #31–#43
}

TYPE_COLORS = {
    "Epic":    "PURPLE",
    "Feature": "BLUE",
    "Story":   "GREEN",
    "Task":    "ORANGE",
}


def gh_gql(query, variables=None):
    """Run a GraphQL query/mutation. Returns (data_dict, error_str)."""
    cmd = [GH, "api", "graphql", "-f", f"query={query}"]
    if variables:
        for k, v in variables.items():
            cmd += ["-f", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return None, r.stderr.strip()
    parsed = json.loads(r.stdout)
    if "errors" in parsed:
        return None, str(parsed["errors"])
    return parsed, None


def get_or_create_type_field():
    """Return (field_id, {option_name: option_id}) for the 'Type' field."""
    # Check if it already exists
    q = """
    query($pid: ID!) {
      node(id: $pid) {
        ... on ProjectV2 {
          fields(first: 30) {
            nodes {
              ... on ProjectV2SingleSelectField { id name options { id name } }
            }
          }
        }
      }
    }
    """
    data, _ = gh_gql(q, {"pid": PROJECT_ID})
    if data:
        for field in data["data"]["node"]["fields"]["nodes"]:
            if field.get("name") == "Level":
                opts = {o["name"]: o["id"] for o in field.get("options", [])}
                print(f"  'Level' field exists ({field['id']}): {list(opts.keys())}")
                return field["id"], opts

    # Build the options fragment
    options_fragment = ", ".join(
        f'{{name: "{name}", color: {color}, description: ""}}'
        for name, color in TYPE_COLORS.items()
    )

    mutation = """
    mutation($pid: ID!) {
      createProjectV2Field(input: {
        projectId: $pid
        dataType: SINGLE_SELECT
        name: "Level"
        singleSelectOptions: [""" + options_fragment + """]
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
      }
    }
    """
    data, err = gh_gql(mutation, {"pid": PROJECT_ID})
    if not data:
        print(f"  ERROR creating Type field: {err}")
        return None, {}
    field = data["data"]["createProjectV2Field"]["projectV2Field"]
    opts = {o["name"]: o["id"] for o in field.get("options", [])}
    print(f"  Created 'Level' field ({field['id']}): {list(opts.keys())}")
    return field["id"], opts


def get_issue_node_id(issue_num):
    r = subprocess.run(
        [GH, "issue", "view", str(issue_num), "--repo", REPO, "--json", "id"],
        capture_output=True, text=True, encoding="utf-8"
    )
    return json.loads(r.stdout)["id"] if r.returncode == 0 else None


def add_to_project(node_id):
    """Add issue to project (idempotent). Returns project item ID."""
    mutation = """
    mutation($pid: ID!, $cid: ID!) {
      addProjectV2ItemById(input: { projectId: $pid contentId: $cid }) {
        item { id }
      }
    }
    """
    data, _ = gh_gql(mutation, {"pid": PROJECT_ID, "cid": node_id})
    return data["data"]["addProjectV2ItemById"]["item"]["id"] if data else None


def set_type_field(item_id, field_id, option_id):
    mutation = """
    mutation($pid: ID!, $iid: ID!, $fid: ID!, $oid: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $pid  itemId: $iid  fieldId: $fid
        value: { singleSelectOptionId: $oid }
      }) { projectV2Item { id } }
    }
    """
    data, err = gh_gql(mutation, {
        "pid": PROJECT_ID, "iid": item_id, "fid": field_id, "oid": option_id
    })
    return data is not None, err


def get_existing_views():
    q = """
    query($pid: ID!) {
      node(id: $pid) {
        ... on ProjectV2 {
          views(first: 20) { nodes { id number name } }
        }
      }
    }
    """
    data, _ = gh_gql(q, {"pid": PROJECT_ID})
    if not data:
        return []
    return data["data"]["node"]["views"]["nodes"]


def create_hierarchy_view(type_field_id):
    """Create (or reuse) a table view grouped by the Type field."""
    views = get_existing_views()
    print(f"  Existing views: {[v['name'] for v in views]}")

    existing = next((v for v in views if "Hierarchy" in v["name"]), None)

    if not existing:
        mutation = """
        mutation($pid: ID!) {
          createProjectV2View(input: {
            projectId: $pid
            name: "Hierarchy"
            layout: TABLE_LAYOUT
          }) {
            projectV2View { id number name }
          }
        }
        """
        data, err = gh_gql(mutation, {"pid": PROJECT_ID})
        if not data:
            print(f"  ERROR creating view: {err}")
            return None
        existing = data["data"]["createProjectV2View"]["projectV2View"]
        print(f"  Created 'Hierarchy' view #{existing['number']}")
    else:
        print(f"  Reusing 'Hierarchy' view #{existing['number']}")

    # Group by the Type field
    view_id = existing["id"]
    mutation = """
    mutation($pid: ID!, $vid: ID!, $fid: String!) {
      updateProjectV2View(input: {
        projectId: $pid
        viewId: $vid
        groupByFields: [$fid]
      }) {
        projectV2View { id name }
      }
    }
    """
    data, err = gh_gql(mutation, {
        "pid": PROJECT_ID, "vid": view_id, "fid": type_field_id
    })
    if data:
        print(f"  Grouped by 'Type' field OK")
    else:
        print(f"  WARNING: Could not set groupBy: {err}")

    return existing


def main():
    # ── Step 1: Type field ────────────────────────────────────────────────────
    print("=== Step 1: Type field ===")
    type_field_id, type_options = get_or_create_type_field()
    if not type_field_id:
        sys.exit("FATAL: cannot proceed without Type field")

    # ── Step 2: Add all issues and set Type ───────────────────────────────────
    print("\n=== Step 2: Set Type on all 43 issues ===")
    results = {"ok": 0, "fail": 0}

    for type_name, issue_nums in TYPE_ISSUES.items():
        option_id = type_options.get(type_name)
        if not option_id:
            print(f"\n  [{type_name}] WARNING: no option ID — skipping {len(issue_nums)} issues")
            continue

        print(f"\n  [{type_name}] {len(issue_nums)} issues")
        for num in issue_nums:
            node_id = get_issue_node_id(num)
            if not node_id:
                print(f"    #{num}: SKIP (no node ID)")
                results["fail"] += 1
                continue

            item_id = add_to_project(node_id)
            if not item_id:
                print(f"    #{num}: FAIL (not added to project)")
                results["fail"] += 1
                continue

            ok, err = set_type_field(item_id, type_field_id, option_id)
            status = "OK" if ok else f"FAIL ({err[:40]})"
            print(f"    #{num}: {status}")
            if ok:
                results["ok"] += 1
            else:
                results["fail"] += 1
            time.sleep(0.25)

    print(f"\n  Totals: {results['ok']} OK, {results['fail']} FAIL")

    # ── Step 3: Create Hierarchy view ─────────────────────────────────────────
    print("\n=== Step 3: Create Hierarchy view ===")
    view = create_hierarchy_view(type_field_id)

    print("\n=== Done ===")
    if view:
        url = f"https://github.com/users/{OWNER}/projects/2/views/{view.get('number', '?')}"
        print(f"  Hierarchy view: {url}")
    print("""
  How to navigate:
    Epic    (#22-26)  ▶  expand to see Features
    Feature (#1-21)   ▶  expand to see Stories
    Story   (#27-30)  ▶  expand to see Tasks
    Task    (#31-43)     leaf nodes
""")


if __name__ == "__main__":
    main()
