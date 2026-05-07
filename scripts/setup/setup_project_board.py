"""
setup_project_board.py
Populates Priority, Phase, Component, Layer, and Job fields on all 21 project items
by reading each issue's labels from GitHub and mapping them to project field values.

Usage: python scripts/setup/setup_project_board.py
Requires: gh CLI authenticated (gh auth login), Python 3.7+
"""

import subprocess
import json
import sys
import time

GH           = r"C:\Program Files\GitHub CLI\gh.exe"
OWNER        = "biteberry"
REPO         = "biteberry/project-intelligent"
PROJECT_NUM  = 2

# ── Field IDs (from: gh project field-list 2 --owner biteberry) ──────────────
FIELD_IDS = {
    "Status":       "PVTSSF_lADOD4jskM4BW8RizhSMqHY",
    "Priority":     "PVTSSF_lADOD4jskM4BW8RizhSMqPA",
    "Phase":        "PVTSSF_lADOD4jskM4BW8RizhSMsc8",
    "Component":    "PVTSSF_lADOD4jskM4BW8RizhSMtC8",
    "Layer":        "PVTSSF_lADOD4jskM4BW8RizhSMtNo",
    "Job":          "PVTSSF_lADOD4jskM4BW8RizhSMtdY",
}

PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

# ── Label → field value mappings ──────────────────────────────────────────────
# Priority options in board are P0/P1/P2 (as created manually)
PRIORITY_MAP = {
    "priority:critical": "P0",
    "priority:high":     "P1",
    "priority:medium":   "P2",
    "priority:low":      "P2",
}

PHASE_MAP = {
    "phase:0-setup":   "Phase 0",
    "phase:1-core":    "Phase 1",
    "phase:2-enhance": "Phase 2",
}

COMPONENT_MAP = {
    "comp:ingestion":   "Ingestion",
    "comp:feature-eng": "Feature-Eng",
    "comp:ml-pipeline": "ML-Pipeline",
    "comp:inference":   "Inference",
    "comp:universe":    "Universe",
    "comp:monitoring":  "Monitoring",
    "comp:infra":       "Infra",
    "comp:data-store":  "Data-Store",
    # comp:docs not in board options yet — skip silently
}

LAYER_MAP = {
    "layer:landing": "Landing",
    "layer:bronze":  "Bronze",
    "layer:silver":  "Silver",
    "layer:gold":    "Gold",
}

# Job derived from issue title keywords
JOB_MAP = {
    "J01": "J01",
    "J02": "J02",
    "J03": "J03",
    "J04": "J04",
    "J05": "J05",
    "J06": "J06",
    "J07": "J07",
    "J08": "J08",
    "J09": "J09",
}


def gh_graphql(query, variables=None):
    cmd = [GH, "api", "graphql", "-f", f"query={query}"]
    if variables:
        for k, v in variables.items():
            cmd += ["-f", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  GraphQL error: {result.stderr.strip()}")
        return None
    return json.loads(result.stdout)


def get_field_options(field_id):
    """Get all single-select options for a field."""
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                options { id name }
              }
            }
          }
        }
      }
    }
    """
    data = gh_graphql(query, {"projectId": PROJECT_ID})
    if not data:
        return {}
    options_map = {}
    for field in data["data"]["node"]["fields"]["nodes"]:
        if field.get("id") == field_id:
            for opt in field.get("options", []):
                options_map[opt["name"]] = opt["id"]
    return options_map


def get_project_items():
    """Get all items in the project with their issue numbers, labels, and titles."""
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 50) {
            nodes {
              id
              content {
                ... on Issue {
                  number
                  title
                  labels(first: 20) {
                    nodes { name }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    data = gh_graphql(query, {"projectId": PROJECT_ID})
    if not data:
        return []
    return data["data"]["node"]["items"]["nodes"]


def set_field_value(item_id, field_id, option_id):
    """Set a single-select field value on a project item."""
    query = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId
        itemId: $itemId
        fieldId: $fieldId
        value: { singleSelectOptionId: $optionId }
      }) {
        projectV2Item { id }
      }
    }
    """
    cmd = [
        GH, "api", "graphql",
        "-f", f"query={query}",
        "-f", f"projectId={PROJECT_ID}",
        "-f", f"itemId={item_id}",
        "-f", f"fieldId={field_id}",
        "-f", f"optionId={option_id}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def detect_job(title):
    """Detect job number from issue title."""
    for job in ["J01", "J02", "J03", "J04", "J05", "J06", "J07", "J08", "J09"]:
        if job in title:
            return job
    # Special cases by feature number
    if "FEATURE-016" in title or "Universe" in title:
        return "J07"
    if "FEATURE-001" in title or "FEATURE-002" in title:
        return None  # No job for setup features
    if "FEATURE-021" in title:
        return None
    return None


def main():
    print("Fetching field option IDs...")
    options = {}
    for field_name, field_id in FIELD_IDS.items():
        opts = get_field_options(field_id)
        options[field_name] = opts
        print(f"  {field_name}: {list(opts.keys())}")

    print("\nFetching project items...")
    items = get_project_items()
    print(f"  Found {len(items)} items\n")

    success = 0
    for item in items:
        content = item.get("content", {})
        if not content:
            continue

        item_id    = item["id"]
        issue_num  = content.get("number")
        title      = content.get("title", "")
        label_names = [l["name"] for l in content.get("labels", {}).get("nodes", [])]

        print(f"Issue #{issue_num}: {title[:55]}")

        # ── Priority ──────────────────────────────────────────────────────────
        priority_val = next((PRIORITY_MAP[l] for l in label_names if l in PRIORITY_MAP), None)
        if priority_val and priority_val in options["Priority"]:
            ok = set_field_value(item_id, FIELD_IDS["Priority"], options["Priority"][priority_val])
            print(f"  Priority  → {priority_val} {'OK' if ok else 'FAIL'}")

        # ── Phase ─────────────────────────────────────────────────────────────
        phase_val = next((PHASE_MAP[l] for l in label_names if l in PHASE_MAP), None)
        if phase_val and phase_val in options["Phase"]:
            ok = set_field_value(item_id, FIELD_IDS["Phase"], options["Phase"][phase_val])
            print(f"  Phase     → {phase_val} {'OK' if ok else 'FAIL'}")

        # ── Component ─────────────────────────────────────────────────────────
        comp_val = next((COMPONENT_MAP[l] for l in label_names if l in COMPONENT_MAP), None)
        if comp_val and comp_val in options["Component"]:
            ok = set_field_value(item_id, FIELD_IDS["Component"], options["Component"][comp_val])
            print(f"  Component → {comp_val} {'OK' if ok else 'FAIL'}")

        # ── Layer ─────────────────────────────────────────────────────────────
        layer_val = next((LAYER_MAP[l] for l in label_names if l in LAYER_MAP), None)
        if layer_val and layer_val in options["Layer"]:
            ok = set_field_value(item_id, FIELD_IDS["Layer"], options["Layer"][layer_val])
            print(f"  Layer     → {layer_val} {'OK' if ok else 'FAIL'}")

        # ── Job ───────────────────────────────────────────────────────────────
        job_val = detect_job(title)
        if job_val and job_val in options["Job"]:
            ok = set_field_value(item_id, FIELD_IDS["Job"], options["Job"][job_val])
            print(f"  Job       → {job_val} {'OK' if ok else 'FAIL'}")

        success += 1
        time.sleep(0.3)  # avoid rate limiting

    print(f"\nDone. Processed {success}/{len(items)} items.")
    print(f"View board: https://github.com/orgs/{OWNER}/projects/{PROJECT_NUM}")


if __name__ == "__main__":
    main()
