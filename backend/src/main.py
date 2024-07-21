# rag-pgvector/backend/main.py

import logging
import threading
from pdf_processing import start_sqs_listener, test_pdf_download
from api.routes import start_api_server
from config import RUN_MODE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

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
