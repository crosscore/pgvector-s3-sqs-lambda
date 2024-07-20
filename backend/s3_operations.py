import os
import requests
import logging
from config import S3_DB_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

PDF_STORAGE_DIR = os.path.join('backend', 'data', 'pdf')

def ensure_pdf_storage_dir():
    """PDFストレージディレクトリが存在することを確認し、なければ作成する"""
    os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

def get_pdf_files_from_s3():
    """S3からPDFファイルのリストを取得する"""
    try:
        response = requests.get(f"{S3_DB_URL}/data/pdf", timeout=10)
        response.raise_for_status()
        files = response.json()
        valid_files = [file for file in files if file.endswith('.pdf')]
        logger.info(f"Found {len(valid_files)} PDF files in S3")
        return valid_files
    except requests.RequestException as e:
        logger.error(f"Error fetching PDF files list from S3: {str(e)}")
        return []

def fetch_and_save_pdf(file_name):
    """指定されたPDFファイルをS3から取得し、ローカルに保存する"""
    try:
        response = requests.get(f"{S3_DB_URL}/data/pdf/{file_name}", stream=True, timeout=10)
        response.raise_for_status()
        file_path = os.path.join(PDF_STORAGE_DIR, file_name)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Successfully downloaded and saved {file_name}")
        return file_path
    except requests.RequestException as e:
        logger.error(f"Error fetching PDF file {file_name} from S3: {str(e)}")
        return None

def fetch_all_pdfs_from_s3():
    """S3から全てのPDFファイルを取得し、ローカルに保存する"""
    ensure_pdf_storage_dir()
    pdf_files = get_pdf_files_from_s3()
    saved_files = []
    for file_name in pdf_files:
        file_path = fetch_and_save_pdf(file_name)
        if file_path:
            saved_files.append(file_path)
    logger.info(f"Total PDFs saved: {len(saved_files)}")
    return saved_files

if __name__ == "__main__":
    # テスト用のコード
    fetched_files = fetch_all_pdfs_from_s3()
    print(f"Fetched and saved {len(fetched_files)} PDF files")
