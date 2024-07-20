# rag-pgvector/backend/main.py

import logging
import threading
from pdf_processing.sqs_listener import start_sqs_listener
from api.routes import start_api_server
from config import RUN_MODE, TEST_PDF_FILES, S3_BUCKET_NAME, LOCAL_PDF_FOLDER
from pdf_processing.s3_operations import S3Operations, fetch_pdf_from_s3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_download():
    from config import S3_DB_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

    logger.info("Initializing S3 operations for PDF download test")
    s3_ops = S3Operations(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_DB_URL)

    for pdf_file in TEST_PDF_FILES:
        logger.info(f"Attempting to download {pdf_file}")
        local_path = fetch_pdf_from_s3(s3_ops, S3_BUCKET_NAME, pdf_file, LOCAL_PDF_FOLDER)

        if local_path:
            logger.info(f"Successfully downloaded {pdf_file} to {local_path}")
        else:
            logger.warning(f"Failed to download {pdf_file}")

    logger.info("PDF download test completed")

def main():
    try:
        if RUN_MODE == 'pdf_processing':
            logger.info("Starting PDF processing mode")
            start_sqs_listener()
        elif RUN_MODE == 'api':
            logger.info("Starting API server")
            start_api_server()
        elif RUN_MODE == 'all':
            logger.info("Starting both PDF processing and API server")
            pdf_thread = threading.Thread(target=start_sqs_listener)
            api_thread = threading.Thread(target=start_api_server)

            pdf_thread.start()
            api_thread.start()

            pdf_thread.join()
            api_thread.join()
        elif RUN_MODE == 'test_pdf_download':
            logger.info("Starting PDF download test")
            test_pdf_download()
        else:
            logger.error(f"Invalid RUN_MODE: {RUN_MODE}")
    except Exception as e:
        logger.exception(f"An error occurred in main: {e}")

if __name__ == "__main__":
    main()
