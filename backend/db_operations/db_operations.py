# rag-pgvector/backend/db_operations.py
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
import logging
from contextlib import contextmanager
from config import *

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=PGVECTOR_DB_NAME,
            user=PGVECTOR_DB_USER,
            password=PGVECTOR_DB_PASSWORD,
            host=PGVECTOR_DB_HOST,
            port=PGVECTOR_DB_PORT
        )
        logger.info(f"Connected to database: {PGVECTOR_DB_HOST}:{PGVECTOR_DB_PORT}")
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed")

def create_table_and_index(cursor):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS pdf_table (
        id SERIAL PRIMARY KEY,
        file_name TEXT,
        page TEXT,
        chunk_num TEXT,
        text TEXT,
        embedding vector(3072)
    );
    """
    cursor.execute(create_table_query)
    logger.info("Table created successfully")

    if INDEX_TYPE == "hnsw":
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS hnsw_embedding_idx ON pdf_table
        USING hnsw ((embedding::halfvec(3072)) halfvec_ip_ops)
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION});
        """
        cursor.execute(create_index_query)
        logger.info("HNSW index created successfully")
    elif INDEX_TYPE == "ivfflat":
        create_index_query = f"""
        CREATE INDEX IF NOT EXISTS ivfflat_embedding_idx ON pdf_table
        USING ivfflat ((embedding::halfvec(3072)) halfvec_ip_ops)
        WITH (lists = {IVFFLAT_LISTS});
        """
        cursor.execute(create_index_query)
        logger.info("IVFFlat index created successfully")
    elif INDEX_TYPE == "none":
        logger.info("No index created as per configuration")
    else:
        raise ValueError(f"Unsupported index type: {INDEX_TYPE}")

def save_to_database(data):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            create_table_and_index(cursor)

            insert_query = f"""
            INSERT INTO pdf_table (file_name, page, chunk_num, text, embedding)
            VALUES (%s, %s, %s, %s, %s::vector(3072));
            """

            batch_data = [
                (row['file_name'], row['page'], row['chunk_num'], row['text'], row['embedding'])
                for _, row in data.iterrows()
            ]

            try:
                execute_batch(cursor, insert_query, batch_data, page_size=BATCH_SIZE)
                conn.commit()
                logger.info(f"Inserted {len(batch_data)} rows into the database")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error inserting batch: {e}")
                raise

def query_similar_embeddings(query_embedding, limit=5):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            query = f"""
            SELECT file_name, page, chunk_num, text, embedding::vector(3072) <-> %s::vector(3072) as distance
            FROM pdf_table
            ORDER BY distance
            LIMIT %s;
            """
            cursor.execute(query, (query_embedding, limit))
            results = cursor.fetchall()
            return results
