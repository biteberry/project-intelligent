-- Migration 003: pipeline_audit table
-- Local mirror of DynamoDB pipeline_audit table (ADR-003)
-- Partition key: job_type, Sort key: run_id

CREATE TABLE IF NOT EXISTS pipeline_audit (
    run_id              VARCHAR(50)     NOT NULL,
    job_type            VARCHAR(50)     NOT NULL,
    input_snapshot      VARCHAR(200),
    output_snapshot     VARCHAR(200),
    row_count_in        INTEGER,
    row_count_out       INTEGER,
    status              VARCHAR(20)     NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    duration_seconds    NUMERIC(10, 3),
    error_message       TEXT,
    started_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    audit_expiry        TIMESTAMPTZ     NOT NULL DEFAULT NOW() + INTERVAL '90 days',

    PRIMARY KEY (run_id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_audit_job_type   ON pipeline_audit (job_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_audit_started_at ON pipeline_audit (started_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_audit_status     ON pipeline_audit (status);
