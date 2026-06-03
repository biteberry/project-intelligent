"""
create_phase1_ingestion_stories_tasks.py
Creates Phase 1 Ingestion Stories and Tasks for Features 4-10, 18.
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

M2 = "M2: Phase 1.2 - Data Ingestion Layer"

STORIES = [
    # FEATURE 4: Delivery Pct
    {
        "key": "STORY-010", "title": "[STORY] NSE bhav copy CSV downloader",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:critical", "layer:bronze"],
        "parent": 4,
        "body": "## User Story\nAs a data engineer, I need to download the daily NSE bhav copy CSV so that delivery percentages can be extracted.\n\n## Parent Feature\nPart of #4\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Downloads from archives.nseindia.com using DDMMYYYY pattern\n- [ ] Handles zip extraction\n- [ ] Returns structured dataframe"
    },
    {
        "key": "STORY-011", "title": "[STORY] Delivery pct Bronze writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:critical", "layer:bronze"],
        "parent": 4,
        "body": "## User Story\nAs a data engineer, I need to write delivery percentages to the Bronze S3 bucket partitioned by date.\n\n## Parent Feature\nPart of #4\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Extracts delivery % column\n- [ ] Converts to Parquet\n- [ ] Writes to Bronze S3"
    },
    {
        "key": "STORY-012", "title": "[STORY] Market holiday detection logic",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:critical", "layer:bronze"],
        "parent": 4,
        "body": "## User Story\nAs an operator, I need the pipeline to detect market holidays so that missing bhav copy files do not trigger false failure alerts.\n\n## Parent Feature\nPart of #4\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Detects NSE holidays\n- [ ] Suppresses alerts if file is missing on a legitimate holiday"
    },
    
    # FEATURE 5: Fundamentals
    {
        "key": "STORY-013", "title": "[STORY] yfinance fundamentals fetcher",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 5,
        "body": "## User Story\nAs a data engineer, I need to fetch fundamental data from yfinance so it can be stored for scoring.\n\n## Parent Feature\nPart of #5\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Calls .info, .financials, .balance_sheet, .cashflow\n- [ ] Maps to standard schema"
    },
    {
        "key": "STORY-014", "title": "[STORY] Bronze fundamentals parquet writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 5,
        "body": "## User Story\nAs a data engineer, I need to write quarterly fundamental snapshots to Bronze S3.\n\n## Parent Feature\nPart of #5\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes to Bronze S3 partitioned by source and fetch_date"
    },
    {
        "key": "STORY-015", "title": "[STORY] Incremental fundamentals re-fetch trigger logic",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 5,
        "body": "## User Story\nAs a data engineer, I need to trigger targeted refetches when an earnings date has passed to keep fundamentals fresh.\n\n## Parent Feature\nPart of #5\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Detects passed earnings dates\n- [ ] Triggers targeted refresh"
    },
    
    # FEATURE 6: India Macro Data
    {
        "key": "STORY-016", "title": "[STORY] RBI Repo rate web scraper",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 6,
        "body": "## User Story\nAs a data engineer, I need to scrape the RBI repo rate weekly to provide macro context to the model.\n\n## Parent Feature\nPart of #6\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Scrapes RBI publications view\n- [ ] Extracts policy rates"
    },
    {
        "key": "STORY-017", "title": "[STORY] India 10Y/2Y bond yield fetcher",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 6,
        "body": "## User Story\nAs a data engineer, I need to fetch India bond yields to capture the macro interest rate environment.\n\n## Parent Feature\nPart of #6\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Pulls 10Y and 2Y yields from reliable free source"
    },
    {
        "key": "STORY-018", "title": "[STORY] Bronze macro data writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 6,
        "body": "## User Story\nAs a data engineer, I need to write macro data to Bronze S3.\n\n## Parent Feature\nPart of #6\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes macro data to Bronze S3"
    },

    # FEATURE 7: Earnings Calendar
    {
        "key": "STORY-019", "title": "[STORY] NSE Corporate Filings API fetcher",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 7,
        "body": "## User Story\nAs a data engineer, I need to pull upcoming board meeting dates from NSE API to track earnings events.\n\n## Parent Feature\nPart of #7\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Calls NSE API\n- [ ] Filters for Financial Results"
    },
    {
        "key": "STORY-020", "title": "[STORY] US earnings calendar fetcher",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 7,
        "body": "## User Story\nAs a data engineer, I need to pull upcoming US earnings dates using yfinance.\n\n## Parent Feature\nPart of #7\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Uses yfinance .calendar"
    },
    {
        "key": "STORY-021", "title": "[STORY] Bronze earnings calendar writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 7,
        "body": "## User Story\nAs a data engineer, I need to write earnings calendar dates to Bronze S3.\n\n## Parent Feature\nPart of #7\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes calendar data to Bronze S3"
    },
    
    # FEATURE 8: Corporate Actions
    {
        "key": "STORY-022", "title": "[STORY] NSE corporate actions fetcher (Splits & Dividends)",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 8,
        "body": "## User Story\nAs a data engineer, I need to fetch splits and dividends from NSE to properly adjust prices.\n\n## Parent Feature\nPart of #8\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Fetches historical and upcoming splits/dividends"
    },
    {
        "key": "STORY-023", "title": "[STORY] Bronze corporate actions writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 8,
        "body": "## User Story\nAs a data engineer, I need to write corporate actions to Bronze S3.\n\n## Parent Feature\nPart of #8\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes corporate actions to Bronze S3"
    },

    # FEATURE 9: Macro Events
    {
        "key": "STORY-024", "title": "[STORY] India Macro Event Calendar fetcher",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:medium", "layer:bronze"],
        "parent": 9,
        "body": "## User Story\nAs a data engineer, I need to fetch macro event calendars to capture volatility events.\n\n## Parent Feature\nPart of #9\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Fetches India/US macro events"
    },

    # FEATURE 10: Circuit Bands
    {
        "key": "STORY-025", "title": "[STORY] NSE daily circuit limits file downloader",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 10,
        "body": "## User Story\nAs a data engineer, I need to download daily circuit limits to capture trading constraints.\n\n## Parent Feature\nPart of #10\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Downloads circuit band file from NSE"
    },
    {
        "key": "STORY-026", "title": "[STORY] Bronze event & circuit band writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "parent": 10,
        "body": "## User Story\nAs a data engineer, I need to write circuit bands to Bronze S3.\n\n## Parent Feature\nPart of #10\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes circuit bands to Bronze S3"
    },

    # FEATURE 18: News Sentiment
    {
        "key": "STORY-027", "title": "[STORY] Finnhub API integration for daily news sentiment",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:medium", "layer:bronze"],
        "parent": 18,
        "body": "## User Story\nAs a data engineer, I need to call the Finnhub API to capture daily news sentiment scores.\n\n## Parent Feature\nPart of #18\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Integrates with Finnhub free tier\n- [ ] Fetches daily sentiment"
    },
    {
        "key": "STORY-028", "title": "[STORY] Bronze sentiment score writer",
        "labels": ["type:story", "phase:1-core", "comp:ingestion", "priority:medium", "layer:bronze"],
        "parent": 18,
        "body": "## User Story\nAs a data engineer, I need to write news sentiment to Bronze S3.\n\n## Parent Feature\nPart of #18\n\n## Child Tasks\n_Updated when tasks are created_\n\n## Acceptance Criteria\n- [ ] Writes sentiment data to Bronze S3"
    }
]

TASKS = [
    # Minimal set of tasks linked to Stories to prove the hierarchy creation
    {
        "key": "TASK-100", "title": "[TASK] Implement NSE bhav copy downloader script",
        "story_key": "STORY-010", "labels": ["type:task", "phase:1-core", "comp:ingestion", "priority:critical", "layer:bronze"],
        "body": "## What needs to be done\nWrite a python script to download and extract the NSE bhav copy.\n\n## Parent Story\nPart of <!-- STORY-010 issue number -->"
    },
    {
        "key": "TASK-101", "title": "[TASK] Write yfinance fundamental mapping logic",
        "story_key": "STORY-013", "labels": ["type:task", "phase:1-core", "comp:ingestion", "priority:high", "layer:bronze"],
        "body": "## What needs to be done\nWrite python logic to map yfinance properties to the target schema.\n\n## Parent Story\nPart of <!-- STORY-013 issue number -->"
    }
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

def get_board_item_id(issue_number):
    node_id = get_issue_node_id(issue_number)
    mutation = "mutation($pid:ID!,$cid:ID!){addProjectV2ItemById(input:{projectId:$pid contentId:$cid}){item{id}}}"
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
    return task["body"].replace(f"<!-- {task['story_key']} issue number -->", str(story_num))

def main():
    print("=== Creating Phase 1 Ingestion Stories ===\n")
    story_nums   = {}
    story_db_ids = {}

    for story in STORIES:
        print(f"Creating {story['key']}: {story['title'][:55]}")
        num = create_issue(story["title"], story["labels"], M2, story["body"])
        if num is None:
            print("  SKIPPED - creation failed")
            continue
        story_nums[story["key"]] = num
        print(f"  -> #{num}")
        time.sleep(1)

        db_id = get_issue_db_id(num)
        story_db_ids[num] = db_id
        ok = add_sub_issue(story["parent"], db_id)
        print(f"  sub-issue of #{story['parent']}: {'OK' if ok else 'FAIL'}")
        
        # Add to board (simplified, skipping custom fields for brevity, board addition handles Level implicitly)
        get_board_item_id(num)
        time.sleep(1)

    print("\n=== Creating Phase 1 Ingestion Tasks ===\n")
    task_nums = {}
    for task in TASKS:
        story_num = story_nums.get(task["story_key"])
        if story_num is None:
            print(f"  SKIP {task['key']} - parent story not created")
            continue
        body = update_task_body_with_story_num(task, story_num)
        print(f"Creating {task['key']}: {task['title'][:55]}")
        num = create_issue(task["title"], task["labels"], M2, body)
        if num is None:
            continue
        task_nums[task["key"]] = num
        print(f"  -> #{num}")
        time.sleep(1)

        db_id = get_issue_db_id(num)
        ok = add_sub_issue(story_num, db_id)
        print(f"  sub-issue of #{story_num}: {'OK' if ok else 'FAIL'}")
        get_board_item_id(num)
        time.sleep(1)

    print("\n=== Summary ===")
    print(f"Total new issues: {len(story_nums) + len(task_nums)}")
    print(f"Board: https://github.com/users/{OWNER}/projects/{PROJECT_NUM}")

if __name__ == "__main__":
    main()
