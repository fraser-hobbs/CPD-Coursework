import boto3
import os

student_id = os.getenv("STUDENT_ID", "00000000")

dynamodb = boto3.client("dynamodb")

table_name = f"FaceComparisonResults-{student_id}"

response = dynamodb.create_table(
    TableName=table_name,
    KeySchema=[{"AttributeName": "ImageID", "KeyType": "HASH"}],
    AttributeDefinitions=[{"AttributeName": "ImageID", "AttributeType": "S"}],
    BillingMode="PAY_PER_REQUEST"
)

print(f"Created table: {table_name}")