"""
set_epic_board_fields.py
Sets Priority, Phase, and Component fields on the 5 Epic issues using
the known project board item IDs (from addProjectV2ItemById mutation).
"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

# Item IDs returned by addProjectV2ItemById for the Epic issues
EPIC_ITEMS = [
    {"issue": 22, "item_id": "PVTI_lADOD4jskM4BW8RizgsBFr4", "epic": "EPIC-001",
     "priority": "P0", "phase": "Phase 0", "component": None,    "layer": None},
    {"issue": 23, "item_id": "PVTI_lADOD4jskM4BW8RizgsBGQg", "epic": "EPIC-002",
     "priority": "P0", "phase": "Phase 1", "component": "Ingestion", "layer": "Bronze"},
    {"issue": 24, "item_id": "PVTI_lADOD4jskM4BW8RizgsBGUA", "epic": "EPIC-003",
     "priority": "P0", "phase": "Phase 1", "component": "Feature-Eng","layer": "Silver"},
    {"issue": 25, "item_id": "PVTI_lADOD4jskM4BW8RizgsBGXM", "epic": "EPIC-004",
     "priority": "P0", "phase": "Phase 1", "component": "ML-Pipeline","layer": "Gold"},
    {"issue": 26, "item_id": "PVTI_lADOD4jskM4BW8RizgsBGZs", "epic": "EPIC-005",
     "priority": "P1", "phase": "Phase 1", "component": "Monitoring", "layer": None},
]

# Field IDs
FIELD_IDS = {
    "Priority":  "PVTSSF_lADOD4jskM4BW8RizhSMqPA",
    "Phase":     "PVTSSF_lADOD4jskM4BW8RizhSMsc8",
    "Component": "PVTSSF_lADOD4jskM4BW8RizhSMtC8",
    "Layer":     "PVTSSF_lADOD4jskM4BW8RizhSMtNo",
}

mutation = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId itemId: $itemId fieldId: $fieldId
    value: { singleSelectOptionId: $optionId }
  }) {
    projectV2Item { id }
  }
}
"""

def get_field_options(field_id):
    q = """query($pid: ID!) { node(id: $pid) { ... on ProjectV2 { fields(first: 30) { nodes { ... on ProjectV2SingleSelectField { id options { id name } } } } } } }"""
    r = subprocess.run([GH, "api", "graphql", "-f", f"query={q}", "-f", f"pid={PROJECT_ID}"], capture_output=True, text=True)
    options = {}
    for field in json.loads(r.stdout)["data"]["node"]["fields"]["nodes"]:
        if field.get("id") == field_id:
            for opt in field.get("options", []):
                options[opt["name"]] = opt["id"]
    return options

def set_field(item_id, field_id, option_id):
    r = subprocess.run(
        [GH, "api", "graphql",
         "-f", f"query={mutation}",
         "-f", f"projectId={PROJECT_ID}",
         "-f", f"itemId={item_id}",
         "-f", f"fieldId={field_id}",
         "-f", f"optionId={option_id}"],
        capture_output=True, text=True
    )
    return r.returncode == 0, r.stderr.strip() if r.returncode != 0 else ""

# Load all option maps
print("Loading field options...")
options = {name: get_field_options(fid) for name, fid in FIELD_IDS.items()}
for name, opts in options.items():
    print(f"  {name}: {list(opts.keys())}")

print()
for ep in EPIC_ITEMS:
    print(f"{ep['epic']} (#{ep['issue']}) item={ep['item_id']}")
    for field_name, val in [("Priority", ep["priority"]), ("Phase", ep["phase"]),
                             ("Component", ep["component"]), ("Layer", ep["layer"])]:
        if val is None:
            continue
        opt_id = options[field_name].get(val)
        if not opt_id:
            print(f"  {field_name} '{val}' not found in options — skip")
            continue
        ok, err = set_field(ep["item_id"], FIELD_IDS[field_name], opt_id)
        print(f"  {field_name} → {val}: {'OK' if ok else f'FAIL {err}'}")

print("\nDone.")
