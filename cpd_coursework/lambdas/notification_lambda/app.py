import boto3
import json

sns = boto3.client('sns')
secrets_client = boto3.client("secretsmanager")

# Fetch the SNS topic ARN from Secrets Manager
try:
    secret_value = secrets_client.get_secret_value(SecretId="cpd-coursework-secret")
    secret_dict = json.loads(secret_value["SecretString"])
    SNS_TOPIC_ARN = secret_dict["SNS_TOPIC_ARN"]
except Exception as e:
    print(f"Error fetching secret: {e}")
    raise

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    for record in event.get("Records", []):
        try:
            if record.get("eventName") != "INSERT":
                continue

            new_image = record["dynamodb"]["NewImage"]
            image_name = new_image.get("ImageID", {}).get("S", "Unknown")
            similarity = float(new_image.get("Similarity", {}).get("N", 0))
            foreground_brightness = float(new_image.get("ForegroundBrightness", {}).get("N", 0))
            background_brightness = float(new_image.get("BackgroundBrightness", {}).get("N", 0))

            if similarity == 0.0 and background_brightness < 10:
                message = (
                    f"No face match found. Background brightness: {background_brightness:.2f}. "
                    f"Foreground brightness: {foreground_brightness:.2f}. "
                    f"Image name: {image_name}."
                )
                print("Sending critical notification:", message)
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message,
                    Subject="No Face Match & Low Brightness Alert"
                )
        except Exception as e:
            print(f"Error processing record: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Notifications processed.")
    }
