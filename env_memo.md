# OpenAI
ENABLE_OPENAI=true
OPENAI_API_KEY=key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=your_azure_openai_embeddings_deployment
AZURE_OPENAI_API_VERSION=your_azure_openai_api_version

# AWS credentials and region
AWS_ACCESS_KEY_ID=key
AWS_SECRET_ACCESS_KEY=key
AWS_REGION=ap-northeast-1

# S3 and SQS settings
S3_BUCKET_NAME=my-bucket
SQS_QUEUE_URL="https://sqs.ap-northeast-1.amazonaws.com/000000000/my-queue.fifo"
LOCAL_UPLOAD_PATH="path"
LOCAL_DOWNLOAD_PATH="path"

# PDF処理設定
CHUNK_SIZE=0
CHUNK_OVERLAP=0
SEPARATOR="\n"
PDF_INPUT_DIR="/app/data/pdf"
CSV_OUTPUT_DIR="/app/data/csv"

# pgvector_db
PGVECTOR_DB_NAME=pgvector_db
PGVECTOR_DB_USER=user
PGVECTOR_DB_PASSWORD=pass
PGVECTOR_DB_HOST=pgvector_db
PGVECTOR_DB_PORT=5432

# インデックス設定
INDEX_TYPE=hnsw
HNSW_M=16
HNSW_EF_CONSTRUCTION=256
HNSW_EF_SEARCH=200
IVFFLAT_LISTS=100
IVFFLAT_PROBES=5

# その他の設定
RUN_MODE=test_pdf_download
BATCH_SIZE=1000
