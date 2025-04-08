import boto3
import os
from dotenv import load_dotenv

load_dotenv()

student_id = os.getenv("STUDENT_ID", "00000000")
topic_name = f"face-comparison-topic-{student_id}"

sns = boto3.client("sns", region_name=f"{os.getenv("AWS_REGION", "us-east-1")}")

def get_topic_arn(name):
    response = sns.list_topics()
    for topic in response["Topics"]:
        if name in topic["TopicArn"]:
            return topic["TopicArn"]
    return None

def subscribe_email(email):
    topic_arn = get_topic_arn(topic_name)
    if not topic_arn:
        print(f"❌ Could not find SNS topic: {topic_name}")
        return

    response = sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email
    )

    print(f"📨 Confirmation email sent to {email}")
    print(f"🆔 Subscription ARN (pending confirmation): {response['SubscriptionArn']}")

if __name__ == "__main__":
    email_to_subscribe = os.getenv("SNS_EMAIL")
    if not email_to_subscribe:
        print("❌ SNS_EMAIL not set in .env file")
    else:
        subscribe_email(email_to_subscribe)