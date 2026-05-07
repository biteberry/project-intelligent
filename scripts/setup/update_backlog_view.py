"""update_backlog_view.py — Groups 'Prioritized backlog' view by Level field"""
import subprocess, json

GH         = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"
OWNER      = "biteberry"

# IDs from create_view_only.py output
BACKLOG_VIEW_ID = "PVTV_lADOD4jskM4BW8RizgKQJkU"   # #1 Prioritized backlog
LEVEL_FIELD_ID  = "PVTSSF_lADOD4jskM4BW8RizhSNAoA"  # Level (Epic/Feature/Story/Task)


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


# Update the "Prioritized backlog" view to group by Level
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
    "vid": BACKLOG_VIEW_ID,
    "fid": LEVEL_FIELD_ID,
})

if data:
    v = data["data"]["updateProjectV2View"]["projectV2View"]
    print(f"OK — view #{v['number']} '{v['name']}' now grouped by Level")
    print(f"\nBoard: https://github.com/users/{OWNER}/projects/2")
    print("""
View now shows 4 groups:
  [Epic]    #22-#26   — click ▶ to expand to Features
  [Feature] #1-#21    — click ▶ to expand to Stories
  [Story]   #27-#30   — click ▶ to expand to Tasks
  [Task]    #31-#43   — leaf nodes
""")
else:
    print("FAIL:", err)
