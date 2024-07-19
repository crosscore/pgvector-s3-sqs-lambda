# rag-pgvector/backend/main.py
import logging
from vectorizer import process_pdf_files
from db_operations import save_to_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # PDFファイルの処理とベクトル化
        processed_data = process_pdf_files()

        if processed_data is not None and not processed_data.empty:
            # データベースへの保存
            save_to_database(processed_data)
            logger.info("All operations completed successfully.")
        else:
            logger.warning("No data processed.")

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()
