"""Check if Epic items are archived on the project board, then unarchive them"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

# Query including archived items
query = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100, includeArchived: true) {
        totalCount
        nodes {
          id
          isArchived
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
data = json.loads(r.stdout)
items = data["data"]["node"]["items"]
print(f"totalCount (incl archived): {items['totalCount']}")

archived = [i for i in items["nodes"] if i.get("isArchived")]
print(f"Archived items: {len(archived)}")
for i in archived:
    num = i.get("content", {}).get("number", "?")
    title = i.get("content", {}).get("title", "?")[:50]
    print(f"  {i['id']}  #{num}  {title}")

# Unarchive all archived items
if archived:
    print("\nUnarchiving...")
    unarchive_mutation = """
    mutation($projectId: ID!, $itemId: ID!) {
      unarchiveProjectV2Item(input: { projectId: $projectId itemId: $itemId }) {
        item { id isArchived }
      }
    }
    """
    for item in archived:
        r2 = subprocess.run(
            [GH, "api", "graphql",
             "-f", f"query={unarchive_mutation}",
             "-f", f"projectId={PROJECT_ID}",
             "-f", f"itemId={item['id']}"],
            capture_output=True, text=True
        )
        if r2.returncode == 0:
            result = json.loads(r2.stdout)
            is_archived = result.get("data", {}).get("unarchiveProjectV2Item", {}).get("item", {}).get("isArchived", "?")
            num = item.get("content", {}).get("number", "?")
            print(f"  #{num}: isArchived={is_archived}")
        else:
            print(f"  #{item.get('content', {}).get('number', '?')}: FAIL {r2.stderr.strip()}")
