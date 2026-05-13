"""
Unit tests for pipeline/ingestion/g0_gate.py
All 7 validation rules + quarantine write + DynamoDB audit log.
Uses moto for S3 and DynamoDB isolation.
"""

import sys
import os
from datetime import date, timedelta

import boto3
import pandas as pd
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.ingestion import g0_gate

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGION = "ap-south-1"
QUARANTINE_BUCKET = "project-intelligent-landing"
AUDIT_TABLE = "project-intelligent-pipeline-audit"
SOURCE = "finnhub"
RUN_DATE = "2024-01-02"
UNIVERSE = {"AAPL", "MSFT", "GOOGL", "RELIANCE"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_row(symbol="AAPL", record_date=None):
    """Return a single valid OHLCV row as a dict."""
    return {
        "symbol": symbol,
        "date": record_date or RUN_DATE,
        "open": 185.0,
        "high": 186.0,
        "low": 184.0,
        "close": 185.5,
        "volume": 72000000,
    }


def _make_df(*rows):
    return pd.DataFrame(list(rows))


@pytest.fixture
def aws_setup():
    """Spin up moto S3 bucket and DynamoDB table for every test."""
    with mock_aws():
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=QUARANTINE_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        dynamodb.create_table(
            TableName=AUDIT_TABLE,
            KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield s3, dynamodb.Table(AUDIT_TABLE)


def _run(df, universe=None):
    return g0_gate.run(
        df=df,
        source=SOURCE,
        run_date=RUN_DATE,
        universe=universe or UNIVERSE,
        quarantine_bucket=QUARANTINE_BUCKET,
        audit_table=AUDIT_TABLE,
        region=REGION,
    )


# ---------------------------------------------------------------------------
# Rule 1 — Mandatory fields
# ---------------------------------------------------------------------------


class TestMandatoryFields:
    def test_pass_all_fields_present(self, aws_setup):
        df = _make_df(_valid_row())
        result = _run(df)
        assert len(result) == 1

    def test_fail_missing_volume(self, aws_setup):
        # 25 rows, 1 with null volume → 4% record-level ratio (< 5%, batch passes)
        rows = [_valid_row(record_date=f"2024-01-{i+1:02d}") for i in range(25)]
        rows[0]["volume"] = None
        df = _make_df(*rows)
        result = _run(df)
        assert len(result) == 24

    def test_fail_missing_symbol(self, aws_setup):
        # 25 rows, 1 with null symbol → 4% record-level ratio (< 5%, batch passes)
        rows = [_valid_row(record_date=f"2024-01-{i+1:02d}") for i in range(25)]
        rows[0]["symbol"] = None
        df = _make_df(*rows)
        result = _run(df)
        assert len(result) == 24


# ---------------------------------------------------------------------------
# Rule 2 — No negative prices / volumes
# ---------------------------------------------------------------------------


class TestNegativePrices:
    def test_pass_all_positive(self, aws_setup):
        df = _make_df(_valid_row())
        result = _run(df)
        assert len(result) == 1

    def test_fail_negative_close(self, aws_setup):
        row = _valid_row()
        row["close"] = -1.5
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 0

    def test_fail_zero_open(self, aws_setup):
        row = _valid_row()
        row["open"] = 0.0
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 0

    def test_pass_zero_volume(self, aws_setup):
        row = _valid_row()
        row["volume"] = 0
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Rule 3 — High >= Low
# ---------------------------------------------------------------------------


class TestHighLow:
    def test_pass_high_greater_than_low(self, aws_setup):
        row = _valid_row()
        row["high"], row["low"] = 105.0, 100.0
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 1

    def test_pass_high_equals_low(self, aws_setup):
        row = _valid_row()
        row["high"] = row["low"] = 100.0
        row["open"] = row["close"] = 100.0
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 1

    def test_fail_high_less_than_low(self, aws_setup):
        row = _valid_row()
        row["high"], row["low"] = 99.0, 100.0
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Rule 4 — No future dates
# ---------------------------------------------------------------------------


class TestFutureDate:
    def test_pass_todays_date(self, aws_setup):
        row = _valid_row(record_date=date.today().isoformat())
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 1

    def test_pass_historical_date(self, aws_setup):
        row = _valid_row(record_date="2020-01-15")
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 1

    def test_fail_far_future_date(self, aws_setup):
        future = (date.today() + timedelta(days=10)).isoformat()
        row = _valid_row(record_date=future)
        df = _make_df(row)
        result = _run(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Rule 5 — Symbol in approved universe
# ---------------------------------------------------------------------------


class TestUniverseCheck:
    def test_pass_valid_symbol(self, aws_setup):
        df = _make_df(_valid_row(symbol="AAPL"))
        result = _run(df)
        assert len(result) == 1

    def test_fail_unknown_symbol(self, aws_setup):
        df = _make_df(_valid_row(symbol="UNKNOWN_XYZ"))
        result = _run(df)
        assert len(result) == 0

    def test_mixed_symbols(self, aws_setup):
        df = _make_df(_valid_row(symbol="AAPL"), _valid_row(symbol="UNKNOWN_XYZ"))
        result = _run(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# Rule 6 — Missing field ratio <= 5%
# ---------------------------------------------------------------------------


class TestMissingFieldRatio:
    def test_pass_low_null_ratio(self, aws_setup):
        # 100 rows with unique dates, 2 with null volume → 2% record-level ratio
        rows = [_valid_row(record_date=f"2024-01-{i % 28 + 1:02d}") for i in range(100)]
        # ensure unique symbol+date combos to avoid dedup collapse
        for i, row in enumerate(rows):
            row["symbol"] = "AAPL" if i % 2 == 0 else "MSFT"
            row["date"] = f"2024-{(i // 28) + 1:02d}-{i % 28 + 1:02d}"
        rows[0]["volume"] = None
        rows[1]["volume"] = None
        df = _make_df(*rows)
        result = _run(df)
        assert len(result) == 98  # 2 rejected for missing volume

    def test_fail_high_null_ratio(self, aws_setup):
        # 100 rows, 6 with null volume → 6% record-level ratio > 5% threshold
        rows = [_valid_row(record_date=f"2024-{(i // 28) + 1:02d}-{i % 28 + 1:02d}") for i in range(100)]
        for i, row in enumerate(rows):
            row["symbol"] = "AAPL" if i % 2 == 0 else "MSFT"
        for i in range(6):
            rows[i]["volume"] = None
        df = _make_df(*rows)
        with pytest.raises(ValueError, match="missing-field ratio"):
            _run(df)


# ---------------------------------------------------------------------------
# Rule 7 — Deduplication on symbol + date
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_pass_unique_symbol_date(self, aws_setup):
        df = _make_df(_valid_row(symbol="AAPL"), _valid_row(symbol="MSFT"))
        result = _run(df)
        assert len(result) == 2

    def test_dedup_duplicate_symbol_date(self, aws_setup):
        df = _make_df(_valid_row(symbol="AAPL"), _valid_row(symbol="AAPL"))
        result = _run(df)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Quarantine write
# ---------------------------------------------------------------------------


class TestQuarantineWrite:
    def test_rejected_records_written_to_s3(self, aws_setup):
        s3, _ = aws_setup
        row_bad = _valid_row()
        row_bad["close"] = -5.0
        df = _make_df(_valid_row(), row_bad)
        _run(df)

        key = f"quarantine/date={RUN_DATE}/source={SOURCE}/rejected.json"
        obj = s3.get_object(Bucket=QUARANTINE_BUCKET, Key=key)
        content = obj["Body"].read().decode("utf-8")
        assert "AAPL" in content

    def test_no_quarantine_file_when_all_pass(self, aws_setup):
        s3, _ = aws_setup
        df = _make_df(_valid_row())
        _run(df)

        key = f"quarantine/date={RUN_DATE}/source={SOURCE}/rejected.json"
        objects = s3.list_objects_v2(Bucket=QUARANTINE_BUCKET, Prefix="quarantine/")
        keys = [o["Key"] for o in objects.get("Contents", [])]
        assert key not in keys


# ---------------------------------------------------------------------------
# DynamoDB audit log
# ---------------------------------------------------------------------------


class TestDynamoAuditLog:
    def test_audit_record_written_on_pass(self, aws_setup):
        _, table = aws_setup
        df = _make_df(_valid_row())
        _run(df)

        items = table.scan()["Items"]
        assert len(items) == 1
        item = items[0]
        assert item["job_id"] == "G0"
        assert item["source"] == SOURCE
        assert item["date"] == RUN_DATE
        assert item["input_count"] == 1
        assert item["pass_count"] == 1
        assert item["reject_count"] == 0
        assert item["status"] == "PASS"
        assert "run_id" in item
        assert "timestamp" in item

    def test_audit_record_written_on_partial(self, aws_setup):
        _, table = aws_setup
        row_bad = _valid_row()
        row_bad["close"] = -1.0
        df = _make_df(_valid_row(), row_bad)
        _run(df)

        items = table.scan()["Items"]
        assert len(items) == 1
        item = items[0]
        assert item["status"] == "PARTIAL"
        assert item["reject_count"] == 1

    def test_audit_record_status_fail_on_batch_reject(self, aws_setup):
        # 100 rows, 6 with null volume → 6% record-level ratio > 5% → batch FAIL
        rows = [_valid_row(record_date=f"2024-{(i // 28) + 1:02d}-{i % 28 + 1:02d}") for i in range(100)]
        for i, row in enumerate(rows):
            row["symbol"] = "AAPL" if i % 2 == 0 else "MSFT"
        for i in range(6):
            rows[i]["volume"] = None
        df = _make_df(*rows)
        with pytest.raises(ValueError):
            _run(df)

        _, table = aws_setup
        items = table.scan()["Items"]
        assert len(items) == 1
        assert items[0]["status"] == "FAIL"
