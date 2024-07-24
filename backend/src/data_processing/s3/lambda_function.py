import json
import boto3
import psycopg2
from psycopg2.extras import execute_values
from botocore.exceptions import ClientError
from pypdf import PdfReader
from openai import OpenAI, AzureOpenAI
import tempfile
import os
from langchain_text_splitters import CharacterTextSplitter
from config import *

s3_client = boto3.client('s3',
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_REGION)
sqs_client = boto3.client('sqs',
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_REGION)

if ENABLE_OPENAI:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )

def get_db_connection():
    return psycopg2.connect(
        dbname=PGVECTOR_DB_NAME,
        user=PGVECTOR_DB_USER,
        password=PGVECTOR_DB_PASSWORD,
        host=PGVECTOR_DB_HOST,
        port=PGVECTOR_DB_PORT
    )

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf = PdfReader(file)
        return [page.extract_text() for page in pdf.pages]

def split_text_into_chunks(text):
    text_splitter = CharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separator=SEPARATOR
    )
    return text_splitter.split_text(text)

def create_embedding(text):
    if ENABLE_OPENAI:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
    else:
        response = openai_client.embeddings.create(
            input=text,
            model=AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
        )
    return response.data[0].embedding

def process_pdf_and_vectorize(file_path, file_name):
    pages = extract_text_from_pdf(file_path)
    vectors = []
    for page_num, page_text in enumerate(pages):
        chunks = split_text_into_chunks(page_text)
        for chunk_no, chunk in enumerate(chunks):
            if chunk.strip():
                vector = create_embedding(chunk)
                vectors.append((file_name, page_num, chunk_no, chunk, vector))
    return vectors

def insert_vectors_to_db(vectors):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_vectors (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT,
                    page_num INTEGER,
                    chunk_no INTEGER,
                    chunk_text TEXT,
                    vector vector(3072)
                )
            """)
            execute_values(cur, """
                INSERT INTO document_vectors (file_name, page_num, chunk_no, chunk_text, vector)
                VALUES %s
            """, vectors)
        conn.commit()

def lambda_handler(event, context):
    try:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0
        )

        if 'Messages' not in response:
            return {'statusCode': 200, 'body': json.dumps('No messages to process')}

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']

        body = json.loads(message['Body'])
        s3_key = body['Records'][0]['s3']['object']['key']

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            s3_client.download_fileobj(S3_BUCKET_NAME, s3_key, temp_file)
            temp_file_path = temp_file.name

        vectors = process_pdf_and_vectorize(temp_file_path, s3_key)
        insert_vectors_to_db(vectors)

        os.unlink(temp_file_path)

        sqs_client.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )

        return {'statusCode': 200, 'body': json.dumps('PDF processed and vectorized successfully')}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(str(e))}
