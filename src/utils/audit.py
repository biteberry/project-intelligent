import os
import boto3
from datetime import datetime

def write_audit_record(run_id: str, job_id: str, status: str, metrics: dict):
    """
    Write a job execution audit record to DynamoDB.
    """
    table_name = os.environ.get("DYNAMODB_AUDIT_TABLE", "project-intelligent-job-audit")
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table(table_name)
    
    item = {
        'run_id': run_id,
        'job_id': job_id,
        'status': status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'metrics': metrics
    }
    
    try:
        table.put_item(Item=item)
        print(f"Audit record written for {run_id}")
    except Exception as e:
        # In a real scenario, we might want to log this but not fail the pipeline if audit fails
        print(f"Failed to write audit record: {e}")
