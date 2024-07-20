# rag-pgvector/backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
ENABLE_OPENAI = os.getenv("ENABLE_OPENAI", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# AWS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
LOCAL_PDF_FOLDER = os.getenv("LOCAL_PDF_FOLDER")

# PDF処理設定
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 10))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 0))
SEPARATOR = os.getenv("SEPARATOR", "\n\n")
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "./data/csv/")

# S3設定
S3_DB_URL = os.getenv("S3_DB_URL", "http://s3_db:9000")

# データベース設定
PGVECTOR_DB_NAME = os.getenv("PGVECTOR_DB_NAME")
PGVECTOR_DB_USER = os.getenv("PGVECTOR_DB_USER")
PGVECTOR_DB_PASSWORD = os.getenv("PGVECTOR_DB_PASSWORD")
PGVECTOR_DB_HOST = os.getenv("PGVECTOR_DB_HOST", "pgvector_db")
PGVECTOR_DB_PORT = int(os.getenv("PGVECTOR_DB_PORT", 5432))

# インデックス設定
INDEX_TYPE = os.getenv("INDEX_TYPE", "hnsw").lower()
HNSW_M = int(os.getenv("HNSW_M", "16"))
HNSW_EF_CONSTRUCTION = int(os.getenv("HNSW_EF_CONSTRUCTION", "256"))
HNSW_EF_SEARCH = int(os.getenv("HNSW_EF_SEARCH", "200"))
IVFFLAT_LISTS = int(os.getenv("IVFFLAT_LISTS", "20"))
IVFFLAT_PROBES = int(os.getenv("IVFFLAT_PROBES", "5"))
VECTOR_DIMENSIONS = 3072

# その他の設定
RUN_MODE = os.getenv("RUN_MODE", "test_pdf_download")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
