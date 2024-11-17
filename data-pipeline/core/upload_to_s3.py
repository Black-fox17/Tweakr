import os
import boto3

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def upload_to_s3(file_path, object_name):
    s3.upload_file(file_path, S3_BUCKET_NAME, object_name)
    return f"s3://{S3_BUCKET_NAME}/{object_name}"
