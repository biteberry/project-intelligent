# Gold Layer Troubleshooting & Resolution Guide

During the implementation of the Gold Layer Medallion pipeline (J12 Feature Engineering and J13 Market Regime Detection), we encountered several complex infrastructure, dependency, and data-type issues due to running headless environments on AWS EC2 (via Systems Manager) and bleeding-edge data tools (DuckDB, PyIceberg).

This document serves as an architectural record of the technical issues we faced, how we analyzed them, and the exact fixes we applied to stabilize the pipeline.

---

## 1. The `pandas-ta` Dependency Blackhole
**The Error:**
```text
ERROR: Ignored the following versions that require a different python version: 0.4.67b0 Requires-Python >=3.12
ERROR: No matching distribution found for pandas-ta
```
**The Analysis:**
Node B runs on Python 3.11 for maximum data-engineering compatibility. However, `pip` continuously failed to find a compatible version of `pandas-ta`. Upon deeper investigation, we discovered that the original author of `pandas-ta` had completely abandoned the project, deleted the GitHub repository in May 2025, and left PyPI with broken, incompatible beta packages.

**The Fix:**
We completely excised `pandas-ta` from the project. We refactored `j12_feature_engineering.py` to use the industry-standard and actively maintained **`ta`** library (`pip install ta`). This involved rewriting the generation logic for RSI, MACD, Bollinger Bands, and ATR to explicitly map the technical indicators to our own column schemas.

---

## 2. DuckDB Headless SSM Execution Crash
**The Error:**
```text
_duckdb.IOException: IO Error: Can't find the home directory at ''
Specify a home directory using the SET home_directory='/path/to/dir' option.
```
**The Analysis:**
The GitHub Actions workflow triggers the EC2 run via AWS Systems Manager (SSM). SSM runs the script as a headless system process, which means the `$HOME` environment variable is completely empty. When DuckDB booted up and attempted to install extensions (like `aws` and `httpfs`), it defaulted to `~/.duckdb/extensions/` and crashed because `~` did not exist.

**The Fix:**
We explicitly overrode DuckDB's default behavior by injecting the following into the database connection setup:
```python
con.execute("SET home_directory='/tmp';")
```

---

## 3. Iceberg C++ Transitive Dependency Auto-Install Crash
**The Error:**
```text
_duckdb.InvalidInputException: Invalid Input Error: Initialization function "iceberg_duckdb_cpp_init" ... threw an exception: "An error occurred while trying to automatically install the required extension 'avro': Can't find the home directory at ''"
```
**The Analysis:**
Even after applying the `home_directory` fix to the main DuckDB connection, running `INSTALL iceberg;` caused another crash. The Iceberg extension has an underlying C++ hook (`iceberg_duckdb_cpp_init`) that tries to automatically install its transitive dependency (`avro`). This C++ code bypassed the DuckDB connection settings and read the OS `$HOME` variable directly, which was still empty.

**The Fix:**
1. We forced Python to spoof the OS `$HOME` variable before DuckDB was imported: `os.environ['HOME'] = '/tmp'`
2. We preempted the auto-installer by manually installing the dependency first: `con.execute("INSTALL avro; LOAD avro;")`

---

## 4. Iceberg Metadata Globbing Disabled
**The Error:**
```text
_duckdb.Error: Failed to read iceberg table. No version was provided and no version-hint could be found, globbing the filesystem to locate the latest version is disabled by default as this is considered unsafe...
```
**The Analysis:**
When DuckDB executes an `iceberg_scan()`, it scans the S3 metadata folder to locate the latest commit version. In a recent update, DuckDB disabled this "globbing" behavior by default for security reasons (to prevent dirty reads during concurrent writes).

**The Fix:**
Since our pipeline operates strictly sequentially (Silver finishes writing completely before Gold starts reading), it is perfectly safe to enable version guessing. We added the requested flag to the connection:
```python
con.execute("SET unsafe_enable_version_guessing=true;")
```

---

## 5. Pandas Case-Sensitivity (KeyError)
**The Error:**
```text
KeyError: 'close'
```
**The Analysis:**
DuckDB SQL queries are case-insensitive. When we ran `SELECT symbol, date, close`, DuckDB successfully retrieved the data from the Iceberg table. However, when DuckDB converted the result to a Pandas DataFrame (`.df()`), it preserved the exact capitalization from the original Iceberg schema (e.g., `Close` with a capital 'C', derived from Yahoo Finance). Because Pandas is strictly case-sensitive, referencing `df['close']` threw a `KeyError`.

**The Fix:**
We enforced strict schema normalization by forcing all columns to lowercase immediately after the DuckDB-to-Pandas conversion:
```python
df.columns = df.columns.str.lower()
```

---

## 6. PyIceberg Nanosecond Precision Rejection
**The Error:**
```text
pyiceberg.io.pyarrow.UnsupportedPyArrowTypeException: Column 'date' has an unsupported type: timestamp[ns]
```
**The Analysis:**
The Apache Iceberg specification mandates that timestamps must have microsecond (`us`) precision. However, Pandas natively utilizes nanosecond precision (`datetime64[ns]`). When we converted our feature DataFrames into PyArrow tables (`pa.Table.from_pandas()`), PyArrow inherited the nanosecond precision. PyIceberg rejected the schema during table creation.

**The Fix:**
1. **For Appending (Writes):** We added `"downcast-ns-timestamp-to-us-on-write": "true"` to the `iceberg_manager.py` Catalog config to automatically truncate nanoseconds to microseconds when writing data.
2. **For Table Creation (Schema Definition):** Because the auto-downcast config only applies to *writes*, we explicitly cast the schema before handing the PyArrow table to PyIceberg:
```python
idx = arrow_table.schema.get_field_index('date')
new_schema = arrow_table.schema.set(idx, pa.field('date', pa.timestamp('us')))
arrow_table = arrow_table.cast(new_schema)
```
