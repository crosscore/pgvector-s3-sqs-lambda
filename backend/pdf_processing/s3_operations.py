# rag-pgvector/backend/s3_operations.py
import boto3
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Operations:
    def __init__(self, aws_access_key_id, aws_secret_access_key, endpoint_url):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url
        )

    def download_pdf(self, bucket_name, object_key, local_path):
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(bucket_name, object_key, local_path)
            logger.info(f"Successfully downloaded {object_key} to {local_path}")
            return local_path
        except ClientError as e:
            logger.error(f"Error downloading {object_key}: {str(e)}")
            return None

def fetch_pdf_from_s3(s3_ops, bucket_name, object_key, local_folder):
    local_path = os.path.join(local_folder, object_key.split('/')[-1])
    return s3_ops.download_pdf(bucket_name, object_key, local_path)
