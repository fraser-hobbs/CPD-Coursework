import json
import os
import io
import logging
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
secretsmanager = boto3.client("secretsmanager")

# Load secret values
try:
    secret_response = secretsmanager.get_secret_value(SecretId="cpd-coursework-secret")
    secret_data = json.loads(secret_response["SecretString"])
except ClientError as e:
    logger.error(f"Failed to load secrets: {str(e)}")
    raise e

BUCKET = secret_data["BUCKET_NAME"]
TABLE_NAME = f"FaceComparisonResults-{secret_data['STUDENT_ID']}"
GROUP_PHOTO_KEY = os.getenv("GROUP_PHOTO_KEY", "groupphoto.png")

# Initialize AWS resources after secrets are loaded
s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    logger.info("📥 Event received: %s", json.dumps(event))

    # Get the latest uploaded object (excluding group photo)
    response = s3.list_objects_v2(Bucket=BUCKET)
    if "Contents" not in response or len(response["Contents"]) <= 1:
        logger.warning("❌ No uploaded image found.")
        return {"statusCode": 400, "body": "No uploaded image found."}

    objects = sorted(
        [obj for obj in response["Contents"] if obj["Key"] != GROUP_PHOTO_KEY],
        key=lambda x: x["LastModified"],
        reverse=True
    )

    if not objects:
        logger.warning("❌ No valid target image found.")
        return {"statusCode": 400, "body": "No valid target image found."}

    target_key = objects[0]["Key"]
    logger.info(f"📸 Latest uploaded image key: {target_key}")

    if not target_key.lower().endswith(('.jpg', '.jpeg', '.png')):
        logger.warning("❌ Unsupported image format.")
        return {"statusCode": 400, "body": "Unsupported image format."}

    # Download group photo and uploaded image
    source_bytes = s3.get_object(Bucket=BUCKET, Key=GROUP_PHOTO_KEY)["Body"].read()
    target_bytes = s3.get_object(Bucket=BUCKET, Key=target_key)["Body"].read()

    logger.info(f"📂 Group photo size: {len(source_bytes)} bytes, Uploaded image size: {len(target_bytes)} bytes")
    logger.info(f"🔍 Comparing '{GROUP_PHOTO_KEY}' to '{target_key}'")

    # Detect faces in the group photo
    group_faces = rekognition.detect_faces(Image={"Bytes": source_bytes}, Attributes=["ALL"])
    if not group_faces["FaceDetails"]:
        logger.warning("❌ No faces detected in group photo.")
        return {"statusCode": 400, "body": "No faces detected in group photo."}

    logger.info(f"👥 Detected {len(group_faces['FaceDetails'])} faces in group photo.")

    # Log each face bounding box
    for idx, face in enumerate(group_faces["FaceDetails"]):
        box = face["BoundingBox"]
        logger.info(f"📏 Face {idx+1} bounding box: Top={box['Top']:.2f}, Left={box['Left']:.2f}, Width={box['Width']:.2f}, Height={box['Height']:.2f}")

    # Save face coordinates for further use (e.g., cropping or labeling)
    face_boxes = [face["BoundingBox"] for face in group_faces["FaceDetails"]]
    logger.info(f"📦 Collected {len(face_boxes)} bounding boxes from group photo.")

    # Compare the group photo to the uploaded image directly
    result = rekognition.compare_faces(
        SourceImage={"Bytes": source_bytes},
        TargetImage={"Bytes": target_bytes},
        SimilarityThreshold=80
    )

    if not result["FaceMatches"]:
        logger.info("⚠️ No face matches found.")
        similarity = 0
    else:
        similarity = result["FaceMatches"][0]["Similarity"]

    logger.info(f"✅ Face similarity: {similarity}")

    # Estimate brightness using Rekognition labels
    labels = rekognition.detect_labels(
        Image={"Bytes": target_bytes},
        MaxLabels=10
    )

    logger.info("🔖 Rekognition Labels: %s", json.dumps(labels["Labels"], indent=2))

    brightness = next(
        (label["Confidence"] for label in labels["Labels"]
         if label["Name"].lower() in ["light", "brightness"]),
        0
    )

    # Store results in DynamoDB
    logger.info("💾 Storing comparison results in DynamoDB...")
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        "ImageID": target_key,
        "Similarity": Decimal(str(similarity)),
        "ForegroundBrightness": Decimal(str(brightness)),
        "BackgroundBrightness": Decimal("0")
    })
    logger.info("✅ DynamoDB put_item completed.")

    return {
        "statusCode": 200,
        "body": "Processed latest image against group photo"
    }