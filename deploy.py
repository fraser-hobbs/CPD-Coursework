import time
import boto3
import os
import subprocess
import zipfile
import dotenv
import json

dotenv.load_dotenv()

AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
STUDENT_ID = os.getenv("STUDENT_ID", "s0000000")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789012")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "123456789012")

TEMPLATE_FILE = "cpd_coursework/cf_templates/main_stack.yaml"
STACK_NAME = f"CPD-Coursework-Stack-{STUDENT_ID}"
LAMBDA_S3_BUCKET = f"lambda-artifacts-{STUDENT_ID}"


def run_script(script_name):
    print(f"🔧 Running {script_name}...")
    result = subprocess.run(
        ["python3", f"cpd_coursework/boto3_scripts/{script_name}"],
        check=True,
    )
    print(f"✅ {script_name} completed successfully.")


def zip_lambda_code(source_dir, zip_filename):
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                zipf.write(file_path, arcname)


def upload_lambda_to_s3(lambda_dir, s3_key):
    zip_file = f"/tmp/{s3_key}.zip"
    zip_lambda_code(lambda_dir, zip_file)

    s3_client = boto3.client("s3", region_name=AWS_REGION)
    print(f"🚀 Uploading {s3_key}.zip to s3://{LAMBDA_S3_BUCKET}/{s3_key}.zip...")
    s3_client.upload_file(zip_file, LAMBDA_S3_BUCKET, f"{s3_key}.zip")
    print(f"✅ Uploaded {s3_key}.zip")


def deploy_bootstrap_stack():
    print("🚀 Deploying bootstrap CloudFormation stack...")
    subprocess.run([
        "aws", "cloudformation", "deploy",
        "--template-file", "cpd_coursework/cf_templates/bootstrap_stack.yaml",
        "--stack-name", f"CPD-Coursework-Bootstrap-{STUDENT_ID}",
        "--profile", AWS_PROFILE,
        "--region", AWS_REGION,
        "--capabilities", "CAPABILITY_NAMED_IAM",
    ], check=True)
    print("✅ Bootstrap stack deployed successfully.")


def deploy_main_stack():
    print("🚀 Deploying main CloudFormation stack...")
    subprocess.run([
        "aws", "cloudformation", "deploy",
        "--template-file", TEMPLATE_FILE,
        "--stack-name", STACK_NAME,
        "--profile", AWS_PROFILE,
        "--region", AWS_REGION,
        "--capabilities", "CAPABILITY_NAMED_IAM",
        "--parameter-overrides",
        f"StudentID={STUDENT_ID}",
        f"RoleArn=arn:aws:iam::{ACCOUNT_ID}:role/LabRole",
    ], check=True)
    print(f"✅ Stack {STACK_NAME} deployed successfully.")


if __name__ == "__main__":
    run_script("create_dynamodb.py")

    print("🔐 Creating/Updating secrets in AWS Secrets Manager...")
    secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)

    secret_name = "cpd-coursework-secret"
    secret_value = json.dumps({
        "GITHUB_USERNAME": f"{GITHUB_USERNAME}",
        "GITHUB_REPO": f"{GITHUB_REPO}",
        "BUCKET_NAME": f"face-comparison-bucket-{STUDENT_ID}",
        "TOPIC_ARN": f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:face-comparison-topic-{STUDENT_ID}",
        "QUEUE_URL": f"https://sqs.{AWS_REGION}.amazonaws.com/{ACCOUNT_ID}/face-comparison-queue-{STUDENT_ID}",
        "STUDENT_ID": STUDENT_ID,
    })

    try:
        secrets_client.create_secret(Name=secret_name, SecretString=secret_value)
        print(f"✅ Secret '{secret_name}' created successfully.")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.put_secret_value(SecretId=secret_name, SecretString=secret_value)
        print(f"🔄 Secret '{secret_name}' already existed and was updated.")

    deploy_bootstrap_stack()
    upload_lambda_to_s3("cpd_coursework/lambdas/face_comparison_lambda", "face_comparison_lambda")
    upload_lambda_to_s3("cpd_coursework/lambdas/notification_lambda", "notification_lambda")
    deploy_main_stack()

    run_script("subscribe_sns_email.py")
    run_script("create_s3_trigger.py")
    run_script("create_dynamodb_trigger.py")

    time.sleep(10)

    print("Creating EC2 Instances.")
    run_script("create_ec2.py")
