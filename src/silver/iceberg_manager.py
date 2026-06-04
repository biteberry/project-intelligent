import os
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchNamespaceError, NoSuchTableError

# Ensure boto3 has the correct region for Glue
os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'

# Configure PyIceberg to use AWS Glue Data Catalog
_catalog = load_catalog(
    "default",
    **{
        "type": "glue",
        "s3.region": "ap-south-1",
        "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO"
    }
)

def ensure_namespace_exists(namespace: str):
    """Ensure the AWS Glue Database exists."""
    try:
        _catalog.load_namespace(namespace)
    except NoSuchNamespaceError:
        print(f"Creating Glue Database: {namespace}")
        _catalog.create_namespace(namespace)

def write_arrow_to_iceberg(table_name: str, arrow_table: pa.Table, namespace: str = "project_intelligent_silver"):
    """
    Appends a PyArrow Table to an Apache Iceberg table in the AWS Glue Catalog.
    If the table does not exist, it automatically creates it with the schema of the Arrow Table.
    """
    ensure_namespace_exists(namespace)
    
    full_table_name = f"{namespace}.{table_name}"
    
    try:
        # Load table if it exists
        table = _catalog.load_table(full_table_name)
        print(f"Appending to existing Iceberg table: {full_table_name}")
        table.append(arrow_table)
    except NoSuchTableError:
        # Create new table using the schema of the pyarrow table
        s3_bucket = os.environ.get('S3_SILVER_BUCKET', 'project-intelligent-silver-307828758318')
        location = f"s3://{s3_bucket}/{table_name}"
        
        print(f"Creating new Iceberg table {full_table_name} at {location}")
        table = _catalog.create_table(
            full_table_name,
            schema=arrow_table.schema,
            location=location
        )
        table.append(arrow_table)
        
    return full_table_name
