# rag-pgvector/backend/vectorizer.py
import os
import requests
import pandas as pd
import numpy as np
from io import BytesIO
from pypdf import PdfReader
from openai import AzureOpenAI
import logging
from config import *
from langchain.text_splitter import CharacterTextSplitter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"Initializing vectorizer with S3_DB_URL: {S3_DB_URL}")

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION
)

def normalize_vector(vector):
    return vector / np.linalg.norm(vector)

def get_pdf_files_from_s3():
    try:
        response = requests.get(f"{S3_DB_URL}/data/pdf", timeout=10)
        response.raise_for_status()
        files = response.json()
        valid_files = [file for file in files if file.endswith('.pdf')]
        logger.info(f"Found {len(valid_files)} PDF files")
        return valid_files
    except requests.RequestException as e:
        logger.error(f"Error fetching PDF files: {str(e)}")
        return []

def fetch_pdf_content(file_name):
    try:
        response = requests.get(f"{S3_DB_URL}/data/pdf/{file_name}", stream=True, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Error fetching PDF file {file_name}: {str(e)}")
        return None

def extract_text_from_pdf(content):
    try:
        pdf = PdfReader(BytesIO(content))
        return [(str(i+1), page.extract_text()) for i, page in enumerate(pdf.pages)]
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return []

def create_embedding(text):
    response = client.embeddings.create(
        input=text,
        model=AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
    )
    return response.data[0].embedding

def split_text_into_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator=SEPARATOR,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def process_pdf(file_name):
    content = fetch_pdf_content(file_name)
    if content is None:
        return pd.DataFrame()

    texts = extract_text_from_pdf(content)
    if not texts:
        logger.warning(f"No text extracted from PDF file: {file_name}")
        return pd.DataFrame()

    processed_data = []
    for page, text in texts:
        chunks = split_text_into_chunks(text)
        for chunk_num, chunk in enumerate(chunks, start=1):
            vector = create_embedding(chunk)
            processed_data.append({
                'file_name': file_name,
                'page': page,
                'chunk_num': chunk_num,
                'text': chunk,
                'embedding': normalize_vector(vector).tolist()
            })

    logger.info(f"Processed {len(processed_data)} chunks from {file_name}")
    return pd.DataFrame(processed_data)

def process_pdf_files():
    all_processed_data = pd.concat([process_pdf(file_name)
                                    for file_name in get_pdf_files_from_s3()],
                                    ignore_index=True)

    if not all_processed_data.empty:
        os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(CSV_OUTPUT_DIR, "pdf_documents_vector_normalized.csv")
        all_processed_data.to_csv(output_file, index=False)
        logger.info(f"All processed data saved to {output_file}")
        return all_processed_data
    else:
        logger.warning("No data processed.")
        return None

if __name__ == "__main__":
    process_pdf_files()
