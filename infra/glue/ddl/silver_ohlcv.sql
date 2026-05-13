-- Story #51 / Task #137
-- Registers silver_ohlcv as an Iceberg table in the Glue Catalog via Athena DDL.
-- Run this in Athena using the "project-intelligent" workgroup (engine v3).
-- S3 output location must exist before running.

CREATE TABLE project_intelligent_silver.silver_ohlcv (
    date         TIMESTAMP,
    symbol       STRING,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    adj_close    DOUBLE,
    volume       BIGINT,
    sector       STRING,
    market_cap   DOUBLE,
    cap_tier     STRING,
    is_valid_row BOOLEAN
)
LOCATION 's3://project-intelligent-silver-307828758318/ohlcv/'
TBLPROPERTIES (
    'table_type'          = 'ICEBERG',
    'format'              = 'parquet',
    'write_compression'   = 'snappy'
);
