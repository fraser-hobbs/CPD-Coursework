## CPD Coursework – Face Comparison Project

This serverless application processes images uploaded to an S3 bucket. When a new image is uploaded, it compares the detected face(s) to those in a predefined group photo using AWS Rekognition. If a match is found, a notification is sent via SNS.

This project is designed as part of the Cloud Platform Development coursework to demonstrate understanding of AWS services.

## Deployment Guide

This guide outlines the steps required to deploy the CPD_Coursework project to your AWS account.

### Prerequisites

- AWS CLI installed and configured.
- Python 3.11 installed.
- An AWS account with permissions to deploy Lambda, S3, SNS, SQS, DynamoDB, and Rekognition services.

### Step 1: Clone the Repository

```bash
git clone https://github.com/fraser-hobbs/CPD_Coursework.git
cd CPD_Coursework
```

### Step 2: Configure Environment

Create a `.env` file in the project root with the following contents:

```
STUDENT_ID=
AWS_PROFILE=(this refers to the ~/.aws/credentials use 'default' if not set) 
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=
GITHUB_USERNAME=fraser-hobbs (leave as this unless forked repo)
GITHUB_REPO=CPD-Coursework (leave as this unless forked repo)
SNS_EMAIL=john.doe@example.com

```

These variables are used for consistent naming and deployment.

### Step 3: Set Up Python Environment

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Use `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Step 4: Deploy the Application

Use the provided deployment script:

```bash
python deploy.py
```

To tear down the infrastructure:

```bash
python destroy.py
```

## Author

Fraser Hobbs
