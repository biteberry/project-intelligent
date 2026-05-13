SELECT snapshot_id, committed_at, operation
FROM "project_intelligent_silver"."silver_ohlcv$snapshots"
ORDER BY committed_at;
