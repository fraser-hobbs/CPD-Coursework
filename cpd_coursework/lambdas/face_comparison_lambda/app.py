import os
import json
import boto3

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

BUCKET = os.environ["BUCKET_NAME"]
TABLE_NAME = f"FaceComparisonResults-{os.environ['STUDENT_ID']}"
SNS_TOPIC_ARN = os.environ["TOPIC_ARN"]
GROUP_PHOTO_KEY = "groupphoto.png"

def lambda_handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        target_key = body["key"]

        # Download group photo
        source_obj = s3.get_object(Bucket=BUCKET, Key=GROUP_PHOTO_KEY)
        source_bytes = source_obj["Body"].read()

        # Download uploaded image
        target_obj = s3.get_object(Bucket=BUCKET, Key=target_key)
        target_bytes = target_obj["Body"].read()

        # Rekognition face comparison
        comparison = rekognition.compare_faces(
            SourceImage={"Bytes": source_bytes},
            TargetImage={"Bytes": target_bytes},
            SimilarityThreshold=80
        )

        similarity = comparison["FaceMatches"][0]["Similarity"] if comparison["FaceMatches"] else 0

        # Rekognition label detection for brightness
        labels = rekognition.detect_labels(
            Image={"Bytes": target_bytes},
            MaxLabels=10
        )

        brightness = 0
        for label in labels["Labels"]:
            if label["Name"].lower() in ["light", "brightness"]:
                brightness = label["Confidence"]
                break

        # Store results in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            "ImageID": target_key,
            "Similarity": similarity,
            "Brightness": brightness
        })

        # Trigger SNS alert if conditions met
        if similarity == 0 and brightness < 10:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="No face match & image is too dark",
                Message=f"Image '{target_key}' had no face match and brightness {brightness:.2f}"
            )

    return {
        "statusCode": 200,
        "body": "Processed image against group photo"
    }