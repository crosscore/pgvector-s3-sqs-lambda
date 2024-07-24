import os
from pypdf import PdfReader
from openai import AzureOpenAI, OpenAI
import logging
import pg8000
from config import *
from langchain_text_splitters import CharacterTextSplitter
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

if ENABLE_OPENAI:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("Using OpenAI API for embeddings")
else:
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    logger.info("Using Azure OpenAI API for embeddings")

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pg8000.connect(
            database=PGVECTOR_DB_NAME,
            user=PGVECTOR_DB_USER,
            password=PGVECTOR_DB_PASSWORD,
            host=PGVECTOR_DB_HOST,
            port=PGVECTOR_DB_PORT
        )
        logger.info(f"Connected to database: {PGVECTOR_DB_HOST}:{PGVECTOR_DB_PORT}")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed")

def create_table_and_index(cursor):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS document_vectors (
        chunk_id SERIAL PRIMARY KEY,
        file_name TEXT,
        document_page SMALLINT,
        chunk_no INTEGER,
        text TEXT,
        model TEXT,
        prompt_tokens INTEGER,
        total_tokens INTEGER,
        created_date_time TIMESTAMPTZ,
        chunk_vector vector(3072)
    );
    """
    cursor.execute(create_table_query)
    logger.info("Table created successfully")

    if INDEX_TYPE == "hnsw":
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS hnsw_document_vectors_chunk_vector_idx ON document_vectors
        USING hnsw ((chunk_vector::halfvec(3072)) halfvec_ip_ops)
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION});
        """
        cursor.execute(create_index_query)
        logger.info("HNSW index created successfully")
    elif INDEX_TYPE == "ivfflat":
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS ivfflat_document_vectors_chunk_vector_idx ON document_vectors
        USING ivfflat ((chunk_vector::halfvec(3072)) halfvec_ip_ops)
        WITH (lists = {IVFFLAT_LISTS});
        """
        cursor.execute(create_index_query)
        logger.info("IVFFlat index created successfully")
    elif INDEX_TYPE == "none":
        logger.info("No index created as per configuration")
    else:
        raise ValueError(f"Unsupported index type: {INDEX_TYPE}")

# 他の関数は変更なし

def process_pdf_and_insert(file_path):
    file_name = os.path.basename(file_path)
    pages = extract_text_from_pdf(file_path)
    if not pages:
        logger.warning(f"No text extracted from PDF file: {file_name}")
        return

    total_chunks = 0
    data = []
    insert_query = """
    INSERT INTO document_vectors
    (file_name, document_page, chunk_no, text, model, prompt_tokens, total_tokens, created_date_time, chunk_vector)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        create_table_and_index(cursor)

        for page in pages:
            page_text = page["page_content"]
            page_num = page["metadata"]["page"]
            chunks = split_text_into_chunks(page_text)

            if not chunks and page_text:
                chunks = [page_text]

            for chunk in chunks:
                if chunk.strip():  # Only process non-empty chunks
                    response = create_embedding(chunk)
                    jst = ZoneInfo("Asia/Tokyo")
                    current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S %Z')
                    data.append((
                        file_name,                    # file_name
                        page_num,                     # document_page
                        total_chunks,                 # chunk_no
                        chunk,                        # text
                        response.model,               # model
                        response.usage.prompt_tokens, # prompt_tokens
                        response.usage.total_tokens,  # total_tokens
                        current_time,                 # created_date_time
                        response.data[0].embedding    # chunk_vector
                    ))
                    total_chunks += 1

                    if len(data) >= BATCH_SIZE:
                        cursor.executemany(insert_query, data)
                        conn.commit()
                        logger.info(f"Inserted batch of {len(data)} rows into the database")
                        data = []

        if data:
            cursor.executemany(insert_query, data)
            conn.commit()
            logger.info(f"Inserted final batch of {len(data)} rows into the database")

    logger.info(f"Processed {file_name}: {len(pages)} pages, {total_chunks} chunks")
# メイン実行部分は変更なし
if __name__ == "__main__":
    # This is for testing purposes. In the Lambda function, this will be called from main.py
    test_pdf_path = "/tmp/test.pdf"
    if os.path.exists(test_pdf_path):
        process_pdf_and_insert(test_pdf_path)
    else:
        logger.error(f"Test PDF not found at {test_pdf_path}")
