# utils.py
import boto3
import logging
from botocore.config import Config
from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_client():
    s3_client_kwargs = {
        "region_name": getattr(settings, "AWS_DEFAULT_REGION", "us-east-1")
    }

    aws_access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    aws_secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

    if aws_access_key and aws_secret_key:
        s3_client_kwargs.update(
            {
                "aws_access_key_id": aws_access_key,
                "aws_secret_access_key": aws_secret_key,
            }
        )

    return boto3.client(
        "s3", config=Config(signature_version="s3v4"), **s3_client_kwargs
    )


def generate_presigned_url(object_name, operation="put_object", expiration=300):
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            operation,
            Params={
                "Bucket": getattr(settings, "AWS_S3_BUCKET_NAME", "iexpense-receipts"),
                "Key": object_name,
            },
            ExpiresIn=expiration,
        )
    except Exception as e:
        logger.error(e)
        return None

    return response


def delete_s3_file(object_name):
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(
            Bucket=getattr(settings, "AWS_S3_BUCKET_NAME", "iexpense-receipts"),
            Key=object_name,
        )
    except Exception as e:
        logger.error(e)
        raise Exception("Failed to delete S3 file: " + str(e))
