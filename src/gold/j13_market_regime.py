import os
import sys
import duckdb
import pandas as pd
import numpy as np

# Ensure AWS Region is set for Headless SSM
os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'

sys.path.append('/home/ec2-user/project-intelligent')
from src.utils.iceberg_manager import write_arrow_to_iceberg
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert

def main():
    date_str = os.environ.get('EXECUTION_DATE', pd.Timestamp.utcnow().strftime('%Y-%m-%d'))
    print(f"Starting J13 Market Regime Detection for {date_str}")
    
    try:
        con = duckdb.connect()
        os.environ['HOME'] = '/tmp'
        con.execute("SET home_directory='/tmp';")
        con.execute("INSTALL avro; LOAD avro;")
        con.execute("INSTALL iceberg; LOAD iceberg;")
        con.execute("INSTALL aws; LOAD aws; CALL load_aws_credentials();")
        con.execute("SET s3_region='ap-south-1';")
        con.execute("SET unsafe_enable_version_guessing=true;")
        
        # We will use RELIANCE.NS as a proxy for the index if ^NSEI is missing for testing
        query = """
        SELECT symbol, date, close
        FROM iceberg_scan('s3://project-intelligent-silver-307828758318/ohlcv_enriched', allow_moved_paths=true)
        WHERE symbol IN ('RELIANCE.NS', '^NSEI', '^INDIAVIX')
        ORDER BY date
        """
        
        df = con.execute(query).df()
        
        if df.empty:
            print("No data found to compute market regime.")
            sys.exit(0)
            
        # For this mock, we will treat RELIANCE.NS as the index if NSEI is not available
        df_index = df[df['symbol'].isin(['^NSEI', 'RELIANCE.NS'])].copy()
        
        if df_index.empty:
            raise Exception("No Index Data found")
            
        # Compute 50-day SMA
        df_index['sma_50'] = df_index['close'].rolling(window=50, min_periods=1).mean()
        df_index['sma_21'] = df_index['close'].rolling(window=21, min_periods=1).mean()
        
        # Calculate Regime
        df_index['regime'] = 'sideways'
        df_index.loc[df_index['close'] > df_index['sma_50'], 'regime'] = 'bull_trend'
        df_index.loc[df_index['close'] < df_index['sma_50'], 'regime'] = 'bear_trend'
        
        # Create final dataframe
        regime_df = pd.DataFrame({
            'date': df_index['date'],
            'market_context': 'india',
            'regime_label': df_index['regime'],
            'index_close': df_index['close'],
            'index_sma_50': df_index['sma_50']
        })
        
        # Write to Gold Layer
        import pyarrow as pa
        arrow_table = pa.Table.from_pandas(regime_df)
        
        table_name = "market_regime"
        full_table_name = write_arrow_to_iceberg(table_name, arrow_table, namespace="project_intelligent_gold")
        
        print(f"Market Regime Detection completed and written to {full_table_name}")
        write_audit_record("J13", date_str, "Success", len(regime_df))
        
    except Exception as e:
        print(f"Failed to process Market Regime: {e}")
        write_audit_record("J13", date_str, "Failed", 0)
        publish_sns_alert("J13 Critical Failure", str(e))
        raise

if __name__ == "__main__":
    main()
