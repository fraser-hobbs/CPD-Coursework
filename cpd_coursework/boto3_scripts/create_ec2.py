import boto3
import os
import json

secretsmanager = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))

ec2 = boto3.client("ec2", region_name=os.getenv("AWS_REGION", "us-east-1"))
secret_response = secretsmanager.get_secret_value(SecretId="cpd-coursework-secret")
secret_data = json.loads(secret_response["SecretString"])

AMI_ID = "ami-00a929b66ed6e0de6"

GITHUB_USERNAME = secret_data.get("GITHUB_USERNAME")
GITHUB_REPO = secret_data.get("GITHUB_REPO")
STUDENT_ID = os.getenv("STUDENT_ID", "00000000")

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/cpd_coursework"

# UserData script (runs on boot)
USER_DATA = f'''#!/bin/bash
yum update -y
yum install -y python3 pip unzip
pip3 install boto3 python-dotenv

# Create working dir
mkdir -p /home/ec2-user/uploader
cd /home/ec2-user/uploader

# Download uploader script
curl -O {BASE_URL}/boto3_scripts/image_uploader.py

# Download images
curl -O {BASE_URL}/resources/images/groupphoto.png
curl -O {BASE_URL}/resources/images/image1.jpg
curl -O {BASE_URL}/resources/images/image2.jpg
curl -O {BASE_URL}/resources/images/image3.jpg
curl -O {BASE_URL}/resources/images/image4.jpg
curl -O {BASE_URL}/resources/images/image5.jpg

# Create .env file
echo "STUDENT_ID={STUDENT_ID}" > .env

# Run script
python3 image_uploader.py > /var/log/image_upload.log 2>&1 &
'''

iam = boto3.client("iam", region_name=os.getenv("AWS_REGION", "us-east-1"))
INSTANCE_PROFILE_NAME = "LabInstanceProfile"

def ensure_instance_profile():
    try:
        iam.get_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
    except iam.exceptions.NoSuchEntityException:
        iam.create_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
        iam.add_role_to_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME,
            RoleName="LabRole"
        )

ensure_instance_profile()

def launch_instance():
    response = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType='t2.micro',
        KeyName='vockey',
        MinCount=1,
        MaxCount=1,
        UserData=USER_DATA,
        IamInstanceProfile={'Name': INSTANCE_PROFILE_NAME},
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f'CPD-Coursework-EC2-{STUDENT_ID}'}]
            }
        ]
    )

    instance_id = response['Instances'][0]['InstanceId']
    print(f"✅ EC2 instance launched: {instance_id}")

launch_instance()
