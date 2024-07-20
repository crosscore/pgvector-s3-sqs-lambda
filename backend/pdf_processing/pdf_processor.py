# rag-pgvector/backend/pdf_processing/pdf_processor.py

import os
import json
import logging
import boto3
import pandas as pd
from botocore.exceptions import ClientError
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class S3Operations:
    def __init__(self, aws_access_key_id, aws_secret_access_key, endpoint_url, use_local_s3=True):
        self.use_local_s3 = use_local_s3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url if use_local_s3 else None,
            region_name='us-east-1' if use_local_s3 else None
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

class PDFProcessor:
    def __init__(self):
        self.s3_ops = S3Operations(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_DB_URL)
        self.sqs_client = boto3.client('sqs',
            endpoint_url=S3_DB_URL if USE_LOCAL_S3 else None,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1' if USE_LOCAL_S3 else None
        )
        self.text_splitter = CharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separator=SEPARATOR
        )

    def fetch_pdf_from_s3(self, bucket_name, object_key, local_folder):
        local_path = os.path.join(local_folder, object_key.split('/')[-1])
        return self.s3_ops.download_pdf(bucket_name, object_key, local_path)

    def extract_text_from_pdf(self, file_path):
        loader = PyPDFLoader(file_path)
        return loader.load()

    def process_pdf_to_dataframe(self, file_name, pages):
        data = []
        total_chunks = 0
        for page_num, page in enumerate(pages):
            page_text = page.page_content
            chunks = self.text_splitter.split_text(page_text) if page_text else []

            if not chunks and page_text:
                chunks = [page_text]

            for chunk in chunks:
                data.append({
                    'file_name': file_name,
                    'file_type': 'pdf',
                    'page': str(page_num),
                    'chunk_number': total_chunks,
                    'content': chunk
                })
                total_chunks += 1

        return pd.DataFrame(data), total_chunks

    def extract_and_process_pdf(self, file_path):
        file_name = os.path.basename(file_path)
        pages = self.extract_text_from_pdf(file_path)

        if not pages:
            logger.warning(f"No text extracted from {file_name}")
            return None

        logger.info(f"Processing {file_name}: {len(pages)} pages")

        df, total_chunks = self.process_pdf_to_dataframe(file_name, pages)
        if df.empty:
            logger.warning(f"No chunks created for {file_name}")
            return None

        logger.info(f"Processed {file_name}: {len(pages)} pages, {total_chunks} chunks")
        return df

    def process_message(self, message):
        try:
            message_body = json.loads(message['Body'])
            bucket_name = message_body['bucket_name']
            object_key = message_body['object_key']

            # Download PDF from S3
            local_pdf_path = self.fetch_pdf_from_s3(bucket_name, object_key, LOCAL_PDF_FOLDER)
            if not local_pdf_path:
                logger.error(f"Failed to download PDF: {object_key}")
                return False

            # Process PDF
            processed_data = self.extract_and_process_pdf(local_pdf_path)
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

    def start_sqs_listener(self):
        logger.info("Starting SQS listener")
        while True:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20
                )

                messages = response.get('Messages', [])
                for message in messages:
                    if self.process_message(message):
                        # Delete the message from the queue if processed successfully
                        self.sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )

            except ClientError as e:
                logger.error(f"Error receiving/deleting message: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in SQS listener: {str(e)}")

    def test_pdf_download(self):
        logger.info(f"Initializing S3 operations for PDF download test (Using {'local s3_db' if USE_LOCAL_S3 else 'AWS S3'})")

        for pdf_file in TEST_PDF_FILES:
            logger.info(f"Attempting to download {pdf_file}")
            local_path = self.fetch_pdf_from_s3(S3_BUCKET_NAME, pdf_file, LOCAL_PDF_FOLDER)

            if local_path:
                logger.info(f"Successfully downloaded {pdf_file} to {local_path}")
            else:
                logger.warning(f"Failed to download {pdf_file}")

        logger.info("PDF download test completed")

def main():
    processor = PDFProcessor()
    if RUN_MODE == 'pdf_processing':
        processor.start_sqs_listener()
    elif RUN_MODE == 'test_pdf_download':
        processor.test_pdf_download()
    else:
        logger.error(f"Invalid RUN_MODE: {RUN_MODE}")

if __name__ == "__main__":
    main()
