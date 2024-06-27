# utils.py
import boto3
import logging
from botocore.config import Config

logger = logging.getLogger(__name__)

def generate_presigned_url(bucket_name, object_name, operation='put_object', expiration=300):
    s3_client = boto3.client('s3', region_name='us-west-1', config=Config(signature_version='s3v4'))
    try:
        response = s3_client.generate_presigned_url(operation,
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        logger.error(e)
        return None

    return response

def delete_s3_file(bucket_name, object_name):
    s3_client = boto3.client('s3', region_name='us-west-1', config=Config(signature_version='s3v4'))
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
    except Exception as e:
        logger.error(e)
        raise Exception("Failed to delete S3 file: " + str(e))
