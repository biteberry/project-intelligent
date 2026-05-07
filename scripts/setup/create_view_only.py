"""create_view_only.py — creates the Hierarchy view (Step 3 only)"""
import subprocess, json

GH         = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"
OWNER      = "biteberry"
# Level field created in previous run
LEVEL_FIELD_ID = "PVTSSF_lADOD4jskM4BW8RizhSNAoA"


def gh_gql(query, variables=None):
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


# 1. List existing views
q = """
query($pid: ID!) {
  node(id: $pid) {
    ... on ProjectV2 {
      views(first: 20) { nodes { id number name } }
    }
  }
}
"""
data, err = gh_gql(q, {"pid": PROJECT_ID})
if not data:
    print("ERROR listing views:", err)
    exit(1)

views = data["data"]["node"]["views"]["nodes"]
print("Existing views:")
for v in views:
    print(f"  #{v['number']} {v['name']} ({v['id']})")

# 2. Find or create Hierarchy view
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
        print("ERROR creating view:", err)
        exit(1)
    existing = data["data"]["createProjectV2View"]["projectV2View"]
    print(f"\nCreated 'Hierarchy' view #{existing['number']} ({existing['id']})")
else:
    print(f"\nReusing view #{existing['number']}: {existing['name']}")

# 3. Group by Level field
mutation = """
mutation($pid: ID!, $vid: ID!, $fid: String!) {
  updateProjectV2View(input: {
    projectId: $pid
    viewId: $vid
    groupByFields: [$fid]
  }) {
    projectV2View { id number name }
  }
}
"""
data, err = gh_gql(mutation, {
    "pid": PROJECT_ID,
    "vid": existing["id"],
    "fid": LEVEL_FIELD_ID
})
if data:
    v = data["data"]["updateProjectV2View"]["projectV2View"]
    print(f"Grouped by 'Level' field OK → view #{v['number']} '{v['name']}'")
    print(f"\nHierarchy view: https://github.com/users/{OWNER}/projects/2/views/{v['number']}")
else:
    print("ERROR setting groupBy:", err)
