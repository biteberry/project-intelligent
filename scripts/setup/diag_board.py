"""Diagnose why board only shows 21 items"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

query = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100) {
        totalCount
        nodes {
          id
          type
          content {
            __typename
            ... on Issue {
              number
              title
            }
          }
        }
      }
    }
  }
}
"""

r = subprocess.run(
    [GH, "api", "graphql", "-f", f"query={query}", "-f", f"projectId={PROJECT_ID}"],
    capture_output=True, text=True
)
if r.returncode != 0:
    print("Error:", r.stderr)
else:
    data = json.loads(r.stdout)
    items = data["data"]["node"]["items"]
    print(f"totalCount: {items['totalCount']}")
    print(f"nodes returned: {len(items['nodes'])}")
    for item in items["nodes"]:
        ctype = item.get("content", {}).get("__typename", "NONE")
        num = item.get("content", {}).get("number", "?")
        title = item.get("content", {}).get("title", "?")[:40]
        print(f"  {item['id']} type={item.get('type')} content={ctype} #{num} {title}")
