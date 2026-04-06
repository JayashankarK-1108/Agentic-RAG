
import boto3
import uuid
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

s3 = boto3.client("s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION)

def upload_image(file_bytes, filename):
    try:
        key = f"images/{uuid.uuid4()}_{filename}"
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=file_bytes, ContentType="image/png")
        return f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
    except Exception as e:
        print(f"Error uploading image to S3: {e}")
        return None
