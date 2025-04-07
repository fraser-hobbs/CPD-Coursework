import boto3
import os
import botocore.exceptions

student_id = os.getenv("STUDENT_ID", "00000000")

dynamodb = boto3.client("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))

table_name = f"FaceComparisonResults-{student_id}"

try:
    response = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "ImageID", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "ImageID", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"

    )
    print(f"✅ Created table: {table_name}")
except botocore.exceptions.ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print(f"ℹ️ Table {table_name} already exists, skipping creation.")
    else:
        raise