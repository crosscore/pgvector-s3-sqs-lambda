import logging
from config import TEST_PDF_FILES, S3_BUCKET_NAME, LOCAL_PDF_FOLDER, S3_DB_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from .s3_operations import S3Operations, fetch_pdf_from_s3

logger = logging.getLogger(__name__)

def test_pdf_download():
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
