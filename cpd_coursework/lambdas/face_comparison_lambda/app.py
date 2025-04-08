import json
import boto3
import os
from decimal import Decimal

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
dynamodb = boto3.resource("dynamodb")
secretsmanager = boto3.client("secretsmanager")

secret_response = secretsmanager.get_secret_value(SecretId="cpd-coursework-secret")
secret_data = json.loads(secret_response["SecretString"])

BUCKET = secret_data["BUCKET_NAME"]
TABLE_NAME = f"FaceComparisonResults-{secret_data['STUDENT_ID']}"
GROUP_PHOTO_KEY = "groupphoto.png"

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))

    # Get the latest uploaded object in the S3 bucket (excluding the group photo)
    response = s3.list_objects_v2(Bucket=BUCKET)
    if "Contents" not in response or len(response["Contents"]) <= 1:
        print("No uploaded image found.")
        return {"statusCode": 400, "body": "No uploaded image found."}

    objects = sorted(
        [obj for obj in response["Contents"] if obj["Key"] != GROUP_PHOTO_KEY],
        key=lambda x: x["LastModified"],
        reverse=True
    )

    if not objects:
        print("No valid target image found.")
        return {"statusCode": 400, "body": "No valid target image found."}

    target_key = objects[0]["Key"]
    print(f"Latest uploaded image key: {target_key}")

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
        "Similarity": Decimal(str(similarity)),
        "Brightness": Decimal(str(brightness))
    })

    return {
        "statusCode": 200,
        "body": "Processed latest image against group photo"
    }