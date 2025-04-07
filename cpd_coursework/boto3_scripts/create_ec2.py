import boto3
import os
import json
secretsmanager = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))

secret_response = secretsmanager.get_secret_value(SecretId="cpd-coursework-secret")
secret_data = json.loads(secret_response["SecretString"])

# Replace with your key pair and security group
KEY_NAME = "CPD"
AMI_ID = "ami-0c02fb55956c7d316"

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

def launch_instance():
    response = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_NAME,
        UserData=USER_DATA,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'CPD-Coursework-EC2'}]
            }
        ]
    )

    instance_id = response['Instances'][0]['InstanceId']
    print(f"✅ EC2 instance launched: {instance_id}")

if __name__ == "__main__":
    launch_instance()
