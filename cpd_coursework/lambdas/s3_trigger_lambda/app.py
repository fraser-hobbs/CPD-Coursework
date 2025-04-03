import os
import json
import boto3

sqs = boto3.client("sqs")
queue_url = os.environ["QUEUE_URL"]

def lambda_handler(event, context):
    records = event.get("Records", [])
    if not records:
        print("No records received.")
        return {
            "statusCode": 400,
            "body": "No S3 events to process"
        }

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        message = {
            "key": key
        }

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

    return {
        "statusCode": 200,
        "body": "SQS message(s) sent for each uploaded image"
    }