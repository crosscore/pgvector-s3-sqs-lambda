# rag-pgvector/backend/pdf_processing/sqs_listener.py
import boto3
import json
import logging
from botocore.exceptions import ClientError
from .s3_operations import S3Operations, fetch_pdf_from_s3
from .pdf_extractor import extract_and_process_pdf
from config import S3_DB_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SQS_QUEUE_URL, LOCAL_PDF_FOLDER

logger = logging.getLogger(__name__)

sqs_client = boto3.client('sqs',
    endpoint_url=S3_DB_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1')

s3_ops = S3Operations(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_DB_URL)

def process_message(message):
    try:
        message_body = json.loads(message['Body'])
        bucket_name = message_body['bucket_name']
        object_key = message_body['object_key']

        # Download PDF from S3
        local_pdf_path = fetch_pdf_from_s3(s3_ops, bucket_name, object_key, LOCAL_PDF_FOLDER)
        if not local_pdf_path:
            logger.error(f"Failed to download PDF: {object_key}")
            return False

        # Process PDF
        processed_data = extract_and_process_pdf(local_pdf_path)
        if processed_data is None:
            logger.error(f"Failed to process PDF: {local_pdf_path}")
            return False

        # TODO: Send processed_data to vectorization module
        logger.info(f"Successfully processed PDF: {object_key}")
        return True

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in message body: {message['Body']}")
        return False
    except KeyError as e:
        logger.error(f"Missing key in message body: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return False

def start_sqs_listener():
    logger.info("Starting SQS listener")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            messages = response.get('Messages', [])
            for message in messages:
                if process_message(message):
                    # Delete the message from the queue if processed successfully
                    sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )

        except ClientError as e:
            logger.error(f"Error receiving/deleting message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in SQS listener: {str(e)}")

if __name__ == "__main__":
    start_sqs_listener()
