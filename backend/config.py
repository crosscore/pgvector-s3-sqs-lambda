# rag-pgvector/backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAIの利用可否
ENABLE_OPENAI = "true"
AZURE_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Azure OpenAI設定
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# PDF処理設定
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 15))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 0))
SEPARATOR = os.getenv("SEPARATOR", "\n\n")
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "./data/csv/pdf")

# S3設定
S3_DB_URL = os.getenv("S3_DB_URL")

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
IVFFLAT_LISTS = int(os.getenv("IVFFLAT_LISTS", "20"))
IVFFLAT_PROBES = int(os.getenv("IVFFLAT_PROBES", "5"))
VECTOR_DIMENSIONS = 3072

# その他の設定
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
