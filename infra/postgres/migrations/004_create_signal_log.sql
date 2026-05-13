-- Migration 004: signal_log table
-- Generated trading signals with timestamps

CREATE TABLE IF NOT EXISTS signal_log (
    signal_id           BIGSERIAL       PRIMARY KEY,
    symbol              VARCHAR(20)     NOT NULL,
    signal_date         DATE            NOT NULL,
    signal_direction    SMALLINT        NOT NULL CHECK (signal_direction IN (0, 1)),
    signal_strength     NUMERIC(5, 4),
    model_version       VARCHAR(50)     NOT NULL,
    cap_tier            VARCHAR(10)     NOT NULL CHECK (cap_tier IN ('large', 'mid', 'small', 'unknown')),
    horizon             INTEGER         NOT NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_log_symbol      ON signal_log (symbol);
CREATE INDEX IF NOT EXISTS idx_signal_log_signal_date ON signal_log (signal_date);
CREATE INDEX IF NOT EXISTS idx_signal_log_model       ON signal_log (model_version);
