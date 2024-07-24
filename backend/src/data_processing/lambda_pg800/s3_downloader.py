# s3_downloader.py
import os
import json
import time
import hashlib
import boto3
from botocore.exceptions import ClientError
from config import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS認証情報を明示的に指定せずにクライアントを初期化
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

MAX_RETRIES = 3
BACKOFF_TIME = 5  # seconds
VISIBILITY_TIMEOUT = 30  # 30 seconds

def calculate_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_message(message):
    body = json.loads(message['Body'])
    s3_key = body['Records'][0]['s3']['object']['key']
    local_file_path = os.path.join('/tmp', os.path.basename(s3_key))

    if os.path.exists(local_file_path):
        logger.info(f"File {local_file_path} already exists. Skipping download.")
        return True

    temp_file_path = local_file_path + '.temp'
    try:
        s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_file_path)
        file_hash = calculate_file_hash(temp_file_path)

        s3_object = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        if 'x-amz-meta-file-hash' in s3_object['Metadata']:
            s3_hash = s3_object['Metadata']['x-amz-meta-file-hash']
            if file_hash != s3_hash:
                raise ValueError("File hash mismatch")

        os.rename(temp_file_path, local_file_path)
        logger.info(f"Downloaded and verified {s3_key} to {local_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing {s3_key}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False

def receive_sqs_message():
    try:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=VISIBILITY_TIMEOUT,
            AttributeNames=['ApproximateReceiveCount']
        )
        if 'Messages' in response:
            return response['Messages'][0]
        else:
            logger.info("No messages in queue.")
            return None
    except ClientError as e:
        logger.error(f"Error receiving message from SQS: {e}")
        raise

def delete_sqs_message(receipt_handle):
    try:
        sqs_client.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        logger.info("SQS message deleted successfully.")
    except ClientError as e:
        logger.error(f"Error deleting message from SQS: {e}")
        raise

def move_to_dlq(message):
    try:
        sqs_client.send_message(
            QueueUrl=DEAD_LETTER_QUEUE_URL,
            MessageBody=message['Body'],
            MessageAttributes={
                'FailureReason': {
                    'DataType': 'String',
                    'StringValue': 'Exceeded max retry attempts'
                }
            }
        )
        logger.info("Message moved to Dead Letter Queue.")
    except ClientError as e:
        logger.error(f"Error moving message to DLQ: {e}")
        raise

def process_sqs_message():
    message = receive_sqs_message()
    if not message:
        return None

    receive_count = int(message['Attributes']['ApproximateReceiveCount'])

    if process_message(message):
        delete_sqs_message(message['ReceiptHandle'])
        return os.path.join('/tmp', os.path.basename(json.loads(message['Body'])['Records'][0]['s3']['object']['key']))
    else:
        if receive_count >= MAX_RETRIES:
            logger.warning(f"Message failed after {MAX_RETRIES} attempts. Moving to Dead Letter Queue.")
            move_to_dlq(message)
            delete_sqs_message(message['ReceiptHandle'])
        else:
            logger.info(f"Processing failed. Message will return to queue for retry. Attempt: {receive_count}")
        return None

if __name__ == "__main__":
    logger.info("Starting S3 downloader...")
    while True:
        try:
            result = process_sqs_message()
            if result:
                logger.info(f"Successfully processed PDF: {result}")
            time.sleep(BACKOFF_TIME)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(BACKOFF_TIME)
