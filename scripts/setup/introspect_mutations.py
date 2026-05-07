"""introspect_mutations.py - find all ProjectV2 view/field mutations in GitHub schema"""
import subprocess, json

GH = r"C:\Program Files\GitHub CLI\gh.exe"

query = "{ __type(name: \"Mutation\") { fields { name } } }"

r = subprocess.run([GH, "api", "graphql", "-f", f"query={query}"],
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode != 0:
    print("Error:", r.stderr)
    exit(1)

d = json.loads(r.stdout)
all_mutations = [f["name"] for f in d["data"]["__type"]["fields"]]
project_view_mutations = [n for n in all_mutations if "roject" in n and ("iew" in n or "ield" in n)]
print("Project + View/Field mutations:")
for n in sorted(project_view_mutations):
    print(" ", n)
