# rag-pgvector/backend/src/data_processing/s3/s3_downloader.py
import os
import json
import time
import hashlib
from botocore.exceptions import ClientError
from s3_utils import s3_client, sqs_client
from config import S3_BUCKET_NAME, SQS_QUEUE_URL, LOCAL_DOWNLOAD_PATH, DEAD_LETTER_QUEUE_URL

MAX_RETRIES = 3
BACKOFF_TIME = 5  # seconds
VISIBILITY_TIMEOUT = 300  # 5 minutes

def calculate_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_message(message):
    body = json.loads(message['Body'])
    s3_key = body['Records'][0]['s3']['object']['key']
    local_file_path = os.path.join(LOCAL_DOWNLOAD_PATH, os.path.basename(s3_key))

    temp_file_path = local_file_path + '.temp'
    try:
        s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_file_path)
        file_hash = calculate_file_hash(temp_file_path)

        # Verify the hash with S3 object metadata if available
        s3_object = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        if 'x-amz-meta-file-hash' in s3_object['Metadata']:
            s3_hash = s3_object['Metadata']['x-amz-meta-file-hash']
            if file_hash != s3_hash:
                raise ValueError("File hash mismatch")

        os.rename(temp_file_path, local_file_path)
        print(f"Downloaded and verified {s3_key} to {local_file_path}")
        return True
    except Exception as e:
        print(f"Error processing {s3_key}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False

def download_pdfs_from_sqs():
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=VISIBILITY_TIMEOUT,
                AttributeNames=['ApproximateReceiveCount']
            )

            if 'Messages' not in response:
                print("No messages in queue. Waiting...")
                continue

            for message in response['Messages']:
                receive_count = int(message['Attributes']['ApproximateReceiveCount'])

                if process_message(message):
                    try:
                        sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        print(f"Successfully processed and deleted message")
                    except ClientError as e:
                        print(f"Error deleting message: {e}")
                else:
                    if receive_count >= MAX_RETRIES:
                        print(f"Message failed after {MAX_RETRIES} attempts. Moving to Dead Letter Queue.")
                        try:
                            # Move to Dead Letter Queue
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
                            # Delete from main queue
                            sqs_client.delete_message(
                                QueueUrl=SQS_QUEUE_URL,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                        except ClientError as e:
                            print(f"Error moving message to DLQ: {e}")
                    else:
                        print(f"Processing failed. Message will return to queue for retry. Attempt: {receive_count}")
                        # Message automatically returns to queue after visibility timeout

        except ClientError as e:
            print(f"Error receiving message from SQS: {e}")
            time.sleep(BACKOFF_TIME)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(BACKOFF_TIME)

if __name__ == "__main__":
    os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
    print("Downloading PDFs from S3 based on SQS messages...")
    download_pdfs_from_sqs()
