# rag-pgvector/backend/src/data_processing/s3_sqs_downloader.py
import boto3
import json
import os
from botocore.exceptions import ClientError
from config import *

# Create boto3 clients
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)
sqs_client = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"Uploaded {file_name} to {bucket}/{object_name}")
        return True
    except ClientError as e:
        print(f"Error uploading {file_name}: {e}")
        return False

def send_sqs_message(queue_url, message_body):
    try:
        response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
        print(f"Sent message to SQS: {message_body}")
        return response['MessageId']
    except ClientError as e:
        print(f"Error sending message to SQS: {e}")
        return None

def process_message(message):
    body = json.loads(message['Body'])
    s3_key = body['Records'][0]['s3']['object']['key']
    local_file_path = os.path.join(LOCAL_DOWNLOAD_PATH, os.path.basename(s3_key))
    try:
        s3_client.download_file(S3_BUCKET_NAME, s3_key, local_file_path)
        print(f"Downloaded {s3_key} to {local_file_path}")
        return True
    except ClientError as e:
        print(f"Error downloading {s3_key}: {e}")
        return False

def upload_pdfs_and_send_messages():
    for filename in os.listdir(LOCAL_UPLOAD_PATH):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(LOCAL_UPLOAD_PATH, filename)
            if upload_file(file_path, S3_BUCKET_NAME, filename):
                message_body = {
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": S3_BUCKET_NAME},
                                "object": {"key": filename}
                            }
                        }
                    ]
                }
                send_sqs_message(SQS_QUEUE_URL, message_body)

def download_pdfs_from_sqs():
    while True:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )
        if 'Messages' in response:
            for message in response['Messages']:
                if process_message(message):
                    sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
        else:
            print("No messages in queue. Waiting...")
            break  # Exit the loop if no messages are found

if __name__ == "__main__":
    os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
    print("Uploading PDFs and sending SQS messages...")
    upload_pdfs_and_send_messages()
    print("Downloading PDFs from S3 based on SQS messages...")
    download_pdfs_from_sqs()
    print("Process completed.")
