"""
create_phase0_stories_tasks.py
Creates all Phase 0 Stories and Tasks, links them as sub-issues,
and adds them to the PROJECT_INTELLIGENT board.

Hierarchy:
  EPIC-001 #22
    FEATURE-001 #1  (Architecture Phase Closure)
      STORY-001  Phase 0 Gate Audit Document
        TASK-001   Review all 14 architecture docs for completeness
        TASK-002   Review 9 analysis docs
        TASK-003   Review 5 ADRs
        TASK-004   PRD v1.0 sign-off with stakeholder
        TASK-005   Create phase-0-gate-audit.md document
      STORY-002  configs/position_sizing.yaml
        TASK-006   Create configs/position_sizing.yaml
        TASK-007   Commit and merge to main
    FEATURE-002 #2  (Environment Provisioning)
      STORY-003  Reproducible Dev Environment
        TASK-008   Create requirements.txt (pinned versions)
        TASK-009   Write README quickstart (clone → run)
        TASK-010   Verify clean-install on bare Python 3.11
      STORY-004  GitHub Project Setup Complete
        TASK-011   Verify all labels, milestones, Epics, Features on board
        TASK-012   Create Phase 0 Stories and Tasks (this issue)
        TASK-013   Document workflow in github_project_setup_guide.md

Usage: python scripts/setup/create_phase0_stories_tasks.py
"""

import subprocess
import json
import os
import tempfile
import time

GH    = r"C:\Program Files\GitHub CLI\gh.exe"
REPO  = "biteberry/project-intelligent"
PROJECT_ID = "PVT_kwDOD4jskM4BW8Ri"
PROJECT_NUM = 2
OWNER = "biteberry"

M0 = "M0: Phase 0 - Architecture and Sign-Off"
PHASE0_LABELS = ["phase:0-setup", "priority:critical"]

# ─── Issue definitions ────────────────────────────────────────────────────────
# Each story/task: title, labels, body, parent_issue_num (for sub-issue link)

STORIES = [
    {
        "key":    "STORY-001",
        "title":  "[STORY] Phase 0 Gate Audit Document",
        "labels": ["type:story", "phase:0-setup", "comp:docs", "priority:critical"],
        "parent": 1,  # FEATURE-001
        "body": """## User Story
As a **platform owner**, I need a signed-off Phase 0 gate audit document so that Phase 1 work can begin under Guardrail G4.

## Parent Feature
Part of #1

## Child Tasks
_Updated when tasks are created_

## Acceptance Criteria
- [ ] All 14 architecture docs reviewed and gaps noted
- [ ] All 9 analysis docs reviewed
- [ ] All 5 ADRs reviewed and rationale confirmed
- [ ] PRD v1.0 marked as approved
- [ ] `docs/project-management/phase-0-gate-audit.md` merged to main

## Architecture Reference
docs/architecture/ (all 14 files)
docs/analysis/ (all 9 files)
docs/adr/ (all 5 files)
docs/PRD_v1.0.md

## Notes
Per doc 07 Guardrail G4: no phase begins before previous phase exit criteria are fully documented and signed off.
""",
    },
    {
        "key":    "STORY-002",
        "title":  "[STORY] Position Sizing Configuration",
        "labels": ["type:story", "phase:0-setup", "comp:infra", "priority:critical"],
        "parent": 1,  # FEATURE-001
        "body": """## User Story
As a **platform owner**, I need `configs/position_sizing.yaml` committed to main so that all pipeline components have a single source of truth for risk parameters.

## Parent Feature
Part of #1

## Child Tasks
_Updated when tasks are created_

## Acceptance Criteria
- [ ] `configs/position_sizing.yaml` exists at repo root
- [ ] Contains: `risk_pct_per_trade`, `max_position_pct`, `max_open_positions`, `max_sector_exposure_pct`
- [ ] Values align with PRD §2 risk rules
- [ ] Merged to main branch

## Architecture Reference
docs/architecture/04_position_sizing.md (or equivalent)
PRD §2 — Risk management parameters

## Notes
Values: risk_pct_per_trade: 1.0, max_position_pct: 20, max_open_positions: 5, max_sector_exposure_pct: 40
""",
    },
    {
        "key":    "STORY-003",
        "title":  "[STORY] Reproducible Dev Environment",
        "labels": ["type:story", "phase:0-setup", "comp:infra", "priority:critical"],
        "parent": 2,  # FEATURE-002
        "body": """## User Story
As a **developer**, I need a reproducible Python environment so that any contributor can clone the repo and run the pipeline with a single setup command.

## Parent Feature
Part of #2

## Child Tasks
_Updated when tasks are created_

## Acceptance Criteria
- [ ] `requirements.txt` with all pinned versions exists at repo root
- [ ] README has a "Quickstart" section with clone → install → run steps
- [ ] Clean install verified on bare Python 3.11 (no implicit deps)

## Architecture Reference
docs/architecture/02_environment_setup.md (or equivalent)

## Notes
Target: Python 3.11. AWS free-tier only — no paid services in Phase 0.
""",
    },
    {
        "key":    "STORY-004",
        "title":  "[STORY] GitHub Project Setup Complete",
        "labels": ["type:story", "phase:0-setup", "comp:docs", "priority:critical"],
        "parent": 2,  # FEATURE-002
        "body": """## User Story
As a **platform owner**, I need the GitHub project board fully configured so that all work is trackable from Epic → Feature → Story → Task.

## Parent Feature
Part of #2

## Child Tasks
_Updated when tasks are created_

## Acceptance Criteria
- [ ] 31 labels, 8 milestones, 5 Epics, 21 Features all on board
- [ ] Phase 0 Stories and Tasks created and linked
- [ ] `docs/project-management/github_project_setup_guide.md` updated

## Architecture Reference
docs/project-management/github_project_setup_guide.md

## Notes
Board: https://github.com/users/biteberry/projects/2
""",
    },
]

TASKS = [
    # ── STORY-001 tasks ──────────────────────────────────────────────────────
    {
        "key":           "TASK-001",
        "title":         "[TASK] Review all 14 architecture docs for completeness",
        "story_key":     "STORY-001",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Open each of the 14 architecture documents in `docs/architecture/` and verify:
- No placeholder sections left blank
- Diagrams or table descriptions are present where required
- India-first context is correct (NSE/BSE primary, US secondary via market_context)
- Any gaps are noted in the phase-0-gate-audit.md

## Parent Story
Part of <!-- STORY-001 issue number -->

## Acceptance Criteria
- [ ] All 14 docs read top-to-bottom
- [ ] Gap list captured in gate audit doc
- [ ] No "TODO" or placeholder text remains without a linked issue

## Files to Create or Modify
- `docs/project-management/phase-0-gate-audit.md`

## Test Approach
Manual review. Gate audit doc updated with findings.
""",
    },
    {
        "key":           "TASK-002",
        "title":         "[TASK] Review all 9 analysis docs",
        "story_key":     "STORY-001",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Review all 9 documents in `docs/analysis/`:
- Confirm analysis conclusions are referenced in architecture docs
- Note any analysis that contradicts current design
- Capture findings in phase-0-gate-audit.md

## Parent Story
Part of <!-- STORY-001 issue number -->

## Acceptance Criteria
- [ ] All 9 analysis docs reviewed
- [ ] Cross-references to architecture docs verified
- [ ] Findings captured in gate audit doc

## Files to Create or Modify
- `docs/project-management/phase-0-gate-audit.md`

## Test Approach
Manual review.
""",
    },
    {
        "key":           "TASK-003",
        "title":         "[TASK] Review all 5 ADRs and confirm rationale",
        "story_key":     "STORY-001",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Review all 5 Architecture Decision Records in `docs/adr/`:
- Confirm decision status (Accepted / Superseded)
- Verify consequences section is accurate given current design
- Flag any ADR whose decision may need revisiting

## Parent Story
Part of <!-- STORY-001 issue number -->

## Acceptance Criteria
- [ ] All 5 ADRs reviewed
- [ ] Each ADR marked with current status
- [ ] Any contested decision has a linked follow-up issue

## Files to Create or Modify
- `docs/adr/` (status updates if needed)
- `docs/project-management/phase-0-gate-audit.md`

## Test Approach
Manual review.
""",
    },
    {
        "key":           "TASK-004",
        "title":         "[TASK] PRD v1.0 sign-off",
        "story_key":     "STORY-001",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Mark `docs/PRD_v1.0.md` as formally signed off:
- Add a `## Sign-Off` section with date and approver
- Commit to main

## Parent Story
Part of <!-- STORY-001 issue number -->

## Acceptance Criteria
- [ ] Sign-off section added to PRD
- [ ] Committed to main branch
- [ ] Referenced in phase-0-gate-audit.md

## Files to Create or Modify
- `docs/PRD_v1.0.md`

## Test Approach
Git log shows commit with sign-off section.
""",
    },
    {
        "key":           "TASK-005",
        "title":         "[TASK] Create docs/project-management/phase-0-gate-audit.md",
        "story_key":     "STORY-001",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Create the formal Phase 0 exit gate document:
- Section per review area: Architecture docs, Analysis docs, ADRs, PRD
- Exit criteria checklist (from FEATURE-001 acceptance criteria)
- Sign-off block with date

## Parent Story
Part of <!-- STORY-001 issue number -->

## Acceptance Criteria
- [ ] File created at `docs/project-management/phase-0-gate-audit.md`
- [ ] All checklist items completed or linked to a follow-up issue
- [ ] Merged to main

## Files to Create or Modify
- `docs/project-management/phase-0-gate-audit.md`

## Test Approach
File exists in main branch, all checkboxes completed.
""",
    },
    # ── STORY-002 tasks ──────────────────────────────────────────────────────
    {
        "key":           "TASK-006",
        "title":         "[TASK] Create configs/position_sizing.yaml",
        "story_key":     "STORY-002",
        "labels":        ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "body": """## What needs to be done
Create `configs/position_sizing.yaml` with risk parameters from PRD §2:

```yaml
# Position sizing and risk management parameters
risk_pct_per_trade: 1.0       # % of portfolio risked per trade
max_position_pct: 20          # max % of portfolio in single stock
max_open_positions: 5         # max concurrent open positions
max_sector_exposure_pct: 40   # max % of portfolio in one sector
```

## Parent Story
Part of <!-- STORY-002 issue number -->

## Acceptance Criteria
- [ ] File exists at `configs/position_sizing.yaml`
- [ ] All 4 required keys present with correct values
- [ ] YAML is valid (no parse errors)

## Files to Create or Modify
- `configs/position_sizing.yaml`

## Test Approach
`python -c "import yaml; yaml.safe_load(open('configs/position_sizing.yaml'))"` succeeds.
""",
    },
    {
        "key":           "TASK-007",
        "title":         "[TASK] Commit configs/position_sizing.yaml to main",
        "story_key":     "STORY-002",
        "labels":        ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "body": """## What needs to be done
After TASK-006 is complete:
- `git add configs/position_sizing.yaml`
- `git commit -m "feat: add position sizing config (Phase 0)"`
- `git push`
- Close STORY-002 and TASK-006

## Parent Story
Part of <!-- STORY-002 issue number -->

## Acceptance Criteria
- [ ] File in main branch on GitHub
- [ ] Commit message follows conventional commits format
- [ ] STORY-002 closed

## Files to Create or Modify
- `configs/position_sizing.yaml`

## Test Approach
File visible in GitHub repo main branch.
""",
    },
    # ── STORY-003 tasks ──────────────────────────────────────────────────────
    {
        "key":           "TASK-008",
        "title":         "[TASK] Create requirements.txt with pinned versions",
        "story_key":     "STORY-003",
        "labels":        ["type:task", "phase:0-setup", "comp:infra", "priority:critical"],
        "body": """## What needs to be done
Create `requirements.txt` at the repo root with all Python dependencies pinned:
- pandas, numpy, scipy (data processing)
- boto3 (AWS DynamoDB / S3)
- requests, httpx (API calls)
- pyyaml (config loading)
- pytest (testing)
Include a comment header with Python version requirement.

## Parent Story
Part of <!-- STORY-003 issue number -->

## Acceptance Criteria
- [ ] `requirements.txt` exists at repo root
- [ ] All packages pinned to exact versions (`==`)
- [ ] `pip install -r requirements.txt` succeeds on clean Python 3.11

## Files to Create or Modify
- `requirements.txt`

## Test Approach
`pip install -r requirements.txt` exits with code 0 on bare venv.
""",
    },
    {
        "key":           "TASK-009",
        "title":         "[TASK] Write README quickstart section",
        "story_key":     "STORY-003",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Add a **Quickstart** section to README.md:
```
## Quickstart
1. `git clone https://github.com/biteberry/project-intelligent`
2. `cd project-intelligent`
3. `python -m venv .venv && .venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. `cp configs/position_sizing.yaml.example configs/position_sizing.yaml`  (if applicable)
```
Include prerequisites: Python 3.11, git, AWS credentials (optional for Phase 0).

## Parent Story
Part of <!-- STORY-003 issue number -->

## Acceptance Criteria
- [ ] README.md has Quickstart section
- [ ] Steps are copy-paste executable on Windows and Linux
- [ ] Merged to main

## Files to Create or Modify
- `README.md`

## Test Approach
Follow the steps on a fresh machine / clean directory.
""",
    },
    {
        "key":           "TASK-010",
        "title":         "[TASK] Verify clean install on bare Python 3.11",
        "story_key":     "STORY-003",
        "labels":        ["type:task", "phase:0-setup", "comp:infra", "priority:high"],
        "body": """## What needs to be done
Create a fresh virtual environment, install from requirements.txt, and run any
existing scripts to confirm no missing imports:
```
python -m venv .venv_test
.venv_test\\Scripts\\activate
pip install -r requirements.txt
python -c "import pandas, boto3, yaml, requests; print('OK')"
```

## Parent Story
Part of <!-- STORY-003 issue number -->

## Acceptance Criteria
- [ ] All imports succeed with no errors
- [ ] If failures found, requirements.txt is updated and retested

## Files to Create or Modify
- `requirements.txt` (if fixes needed)

## Test Approach
Terminal output shows `OK` with exit code 0.
""",
    },
    # ── STORY-004 tasks ──────────────────────────────────────────────────────
    {
        "key":           "TASK-011",
        "title":         "[TASK] Verify all labels, milestones, Epics, Features on board",
        "story_key":     "STORY-004",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Open the PROJECT_INTELLIGENT board and verify:
- 32 labels exist (31 original + type:epic)
- 8 milestones (M0–M7) exist with correct due dates
- 5 Epics (#22–#26) visible with Priority/Phase/Component set
- 21 Features (#1–#21) visible with all fields set

## Parent Story
Part of <!-- STORY-004 issue number -->

## Acceptance Criteria
- [ ] Board shows 26+ items (21 Features + 5 Epics)
- [ ] No missing fields on any Epic or Feature
- [ ] All labels present in https://github.com/biteberry/project-intelligent/labels

## Files to Create or Modify
None (verification only)

## Test Approach
Visual inspection of board and labels page.
""",
    },
    {
        "key":           "TASK-012",
        "title":         "[TASK] Create Phase 0 Stories and Tasks on board",
        "story_key":     "STORY-004",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:critical"],
        "body": """## What needs to be done
Run `scripts/setup/create_phase0_stories_tasks.py` to create all
Phase 0 Stories and Tasks and link them as sub-issues.

## Parent Story
Part of <!-- STORY-004 issue number -->

## Acceptance Criteria
- [ ] 4 Stories created and linked to FEATURE-001 / FEATURE-002
- [ ] 13 Tasks created and linked to their parent Stories
- [ ] All visible on project board with correct fields

## Files to Create or Modify
- `scripts/setup/create_phase0_stories_tasks.py`

## Test Approach
Board shows Stories and Tasks under Phase 0 milestone.
""",
    },
    {
        "key":           "TASK-013",
        "title":         "[TASK] Update github_project_setup_guide.md with Story/Task workflow",
        "story_key":     "STORY-004",
        "labels":        ["type:task", "phase:0-setup", "comp:docs", "priority:high"],
        "body": """## What needs to be done
Add a section to `docs/project-management/github_project_setup_guide.md` documenting:
- The 4-tier hierarchy (Epic → Feature → Story → Task)
- How to create a new Story using the issue template
- How to link Stories as sub-issues of Features
- How to create Tasks and link to Stories

## Parent Story
Part of <!-- STORY-004 issue number -->

## Acceptance Criteria
- [ ] Section added to guide
- [ ] Sub-issue linking steps documented with gh CLI commands
- [ ] Merged to main

## Files to Create or Modify
- `docs/project-management/github_project_setup_guide.md`

## Test Approach
Guide is readable and steps are actionable.
""",
    },
]


def run_gh(*args):
    return subprocess.run([GH] + list(args), capture_output=True, text=True)


def create_issue(title, labels, milestone, body):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        tmp = f.name
    try:
        cmd = [GH, "issue", "create", "--repo", REPO,
               "--title", title, "--body-file", tmp,
               "--milestone", milestone]
        for label in labels:
            cmd += ["--label", label]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr.strip()[:120]}")
            return None
        url = result.stdout.strip().split("\n")[-1].strip()
        num = int(url.rstrip("/").split("/")[-1])
        return num
    finally:
        os.unlink(tmp)


def get_issue_db_id(issue_number):
    r = run_gh("api", f"repos/{REPO}/issues/{issue_number}", "--jq", ".id")
    return int(r.stdout.strip()) if r.returncode == 0 else None


def get_issue_node_id(issue_number):
    r = run_gh("issue", "view", str(issue_number), "--repo", REPO, "--json", "id")
    return json.loads(r.stdout)["id"] if r.returncode == 0 else None


def add_sub_issue(parent_number, child_db_id):
    r = run_gh("api", f"repos/{REPO}/issues/{parent_number}/sub_issues",
               "--method", "POST", "--field", f"sub_issue_id={child_db_id}")
    return r.returncode == 0


def add_to_board(issue_number):
    node_id = get_issue_node_id(issue_number)
    if not node_id:
        return False
    mutation = """mutation($pid: ID!, $cid: ID!) { addProjectV2ItemById(input:{projectId:$pid contentId:$cid}){item{id}}}"""
    r = subprocess.run(
        [GH, "api", "graphql",
         "-f", f"query={mutation}",
         "-f", f"pid={PROJECT_ID}",
         "-f", f"cid={node_id}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return False
    data = json.loads(r.stdout)
    return bool(data.get("data", {}).get("addProjectV2ItemById", {}).get("item"))


def set_board_fields(item_id, priority_opt, phase_opt, comp_opt=None):
    """Set Priority, Phase (and optionally Component) on a board item."""
    field_map = {
        "Priority":  ("PVTSSF_lADOD4jskM4BW8RizhSMqPA", priority_opt),
        "Phase":     ("PVTSSF_lADOD4jskM4BW8RizhSMsc8", phase_opt),
    }
    if comp_opt:
        field_map["Component"] = ("PVTSSF_lADOD4jskM4BW8RizhSMtC8", comp_opt)

    mutation = """
    mutation($pid:ID!,$iid:ID!,$fid:ID!,$oid:String!){
      updateProjectV2ItemFieldValue(input:{projectId:$pid itemId:$iid fieldId:$fid value:{singleSelectOptionId:$oid}}){
        projectV2Item{id}}}"""

    # First fetch option IDs
    q = """query($pid:ID!){node(id:$pid){...on ProjectV2{fields(first:30){nodes{...on ProjectV2SingleSelectField{id options{id name}}}}}}}"""
    r = subprocess.run([GH, "api", "graphql", "-f", f"query={q}", "-f", f"pid={PROJECT_ID}"], capture_output=True, text=True)
    opts_by_field = {}
    for field in json.loads(r.stdout)["data"]["node"]["fields"]["nodes"]:
        if field.get("options"):
            for opt in field["options"]:
                opts_by_field.setdefault(field["id"], {})[opt["name"]] = opt["id"]

    results = {}
    for fname, (fid, val) in field_map.items():
        opt_id = opts_by_field.get(fid, {}).get(val)
        if not opt_id:
            results[fname] = "SKIP"
            continue
        r2 = subprocess.run(
            [GH, "api", "graphql",
             "-f", f"query={mutation}",
             "-f", f"pid={PROJECT_ID}",
             "-f", f"iid={item_id}",
             "-f", f"fid={fid}",
             "-f", f"oid={opt_id}"],
            capture_output=True, text=True)
        results[fname] = "OK" if r2.returncode == 0 else "FAIL"
    return results


def get_board_item_id(issue_number):
    node_id = get_issue_node_id(issue_number)
    mutation = """mutation($pid:ID!,$cid:ID!){addProjectV2ItemById(input:{projectId:$pid contentId:$cid}){item{id}}}"""
    r = subprocess.run(
        [GH, "api", "graphql",
         "-f", f"query={mutation}",
         "-f", f"pid={PROJECT_ID}",
         "-f", f"cid={node_id}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    data = json.loads(r.stdout)
    return data.get("data", {}).get("addProjectV2ItemById", {}).get("item", {}).get("id")


def update_task_body_with_story_num(task, story_num):
    """Replace <!-- STORY-XXX issue number --> with actual story number."""
    return task["body"].replace(f"<!-- {task['story_key']} issue number -->", str(story_num))


def main():
    print("=== Creating Phase 0 Stories ===\n")

    story_nums   = {}   # key → issue number
    story_db_ids = {}   # issue number → db id

    for story in STORIES:
        print(f"Creating {story['key']}: {story['title'][:55]}")
        num = create_issue(story["title"], story["labels"], M0, story["body"])
        if num is None:
            print("  SKIPPED — creation failed")
            continue
        story_nums[story["key"]] = num
        print(f"  → #{num}")
        time.sleep(0.8)

        # Link as sub-issue of parent Feature
        db_id = get_issue_db_id(num)
        story_db_ids[num] = db_id
        ok = add_sub_issue(story["parent"], db_id)
        print(f"  sub-issue of #{story['parent']}: {'OK' if ok else 'FAIL'}")
        time.sleep(0.5)

        # Add to board + set fields
        item_id = get_board_item_id(num)
        if item_id:
            fields = set_board_fields(item_id, "P0", "Phase 0", "Docs" if "comp:docs" in story["labels"] else "Infra")
            print(f"  board fields: {fields}")
        time.sleep(0.4)

    print("\n=== Creating Phase 0 Tasks ===\n")

    task_nums = {}   # key → issue number

    for task in TASKS:
        story_num = story_nums.get(task["story_key"])
        if story_num is None:
            print(f"  SKIP {task['key']} — parent story not created")
            continue

        # Replace placeholder with actual story issue number
        body = update_task_body_with_story_num(task, story_num)

        print(f"Creating {task['key']}: {task['title'][:55]}")
        num = create_issue(task["title"], task["labels"], M0, body)
        if num is None:
            print("  SKIPPED — creation failed")
            continue
        task_nums[task["key"]] = num
        print(f"  → #{num}")
        time.sleep(0.8)

        # Link as sub-issue of parent Story
        db_id = get_issue_db_id(num)
        ok = add_sub_issue(story_num, db_id)
        print(f"  sub-issue of #{story_num}: {'OK' if ok else 'FAIL'}")
        time.sleep(0.5)

        # Add to board + set fields
        item_id = get_board_item_id(num)
        if item_id:
            pri = "P0" if "priority:critical" in task["labels"] else "P1"
            fields = set_board_fields(item_id, pri, "Phase 0", "Docs" if "comp:docs" in task["labels"] else "Infra")
            print(f"  board fields: {fields}")
        time.sleep(0.4)

    print("\n=== Summary ===")
    print("\nStories:")
    for key, num in story_nums.items():
        print(f"  {key} → #{num}")
    print("\nTasks:")
    for key, num in task_nums.items():
        print(f"  {key} → #{num}")
    print(f"\nTotal new issues: {len(story_nums) + len(task_nums)}")
    print(f"Board: https://github.com/users/{OWNER}/projects/{PROJECT_NUM}")


if __name__ == "__main__":
    main()
