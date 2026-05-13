-- Migration 002: predictions table
-- Local mirror of DynamoDB predictions table (ADR-003)
-- Partition key: symbol, Sort key: prediction_date

CREATE TABLE IF NOT EXISTS predictions (
    symbol              VARCHAR(20)     NOT NULL,
    prediction_date     DATE            NOT NULL,
    horizon             INTEGER         NOT NULL,
    cap_tier            VARCHAR(10)     NOT NULL CHECK (cap_tier IN ('large', 'mid', 'small', 'unknown')),
    prediction_direction SMALLINT       NOT NULL CHECK (prediction_direction IN (0, 1)),
    prediction_return   NUMERIC(10, 6),
    confidence          NUMERIC(5, 4),
    model_version       VARCHAR(50)     NOT NULL,
    gold_snapshot_id    VARCHAR(100),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, prediction_date)
);

CREATE INDEX IF NOT EXISTS idx_predictions_date        ON predictions (prediction_date);
CREATE INDEX IF NOT EXISTS idx_predictions_model       ON predictions (model_version);
