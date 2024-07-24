# rag-pgvector/backend/src/data_processing/s3/s3_utils.py
import boto3
from config import *

def create_s3_client():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_REGION)

def create_sqs_client():
    return boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_REGION)

s3_client = create_s3_client()
sqs_client = create_sqs_client()
