# Feature #9: India Macro Event Calendar (J07)

This plan addresses Issue #9 (India Macro Event Calendar), which provides the reference dates for the RBI MPC announcements and Union Budget. These binary macro events are critical for setting the `macro_event_blackout_flag` on rate-sensitive sectors in the downstream Silver layer.

As specified in the PRD and Data Ingestion Architecture docs, because there are only ~7 dates per year and they are known well in advance, it is brittle to build an automated web scraper. The data will be managed via a static YAML reference file.

*(Note: We will designate this pipeline as **J07** since J03, J04, J05, and J06 are already allocated to other ingestion pipelines).*

## Proposed Changes

### 1. Issue Management
- Created child story **Issue #219** (`[STORY] Bronze macro events calendar writer`).
- Child story **Issue #203** (`[STORY] India Macro Event Calendar fetcher`) will be handled by the logic that reads the YAML file.
- **Rule Check**: Acceptance criteria defined and verified for all issues.

### 2. Static Configuration

#### [NEW] `configs/india_macro_events.yaml`
We will create the annual YAML calendar file to hold the RBI MPC and Union Budget dates. 

### 3. Pipeline Orchestration

#### [NEW] `src/ingestion/j07_macro_events_reference.py`
A lightweight script that:
- Loads `configs/india_macro_events.yaml`.
- Converts the list of events into a Pandas DataFrame.
- Adds metadata (`ingestion_run_id`, `ingestion_timestamp`).
- Writes the DataFrame directly to the Bronze layer in S3 via `write_dataframe_to_bronze(table_name="macro_events_calendar")`.
- Records success metrics in the DynamoDB audit log.

#### [MODIFY] `.github/workflows/weekly_batch.yml`
Since this reference data only changes annually, it does not strictly need to be run every single week, but adding it to the end of the `weekly_batch.yml` guarantees that any changes made to the YAML file in Git are automatically synced to the Bronze S3 table within 7 days without requiring a manual deployment step.

## Verification Plan

### Automated Tests
- None required for this reference sync task.

### Manual Verification
- Execute `j07_macro_events_reference.py` on the EC2 instance via AWS SSM.
- Verify that `s3://project-intelligent-bronze/macro_events_calendar/` is populated with the correct Parquet file containing the 2024 dates.
