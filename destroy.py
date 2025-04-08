import boto3
import os
import subprocess
import dotenv
import json
from botocore.exceptions import ClientError

dotenv.load_dotenv()

AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
STUDENT_ID = os.getenv("STUDENT_ID", "s0000000")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789012")
LAMBDA_S3_BUCKET = f"lambda-artifacts-{STUDENT_ID}"
FACE_BUCKET_NAME = f"face-comparison-bucket-{STUDENT_ID}"

STACK_NAME = f"CPD-Coursework-Stack-{STUDENT_ID}"
BOOTSTRAP_STACK_NAME = f"CPD-Coursework-Bootstrap-{STUDENT_ID}"
SECRET_NAME = "cpd-coursework-secret"
DYNAMODB_TABLE_NAME = f"FaceComparisonResults-{STUDENT_ID}"
EC2_INSTANCE_NAME_TAG = f"CPD-Coursework-EC2-{STUDENT_ID}"

def empty_and_delete_bucket(bucket_name):
    s3 = boto3.resource("s3", region_name=AWS_REGION)
    bucket = s3.Bucket(bucket_name)
    try:
        print(f"🧹 Emptying and deleting S3 bucket '{bucket_name}'...")
        bucket.objects.all().delete()
        bucket.object_versions.all().delete()  # Also delete versioned objects
        bucket.delete()
        print(f"✅ S3 bucket '{bucket_name}' deleted.")
    except ClientError as e:
        print(f"⚠️ S3 deletion error: {e} - bucket= '{bucket_name}'")

def delete_stack(stack_name):
    print(f"🗑️ Deleting CloudFormation stack {stack_name}...")
    subprocess.run([
        "aws", "cloudformation", "delete-stack",
        "--stack-name", stack_name,
        "--profile", AWS_PROFILE,
        "--region", AWS_REGION
    ], check=True)
    print(f"✅ Stack {stack_name} deleted.")

def delete_secret():
    secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        secrets_client.delete_secret(
            SecretId=SECRET_NAME,
            ForceDeleteWithoutRecovery=True
        )
        print(f"✅ Secret '{SECRET_NAME}' deleted.")
    except ClientError as e:
        print(f"⚠️ Secret deletion error: {e}")

def delete_dynamodb_table():
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    try:
        dynamodb.delete_table(TableName=DYNAMODB_TABLE_NAME)
        print(f"✅ DynamoDB table '{DYNAMODB_TABLE_NAME}' deleted.")
    except ClientError as e:
        print(f"⚠️ DynamoDB deletion error: {e}")

def terminate_ec2_instances():
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    try:
        instances = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": [EC2_INSTANCE_NAME_TAG]},
                {"Name": "instance-state-name", "Values": ["pending", "running", "stopped"]}
            ]
        )
        instance_ids = [
            i["InstanceId"]
            for r in instances["Reservations"]
            for i in r["Instances"]
        ]
        if instance_ids:
            ec2.terminate_instances(InstanceIds=instance_ids)
            print(f"✅ Terminating EC2 instances: {instance_ids}")
        else:
            print("ℹ️ No EC2 instances found to terminate.")
    except ClientError as e:
        print(f"⚠️ EC2 termination error: {e}")

if __name__ == "__main__":
    empty_and_delete_bucket(LAMBDA_S3_BUCKET)
    empty_and_delete_bucket(FACE_BUCKET_NAME)
    delete_stack(STACK_NAME)
    delete_stack(BOOTSTRAP_STACK_NAME)
    delete_secret()
    delete_dynamodb_table()
    terminate_ec2_instances()
