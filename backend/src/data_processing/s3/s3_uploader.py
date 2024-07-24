# rag-pgvector/backend/src/data_processing/s3/s3_uploader.py
import os
import json
from botocore.exceptions import ClientError
from s3_utils import s3_client, sqs_client
from config import S3_BUCKET_NAME, SQS_QUEUE_URL, LOCAL_UPLOAD_PATH
from dotenv import load_dotenv

load_dotenv()

LOCAL_UPLOAD_PATH = os.getenv("LOCAL_UPLOAD_PATH")

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

def send_sqs_message(queue_url, message_body, message_group_id):
    try:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=message_group_id
        )
        print(f"Sent message to SQS: {message_body}")
        return response['MessageId']
    except ClientError as e:
        print(f"Error sending message to SQS: {e}")
        return None

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
                send_sqs_message(SQS_QUEUE_URL, message_body, filename)

if __name__ == "__main__":
    print("Uploading PDFs and sending SQS messages...")
    upload_pdfs_and_send_messages()
    print("Upload process completed.")
