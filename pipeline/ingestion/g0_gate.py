"""
G0 Quality Gate — Landing → Bronze ingestion validator.

Validates raw OHLCV records from the Landing layer before promoting to Bronze.
Passing records are returned to the caller for Bronze write.
Failing records are written to the S3 quarantine prefix and logged to DynamoDB.
"""

import logging
import uuid
from datetime import date, timedelta
from typing import Any

import boto3
import pandas as pd

logger = logging.getLogger(__name__)

MANDATORY_FIELDS = ["symbol", "date", "open", "high", "low", "close", "volume"]
MISSING_FIELD_RATIO_THRESHOLD = 0.05  # 5%


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run(
    df: pd.DataFrame,
    source: str,
    run_date: str,
    universe: set,
    quarantine_bucket: str,
    audit_table: str,
    region: str = "ap-south-1",
) -> pd.DataFrame:
    """
    Validate *df* against all G0 rules.

    Returns a DataFrame containing only passing rows.
    Rejected rows are written to S3 quarantine and an audit record is written
    to DynamoDB.

    Parameters
    ----------
    df               : Raw OHLCV records from Landing layer.
    source           : Source name (e.g. 'finnhub', 'alphavantage').
    run_date         : Partition date string 'YYYY-MM-DD'.
    universe         : Set of approved ticker symbols.
    quarantine_bucket: S3 bucket name for rejected records.
    audit_table      : DynamoDB table name for audit logs.
    region           : AWS region.
    """
    run_id = str(uuid.uuid4())
    input_count = len(df)

    # --- Rule 6: batch-level missing-field ratio check ---
    _check_missing_field_ratio(df, run_id, source, run_date, input_count, audit_table, region)

    # --- Row-level validation ---
    passing_mask = _build_passing_mask(df, universe, run_date)
    passing_df = df[passing_mask].copy()
    rejected_df = df[~passing_mask].copy()

    pass_count = len(passing_df)
    reject_count = len(rejected_df)

    # --- Rule 7: deduplicate passing rows on symbol + date ---
    passing_df = passing_df.drop_duplicates(subset=["symbol", "date"], keep="first")

    quarantine_path = ""
    if reject_count > 0:
        quarantine_path = _write_quarantine(rejected_df, source, run_date, quarantine_bucket, region)

    status = "PASS" if reject_count == 0 else "PARTIAL" if pass_count > 0 else "FAIL"

    _write_audit(
        run_id=run_id,
        source=source,
        run_date=run_date,
        input_count=input_count,
        pass_count=len(passing_df),
        reject_count=reject_count,
        quarantine_path=quarantine_path,
        status=status,
        audit_table=audit_table,
        region=region,
    )

    logger.info(
        "G0 gate complete run_id=%s source=%s date=%s input=%d pass=%d reject=%d status=%s",
        run_id,
        source,
        run_date,
        input_count,
        pass_count,
        reject_count,
        status,
    )

    return passing_df


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_missing_field_ratio(
    df: pd.DataFrame,
    run_id: str,
    source: str,
    run_date: str,
    input_count: int,
    audit_table: str,
    region: str,
) -> None:
    """Rule 6: reject entire batch if missing-field ratio > 5%."""
    mandatory_present = [f for f in MANDATORY_FIELDS if f in df.columns]
    if not mandatory_present:
        _write_audit(
            run_id=run_id,
            source=source,
            run_date=run_date,
            input_count=input_count,
            pass_count=0,
            reject_count=input_count,
            quarantine_path="",
            status="FAIL",
            audit_table=audit_table,
            region=region,
        )
        raise ValueError(f"G0 FAIL: no mandatory columns present in batch (source={source}, date={run_date})")

    records_with_nulls = df[mandatory_present].isnull().any(axis=1).sum()
    ratio = records_with_nulls / input_count if input_count > 0 else 0.0

    if ratio > MISSING_FIELD_RATIO_THRESHOLD:
        _write_audit(
            run_id=run_id,
            source=source,
            run_date=run_date,
            input_count=input_count,
            pass_count=0,
            reject_count=input_count,
            quarantine_path="",
            status="FAIL",
            audit_table=audit_table,
            region=region,
        )
        raise ValueError(
            f"G0 FAIL: missing-field ratio {ratio:.1%} exceeds {MISSING_FIELD_RATIO_THRESHOLD:.0%} "
            f"threshold (source={source}, date={run_date})"
        )


def _build_passing_mask(df: pd.DataFrame, universe: set, run_date: str) -> pd.Series:
    """Return a boolean Series — True for rows that pass all row-level rules."""
    mask = pd.Series(True, index=df.index)

    # Rule 1: mandatory fields present (non-null)
    for field in MANDATORY_FIELDS:
        if field in df.columns:
            mask &= df[field].notnull()
        else:
            mask &= False

    # Rule 2: no negative prices; volume >= 0
    for price_col in ["open", "high", "low", "close"]:
        if price_col in df.columns:
            mask &= df[price_col] > 0
    if "volume" in df.columns:
        mask &= df["volume"] >= 0

    # Rule 3: high >= low
    if "high" in df.columns and "low" in df.columns:
        mask &= df["high"] >= df["low"]

    # Rule 4: no future dates (allow today + 1 business day)
    if "date" in df.columns:
        cutoff = _future_cutoff()
        parsed = pd.to_datetime(df["date"], errors="coerce").dt.date
        mask &= parsed.notnull() & (parsed <= cutoff)

    # Rule 5: symbol must be in approved universe
    if "symbol" in df.columns:
        mask &= df["symbol"].isin(universe)

    return mask


def _future_cutoff() -> date:
    """Return today + 1 business day as the maximum allowed record date."""
    today = date.today()
    offset = 1
    candidate = today + timedelta(days=1)
    while offset < 1 or candidate.weekday() >= 5:  # skip weekends
        candidate += timedelta(days=1)
        if candidate.weekday() < 5:
            offset += 1
    return candidate


# ---------------------------------------------------------------------------
# S3 quarantine writer
# ---------------------------------------------------------------------------


def _write_quarantine(
    rejected_df: pd.DataFrame,
    source: str,
    run_date: str,
    quarantine_bucket: str,
    region: str,
) -> str:
    """Write rejected records to S3 quarantine prefix as JSON lines."""
    s3 = boto3.client("s3", region_name=region)
    key = f"quarantine/date={run_date}/source={source}/rejected.json"
    body = rejected_df.to_json(orient="records", lines=True, date_format="iso")
    s3.put_object(Bucket=quarantine_bucket, Key=key, Body=body.encode("utf-8"))
    path = f"s3://{quarantine_bucket}/{key}"
    logger.info("Quarantine written: %s (%d records)", path, len(rejected_df))
    return path


# ---------------------------------------------------------------------------
# DynamoDB audit writer
# ---------------------------------------------------------------------------


def _write_audit(
    run_id: str,
    source: str,
    run_date: str,
    input_count: int,
    pass_count: int,
    reject_count: int,
    quarantine_path: str,
    status: str,
    audit_table: str,
    region: str,
) -> None:
    """Write a G0 audit record to DynamoDB."""
    from datetime import datetime, timezone

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(audit_table)
    item: dict[str, Any] = {
        "run_id": run_id,
        "job_id": "G0",
        "source": source,
        "date": run_date,
        "input_count": input_count,
        "pass_count": pass_count,
        "reject_count": reject_count,
        "quarantine_path": quarantine_path,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    table.put_item(Item=item)
    logger.debug("Audit record written: run_id=%s status=%s", run_id, status)
