# utils.py
import boto3
import logging
from botocore.config import Config

logger = logging.getLogger(__name__)

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client('s3', region_name='us-west-1', config=Config(signature_version='s3v4'))
    try:
        response = s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        logger.error(e)
        return None

    return response
