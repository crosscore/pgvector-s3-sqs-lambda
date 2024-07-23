# rag-pgvector/backend/src/data_processing/reading_pgvector.py
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect, text
import ast
import logging
import struct

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float

class VECTOR(ARRAY):
    def __init__(self, dimensions):
        super(VECTOR, self).__init__(Float, dimensions=dimensions)

# SQLAlchemyに新しい型を登録
from sqlalchemy.dialects import postgresql
postgresql.base.ischema_names['vector'] = VECTOR

def get_db_url():
    return f"postgresql://{os.getenv('PGVECTOR_DB_USER')}:{os.getenv('PGVECTOR_DB_PASSWORD')}@" \
            f"{os.getenv('PGVECTOR_DB_HOST')}:{os.getenv('PGVECTOR_DB_PORT')}/{os.getenv('PGVECTOR_DB_NAME')}"

def get_primary_key_info(engine):
    with engine.connect() as connection:
        query = text("""
        SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
        FROM   pg_index i
        JOIN   pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE  i.indrelid = 'document_vectors'::regclass
        AND    i.indisprimary;
        """)
        result = connection.execute(query)
        return result.fetchall()

def get_table_structure(engine):
    inspector = inspect(engine)
    columns = inspector.get_columns('document_vectors')
    return columns

def get_index_info(engine):
    with engine.connect() as connection:
        query = text("""
        SELECT
            i.relname AS index_name,
            a.attname AS column_name,
            ix.indisprimary AS is_primary,
            ix.indisunique AS is_unique,
            am.amname AS index_type,
            pg_get_indexdef(i.oid) AS index_definition
        FROM
            pg_index ix
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_am am ON i.relam = am.oid
            LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE
            t.relname = 'document_vectors'
        ORDER BY
            i.relname, a.attnum;
        """)
        result = connection.execute(query)
        return result.fetchall()

def get_hnsw_index_settings(engine):
    with engine.connect() as connection:
        query = text("""
        SELECT reloptions
        FROM pg_class
        WHERE relname = 'hnsw_document_vectors_chunk_vector_idx';
        """)
        result = connection.execute(query)
        return result.fetchone()

def read_vector_data():
    try:
        engine = create_engine(get_db_url())
        query = "SELECT * FROM document_vectors"
        df = pd.read_sql(query, engine)
        df['chunk_vector'] = df['chunk_vector'].apply(ast.literal_eval)
        logger.info(f"データベースから {len(df)} 行のデータを正常に読み込みました。")
        return engine, df
    except Exception as e:
        logger.error(f"データの読み込み中にエラーが発生しました: {e}")
        raise

def log_table_info(df):
    logger.info("\n------ テーブル情報 ------")
    logger.info(f"行数: {len(df)}")
    logger.info(f"列数: {len(df.columns)}")
    logger.info("列の情報:")
    for col in df.columns:
        logger.info(f"  - {col}: {df[col].dtype}")

def log_sample_data(df):
    logger.info("\n------ サンプルデータ (最初の1行) ------")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    logger.info(f"\n{df.head(1).to_string()}")

def verify_vector(engine):
    with engine.connect() as connection:
        query = text("""
        SELECT chunk_vector::text
        FROM document_vectors
        LIMIT 1;
        """)
        result = connection.execute(query)
        db_vector = result.fetchone()[0]

    logger.info("\n------ データベース内のベクトル形式 ------")
    logger.info(f"データベースから取得したベクトル（最初の10要素）: {db_vector[:100]}...")

def compare_float_representations(df):
    logger.info("\n------ 浮動小数点数の表現比較 ------")
    vector = df['chunk_vector'][0]

    # float32 (単精度浮動小数点数)
    vector_f32 = np.array(vector, dtype=np.float32)

    # float16 (半精度浮動小数点数)
    vector_f16 = np.array(vector, dtype=np.float16)

    logger.info(f"元のベクトル:      {vector[:5]}")
    logger.info(f"float32として解釈: {vector_f32[:5]}")
    logger.info(f"float16として解釈: {vector_f16[:5]}")

def check_binary_representation(df):
    logger.info("\n------ バイナリ表現の確認 ------")
    vector = df['chunk_vector'][0]

    # float32のバイナリ表現
    f32_binary = struct.pack('f', vector[0])
    f32_hex = f32_binary.hex()

    # float16のバイナリ表現
    f16_val = np.float16(vector[0])
    f16_binary = struct.pack('e', f16_val)
    f16_hex = f16_binary.hex()

    logger.info(f"最初の要素の値: {vector[0]}")
    logger.info(f"float32のバイナリ表現（16進数）: {f32_hex}")
    logger.info(f"float16のバイナリ表現（16進数）: {f16_hex}")

def main():
    try:
        logger.info("データベースからの読み取りを開始します。")
        engine, df = read_vector_data()

        table_structure = get_table_structure(engine)
        logger.info("------ テーブル構造 ------")
        for column in table_structure:
            logger.info(f"  - {column['name']}: {column['type']}")

        primary_key_info = get_primary_key_info(engine)
        logger.info("\n------ プライマリキー情報 ------")
        for column in primary_key_info:
            logger.info(f"カラム名: {column.attname}, データ型: {column.data_type}")

        logger.info("\n------ インデックス情報 ------")
        index_info = get_index_info(engine)
        for index in index_info:
            logger.info(f"インデックス名: {index.index_name}")
            logger.info(f"  カラム: {index.column_name}")
            logger.info(f"  タイプ: {index.index_type}")
            logger.info(f"  定義: {index.index_definition}")
            logger.info("  ---")

        hnsw_settings = get_hnsw_index_settings(engine)
        if hnsw_settings:
            logger.info("\n------ HNSWインデックス設定 ------")
            logger.info(f"設定: {hnsw_settings[0]}")

        log_table_info(df)
        log_sample_data(df)

        logger.info("\n------ embedding の長さ ------")
        for i in range(min(10, len(df))):
            logger.info(f"len(df['chunk_vector'][{i}]): {len(df['chunk_vector'][i])}")

        verify_vector(engine)
        compare_float_representations(df)
        check_binary_representation(df)

        logger.info("データベースの読み取りが完了しました。")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
