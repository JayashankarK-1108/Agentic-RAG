
import boto3
import hashlib
import traceback
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

# Presigned URLs valid for 1 year — regenerated on every ingestion run
PRESIGNED_URL_EXPIRY = 31536000

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def test_s3_connection():
    """
    Verify S3 bucket is reachable and credentials have access.
    Returns (success: bool, message: str).
    """
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        return True, f"Bucket '{S3_BUCKET_NAME}' in region '{AWS_REGION}' is accessible"
    except Exception as e:
        return False, f"Cannot access bucket '{S3_BUCKET_NAME}': {e}"

def upload_image(file_bytes, filename):
    """
    Upload image bytes to S3 and return a presigned URL valid for 7 days.
    Presigned URLs work without making the bucket public.
    Returns the URL string, or None if upload fails.
    """
    try:
        content_hash = hashlib.md5(file_bytes).hexdigest()
        key = f"images/{content_hash}_{filename}"
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType="image/png",
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXPIRY,
        )
        return url
    except Exception as e:
        print(f"  [S3 ERROR] Failed to upload '{filename}': {e}")
        print(traceback.format_exc())
        return None
