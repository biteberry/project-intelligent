-- Migration 005: backtest_results table
-- Backtesting run output per model and horizon (ADR-003)

CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id         BIGSERIAL       PRIMARY KEY,
    model_version       VARCHAR(50)     NOT NULL,
    horizon             INTEGER         NOT NULL,
    cap_tier            VARCHAR(10)     NOT NULL CHECK (cap_tier IN ('large', 'mid', 'small', 'unknown')),
    start_date          DATE            NOT NULL,
    end_date            DATE            NOT NULL,
    total_return        NUMERIC(10, 6),
    sharpe_ratio        NUMERIC(10, 6),
    max_drawdown        NUMERIC(10, 6),
    win_rate            NUMERIC(5, 4),
    num_trades          INTEGER,
    gold_snapshot_id    VARCHAR(100),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_model   ON backtest_results (model_version);
CREATE INDEX IF NOT EXISTS idx_backtest_horizon ON backtest_results (horizon, cap_tier);
