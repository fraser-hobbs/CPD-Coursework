import boto3
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

student_id = os.getenv("STUDENT_ID", "00000000")
bucket_name = f"face-comparison-bucket-{student_id}"

s3 = boto3.client("s3")

# List of images to upload
image_files = [
    "image1.jpg",
    "image2.jpg",
    "image3.jpg",
    "image4.jpg",
    "image5.jpg"
]

def upload_image(file_to_upload):
    object_key = os.path.basename(file_to_upload)
    try:
        with open(file_to_upload, "rb") as file:
            s3.upload_fileobj(file, bucket_name, object_key)
            print(f"✅ Uploaded {file_to_upload} to s3://{bucket_name}/{object_key}")
    except Exception as e:
        print(f"❌ Failed to upload {file_to_upload}: {e}")

if __name__ == "__main__":

    upload_image("groupphoto.png")

    for image in image_files:
        upload_image(image)
        time.sleep(30)