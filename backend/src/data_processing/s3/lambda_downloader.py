import os
import json
import hashlib
import boto3
from botocore.exceptions import ClientError

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
DEAD_LETTER_QUEUE_URL = os.environ['DEAD_LETTER_QUEUE_URL']

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

MAX_RETRIES = 3
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
    local_file_path = f'/tmp/{os.path.basename(s3_key)}'

    if os.path.exists(local_file_path):
        print(f"File {local_file_path} already exists. Skipping download.")
        return True

    temp_file_path = f'{local_file_path}.temp'
    for attempt in range(MAX_RETRIES):
        try:
            s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_file_path)
            file_hash = calculate_file_hash(temp_file_path)

            s3_object = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            if 'x-amz-meta-file-hash' in s3_object['Metadata']:
                s3_hash = s3_object['Metadata']['x-amz-meta-file-hash']
                if file_hash != s3_hash:
                    raise ValueError("File hash mismatch")

            os.rename(temp_file_path, local_file_path)
            print(f"Downloaded and verified {s3_key} to {local_file_path}")
            return True
        except Exception as e:
            print(f"Error processing {s3_key} (attempt {attempt + 1}): {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if attempt == MAX_RETRIES - 1:
                return False
    return False

def lambda_handler(event, context):
    try:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0,
            VisibilityTimeout=VISIBILITY_TIMEOUT,
            AttributeNames=['ApproximateReceiveCount']
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            return {'statusCode': 200, 'body': json.dumps('No messages to process')}

        message = response['Messages'][0]
        receive_count = int(message['Attributes']['ApproximateReceiveCount'])

        if process_message(message):
            sqs_client.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
            print("Successfully processed and deleted message")
        elif receive_count >= MAX_RETRIES:
            print(f"Message failed after {MAX_RETRIES} attempts. Moving to Dead Letter Queue.")
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
            sqs_client.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
        else:
            print(f"Processing failed. Message will return to queue for retry. Attempt: {receive_count}")

        return {'statusCode': 200, 'body': json.dumps('Processing complete')}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {'statusCode': 500, 'body': json.dumps('Error processing messages')}
