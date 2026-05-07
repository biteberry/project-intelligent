"""add_epics_to_board.py — adds Epic issues #22-26 to the project board"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "biteberry/project-intelligent"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

mutation = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: { projectId: $projectId contentId: $contentId }) {
    item { id }
  }
}
"""

for num in [22, 23, 24, 25, 26]:
    r = subprocess.run(
        [GH, "issue", "view", str(num), "--repo", REPO, "--json", "id"],
        capture_output=True, text=True)
    nid = json.loads(r.stdout)["id"]
    print(f"#{num} node_id: {nid}")

    r2 = subprocess.run(
        [GH, "api", "graphql",
         "-f", f"query={mutation}",
         "-f", f"projectId={PROJECT_ID}",
         "-f", f"contentId={nid}"],
        capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"  FAIL: {r2.stderr.strip()}")
        continue
    data = json.loads(r2.stdout)
    item = data.get("data", {}).get("addProjectV2ItemById", {}).get("item", {})
    item_id = item.get("id", "NO_ID")
    print(f"  Board item ID: {item_id}")

print("Done")
