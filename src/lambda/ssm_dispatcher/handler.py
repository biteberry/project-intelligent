# Lambda SSM dispatcher handler
# Issue #72: Implements Lambda to trigger SSM RunCommand on EC2 from EventBridge
#
# Steps:
# 1. Parse event type (daily/weekly) from EventBridge event
# 2. Read EC2_INSTANCE_ID and SSM_DOCUMENT_NAME from environment variables
# 3. Call ssm.send_command() to start pipeline
# 4. Log command ID to CloudWatch

import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Lambda entry point. Receives EventBridge event, triggers SSM RunCommand on EC2.
    Handles both daily and weekly triggers.
    """
    # 1. Parse event type (daily/weekly)
    # EventBridge 'detail-type' or custom field can be used to distinguish
    event_type = 'unknown'
    if 'detail-type' in event:
        if 'daily' in event['detail-type'].lower():
            event_type = 'daily'
        elif 'weekly' in event['detail-type'].lower():
            event_type = 'weekly'
    # Fallback: check for custom fields if needed

    logger.info(f"Received event: {event}")
    logger.info(f"Trigger type detected: {event_type}")

    # 2. Read environment variables
    ec2_instance_id = os.environ.get('EC2_INSTANCE_ID')
    ssm_document_name = os.environ.get('SSM_DOCUMENT_NAME')
    if not ec2_instance_id or not ssm_document_name:
        logger.error("Missing EC2_INSTANCE_ID or SSM_DOCUMENT_NAME in environment variables.")
        raise Exception("Missing required environment variables.")

    # 3. Prepare SSM RunCommand parameters
    # You can customize parameters as needed for your pipeline
    command_parameters = {
        'event_type': [event_type]
    }

    try:
        response = ssm.send_command(
            InstanceIds=[ec2_instance_id],
            DocumentName=ssm_document_name,
            Parameters=command_parameters,
        )
        command_id = response['Command']['CommandId']
        logger.info(f"SSM command sent. Command ID: {command_id}")
        return {
            'statusCode': 200,
            'body': f"SSM command sent. Command ID: {command_id}"
        }
    except Exception as e:
        logger.error(f"Failed to send SSM command: {e}")
        raise
