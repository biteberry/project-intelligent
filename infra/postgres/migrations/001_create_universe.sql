-- Migration 001: universe table
-- Tracks all symbols under active monitoring with tier and metadata
-- Mirrors the DynamoDB universe selection + S3 snapshot design from ADR-003

CREATE TABLE IF NOT EXISTS universe (
    symbol          VARCHAR(20)  NOT NULL,
    cap_tier        VARCHAR(10)  NOT NULL CHECK (cap_tier IN ('large', 'mid', 'small', 'unknown')),
    sector          VARCHAR(100),
    market_cap      NUMERIC(20, 2),
    added_date      DATE         NOT NULL DEFAULT CURRENT_DATE,
    removed_date    DATE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    snapshot_id     VARCHAR(100),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol)
);

CREATE INDEX IF NOT EXISTS idx_universe_cap_tier  ON universe (cap_tier);
CREATE INDEX IF NOT EXISTS idx_universe_is_active ON universe (is_active);
