import boto3
import os
import botocore.exceptions
from dotenv import load_dotenv
load_dotenv()

student_id = os.environ["STUDENT_ID"]

region = os.environ["AWS_REGION"]
dynamodb = boto3.client("dynamodb", region_name=region)

table_name = f"FaceComparisonResults-{student_id}"

try:
    response = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "ImageID", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "ImageID", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
        StreamSpecification={
            "StreamEnabled": True,
            "StreamViewType": "NEW_IMAGE"
        }
    )
    print(f"✅ Created table: {table_name}")
except botocore.exceptions.ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print(f"ℹ️ Table {table_name} already exists, skipping creation.")
    else:
        raise