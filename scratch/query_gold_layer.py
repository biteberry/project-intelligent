import os
import duckdb

print("Connecting to AWS and loading Iceberg extension...")
con = duckdb.connect()

# Load extensions required for Iceberg on S3
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("INSTALL aws; LOAD aws;")
con.execute("CALL load_aws_credentials();")
con.execute("SET s3_region='ap-south-1';")
con.execute("INSTALL iceberg; LOAD iceberg;")
con.execute("SET unsafe_enable_version_guessing=true;")

print("\n--- 1. MARKET REGIME TABLE (J13) ---")
try:
    regime_query = """
    SELECT date, regime_label
    FROM iceberg_scan('s3://project-intelligent-gold-307828758318/market_regime', allow_moved_paths=true)
    ORDER BY date DESC
    LIMIT 5
    """
    df_regime = con.execute(regime_query).df()
    print(df_regime.to_string(index=False))
except Exception as e:
    print(f"Error querying market_regime: {e}")

print("\n--- 2. FEATURES TABLE (J12) ---")
try:
    features_query = """
    SELECT symbol, date, close, rsi_14, macd_12_26_9, return_5d
    FROM iceberg_scan('s3://project-intelligent-gold-307828758318/features', allow_moved_paths=true)
    WHERE symbol = 'RELIANCE.NS'
    ORDER BY date DESC
    LIMIT 5
    """
    df_features = con.execute(features_query).df()
    print(df_features.to_string(index=False))
except Exception as e:
    print(f"Error querying features: {e}")
