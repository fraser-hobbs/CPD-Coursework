import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secrets_client = boto3.client("secretsmanager")

# Fetch the SNS topic ARN from Secrets Manager
try:
    secret_value = secrets_client.get_secret_value(SecretId="cpd-coursework-secret")
    secret_dict = json.loads(secret_value["SecretString"])
    SNS_TOPIC_ARN = secret_dict["sns_topic_arn"]
except Exception as e:
    print(f"Error fetching secret: {e}")
    raise

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    for record in event.get("Records", []):
        if record.get("eventName") != "INSERT":
            continue

        new_image = record.get("dynamodb", {}).get("NewImage", {})
        if not new_image:
            print("No NewImage found in the record.")
            continue

        try:
            image1 = new_image["Image1"]["S"]
            image2 = new_image["Image2"]["S"]
            similarity = float(new_image["Similarity"]["N"])
            foreground_brightness = float(new_image.get("ForegroundBrightness", {}).get("N", "0"))
            background_brightness = float(new_image.get("BackgroundBrightness", {}).get("N", "0"))
        except KeyError as e:
            print(f"Missing expected key: {e}")
            continue
        except ValueError as e:
            print(f"Invalid numeric value: {e}")
            continue

        if similarity == 0.0 and background_brightness < 10:
            message = (
                f"No face match found. Background brightness: {background_brightness:.2f}. "
                f"Foreground brightness: {foreground_brightness:.2f}. "
                f"Images compared: {image1} vs {image2}."
            )
            print("Sending critical notification:", message)
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message,
                    Subject="No Face Match & Low Brightness Alert"
                )
            except Exception as e:
                print(f"Failed to publish to SNS: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Notifications processed.")
    }
