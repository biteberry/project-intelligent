"""Check archived items and unarchive Epic issues"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"

query = """query($pid: ID!) { node(id: $pid) { ... on ProjectV2 { items(first: 100, includeArchived: true) { totalCount nodes { id isArchived content { __typename ... on Issue { number title } } } } } } }"""

r = subprocess.run(
    [GH, "api", "graphql", "-f", f"query={query}", "-f", f"pid={PROJECT_ID}"],
    capture_output=True, text=True
)
print("returncode:", r.returncode)
print("stderr:", r.stderr[:300] if r.stderr else "none")
if r.returncode != 0:
    # try without includeArchived
    query2 = """query($pid: ID!) { node(id: $pid) { ... on ProjectV2 { items(first: 100) { totalCount } } } }"""
    r2 = subprocess.run([GH, "api", "graphql", "-f", f"query={query2}", "-f", f"pid={PROJECT_ID}"], capture_output=True, text=True)
    print("Without includeArchived:", r2.stdout[:200])
else:
    d = json.loads(r.stdout)
    items = d["data"]["node"]["items"]
    print(f"Total (incl archived): {items['totalCount']}")
    archived = [i for i in items["nodes"] if i.get("isArchived")]
    print(f"Archived: {len(archived)}")
    for i in archived:
        print(f"  #{i.get('content',{}).get('number','?')} {i['id']}")
