import boto3
import os
from dotenv import load_dotenv

load_dotenv()

stack_name = os.getenv("CFN_STACK_NAME", "CPD-Coursework-Stack-s2341289")
aws_region = os.getenv("AWS_REGION", "us-east-1")
aws_profile = os.getenv("AWS_PROFILE", "default")

session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
cloudformation = session.client("cloudformation")
s3 = session.client("s3")

# Get outputs from the CloudFormation stack
response = cloudformation.describe_stacks(StackName=stack_name)
outputs = response["Stacks"][0]["Outputs"]

bucket_name = None
queue_arn = None

for output in outputs:
    if output["OutputKey"] == "BucketName":
        bucket_name = output["OutputValue"]
    elif output["OutputKey"] == "QueueArn":
        queue_arn = output["OutputValue"]

if not bucket_name or not queue_arn:
    raise Exception("Missing bucket name or queue ARN in stack outputs.")

# Set the S3 event notification to trigger SQS
s3.put_bucket_notification_configuration(
    Bucket=bucket_name,
    NotificationConfiguration={
        "QueueConfigurations": [
            {
                "QueueArn": queue_arn,
                "Events": ["s3:ObjectCreated:*"]
            }
        ]
    }
)

print(f"✅ Configured S3 trigger: {bucket_name} -> {queue_arn}")
