import subprocess
import os
import boto3
import json
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("EMAIL")
STUDENT_ID = os.getenv("STUDENT_ID")
AWS_PROFILE = os.getenv("AWS_PROFILE")
REPO_NAME = os.getenv("REPO_NAME")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
secret_name = "cpd-coursework-secret"
secret_value = json.dumps({
    "STUDENT_ID": STUDENT_ID,
    "EMAIL": EMAIL,
    "REPO_NAME": REPO_NAME,
    "GITHUB_USERNAME": GITHUB_USERNAME
})

try:
    secrets_client.create_secret(Name=secret_name, SecretString=secret_value)
    print("✅ Secret created in AWS Secrets Manager.")
except secrets_client.exceptions.ResourceExistsException:
    secrets_client.update_secret(SecretId=secret_name, SecretString=secret_value)
    print("🔄 Secret already existed and was updated.")

def run_script(script_name):
    print(f"🔧 Running {script_name}...")
    try:
        subprocess.run(
            ["python", f"cpd_coursework/boto3_scripts/{script_name}"],
            check=True,
            env={**os.environ, "AWS_PROFILE": AWS_PROFILE}
        )
        print(f"✅ {script_name} completed successfully.\n")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to run {script_name}.\n")

def run_cdk_command(command, args):
    print(f"🚀 Running cdk {command}...")
    try:
        subprocess.run(
            ["cdk", command, "--profile", "aws-uni"] + args,
            check=True
        )
        print(f"✅ cdk {command} completed successfully.\n")
    except subprocess.CalledProcessError:
        print(f"❌ cdk {command} failed.\n")

if __name__ == "__main__":
    run_script("create_dynamodb.py")
    run_cdk_command("bootstrap", [])
    run_cdk_command("deploy", ["--require-approval", "never", "--context", f"student_id={STUDENT_ID}"])
    run_script("create_ec2.py")
