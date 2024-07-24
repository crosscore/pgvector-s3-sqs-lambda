# main.py
import json
import logging
from s3_downloader import process_sqs_message
from pdf_vectorizer import process_pdf_and_insert
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    try:
        # S3からPDFをダウンロード
        local_file_path = process_sqs_message()

        if not local_file_path:
            return {
                'statusCode': 200,
                'body': json.dumps('No PDF to process')
            }

        # PDFをベクトル化してデータベースに保存
        process_pdf_and_insert(local_file_path)

        # 処理が完了したらファイルを削除
        os.remove(local_file_path)
        logger.info(f"Deleted temporary file: {local_file_path}")

        return {
            'statusCode': 200,
            'body': json.dumps('PDF processed and vectorized successfully')
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

if __name__ == "__main__":
    # ローカルテスト用
    result = lambda_handler(None, None)
    print(result)
