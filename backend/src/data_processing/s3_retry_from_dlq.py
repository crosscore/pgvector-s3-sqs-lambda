import os
import boto3
import json
import time
from botocore.exceptions import ClientError
from s3_utils import s3_client
from config import S3_BUCKET_NAME, DEAD_LETTER_QUEUE_URL, LOCAL_DOWNLOAD_PATH

sqs_client = boto3.client('sqs')

MAX_RETRIES = 3
BACKOFF_TIME = 5  # seconds

def calculate_file_hash(file_path):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_message_from_dlq(message):
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
        print(f"Error processing {s3_key} from DLQ: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False

def process_dlq_messages():
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=DEAD_LETTER_QUEUE_URL,
                MaxNumberOfMessages=1,  # Adjust as needed
                WaitTimeSeconds=20,
                VisibilityTimeout=300,
            )

            if 'Messages' not in response:
                print("No messages in DLQ. Waiting...")
                time.sleep(BACKOFF_TIME)
                continue

            for message in response['Messages']:
                if process_message_from_dlq(message):
                    try:
                        sqs_client.delete_message(
                            QueueUrl=DEAD_LETTER_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        print("Successfully processed and deleted DLQ message")
                    except ClientError as e:
                        print(f"Error deleting message from DLQ: {e}")
                else:
                    print(f"Failed to process DLQ message: {message['MessageId']}")

        except ClientError as e:
            print(f"Error receiving messages from DLQ: {e}")
            time.sleep(BACKOFF_TIME)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(BACKOFF_TIME)

if __name__ == "__main__":
    os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
    print("Processing messages from DLQ...")
    process_dlq_messages()
