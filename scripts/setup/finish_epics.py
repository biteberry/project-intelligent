"""
finish_epics.py  — one-time runner
- Links #2 to already-created EPIC-001 (#22)
- Creates EPIC-002 to EPIC-005 with correct milestones
Run: python scripts/setup/finish_epics.py
"""
import subprocess, json, os, tempfile, time, sys

# Add parent so we can reuse helpers from create_github_epics
sys.path.insert(0, os.path.dirname(__file__))
from create_github_epics import (
    GH, REPO, OWNER, EPICS,
    get_issue_db_id, add_sub_issue, add_to_project_board, create_epic_issue, run_gh
)

def main():
    # ── Step 1: Finish EPIC-001 (#22) — link #2 (already linked #1) ──────────
    print("=== Finishing EPIC-001 (#22) ===")
    db2 = get_issue_db_id(2)
    ok = add_sub_issue(22, db2)
    print(f"  #{2} → {'OK' if ok else 'FAIL'}")

    # ── Step 2: Gather DB IDs for all features (needed for EPIC-002..005) ──────
    print("\nFetching DB IDs for features #3-#21 ...")
    needed = [3,4,5,6,7,8,9,10,18, 11,12,13,14, 15,16,17, 19,20,21]
    db_ids = {}
    for num in needed:
        did = get_issue_db_id(num)
        db_ids[num] = did
        print(f"  #{num} → {did}")

    # ── Step 3: Create EPIC-002 .. EPIC-005 ──────────────────────────────────
    epic_numbers = {}
    for epic in EPICS[1:]:   # skip EPIC-001 (already created as #22)
        print(f"\n--- {epic['id']} ---")
        epic_num, _ = create_epic_issue(epic)
        if epic_num is None:
            continue
        epic_numbers[epic["id"]] = epic_num
        time.sleep(1)

        ok = add_to_project_board(epic_num)
        print(f"  Board add → {'OK' if ok else 'FAIL'}")
        time.sleep(0.5)

        print(f"  Linking sub-issues: {epic['features']}")
        for feat_num in epic["features"]:
            did = db_ids.get(feat_num)
            if not did:
                print(f"    #{feat_num} → SKIP")
                continue
            ok = add_sub_issue(epic_num, did)
            print(f"    #{feat_num} → {'OK' if ok else 'FAIL'}")
            time.sleep(0.3)

    print("\n=== Summary ===")
    print("  EPIC-001 → #22 (pre-existing)")
    for eid, enum in epic_numbers.items():
        print(f"  {eid} → #{enum}")

if __name__ == "__main__":
    main()
