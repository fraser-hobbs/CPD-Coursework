import boto3
import os
import dotenv

dotenv.load_dotenv()

region = os.getenv("AWS_REGION", "us-east-1")
STUDENT_ID = os.getenv("STUDENT_ID")
stack_name = os.getenv("CFN_STACK_NAME", f"CPD-Coursework-Stack-{STUDENT_ID}")


student_id = os.getenv("STUDENT_ID", "00000000")
table_name = f"FaceComparisonResults-{student_id}"

cloudformation = boto3.client("cloudformation", region_name=region)
lambda_client = boto3.client("lambda", region_name=region)

# Get Lambda ARN from CloudFormation Outputs
response = cloudformation.describe_stacks(StackName=stack_name)
outputs = response["Stacks"][0]["Outputs"]

lambda_arn = None
for output in outputs:
    if output["OutputKey"] == "NotificationFunctionArn":
        lambda_arn = output["OutputValue"]
        break

if not lambda_arn:
    raise Exception("NotificationFunctionArn not found in stack outputs")

# Get the DynamoDB stream ARN
dynamodb = boto3.client("dynamodb", region_name=region)
table_info = dynamodb.describe_table(TableName=table_name)
stream_arn = table_info["Table"]["LatestStreamArn"]

# Create event source mapping
try:
    lambda_client.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName=lambda_arn,
        StartingPosition="LATEST",
        BatchSize=5,
        Enabled=True,
    )
    print(f"✅ Stream trigger created from {table_name} to Lambda {lambda_arn}")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️ Event source mapping already exists.")