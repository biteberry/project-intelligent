import os
import boto3

def publish_sns_alert(subject: str, message: str):
    """
    Publish an alert to the project SNS topic.
    """
    topic_arn = os.environ.get("SNS_ALERT_TOPIC_ARN", "arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts")
    sns = boto3.client('sns', region_name='ap-south-1')

    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],  # SNS subject limit is 100 chars
            Message=message
        )
        print(f"Alert published: {subject}")
    except Exception as e:
        print(f"Failed to publish SNS alert: {e}")
