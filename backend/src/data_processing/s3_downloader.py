import os
import json
from botocore.exceptions import ClientError
from s3_utils import s3_client, sqs_client
from config import S3_BUCKET_NAME, SQS_QUEUE_URL, LOCAL_DOWNLOAD_PATH

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
    print("Downloading PDFs from S3 based on SQS messages...")
    download_pdfs_from_sqs()
    print("Download process completed.")
