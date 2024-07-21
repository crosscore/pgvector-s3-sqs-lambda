import os
import pandas as pd
from pypdf import PdfReader
from openai import AzureOpenAI, OpenAI
import logging
from config import *
from langchain.text_splitter import CharacterTextSplitter
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
logger.info("Initializing vectorizer to read from local PDF folder")

if ENABLE_OPENAI:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("Using OpenAI API for embeddings")
else:
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    logger.info("Using Azure OpenAI API for embeddings")

def get_pdf_files_from_local():
    pdf_files = [f for f in os.listdir(PDF_INPUT_DIR) if f.endswith('.pdf')]
    logger.info(f"Found {len(pdf_files)} PDF files in {PDF_INPUT_DIR}")
    return pdf_files

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            return [(str(i+1), page.extract_text()) for i, page in enumerate(pdf.pages)]
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return []

def create_embedding(text):
    if ENABLE_OPENAI:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
    else:
        response = client.embeddings.create(
            input=text,
            model=AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
        )
    return response

def split_text_into_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator=SEPARATOR,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def process_pdf(file_name):
    file_path = os.path.join(PDF_INPUT_DIR, file_name)
    texts = extract_text_from_pdf(file_path)
    if not texts:
        logger.warning(f"No text extracted from PDF file: {file_name}")
        return None

    processed_data = []
    for page, text in texts:
        chunks = split_text_into_chunks(text)
        for chunk_num, chunk in enumerate(chunks, start=1):
            response = create_embedding(chunk)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            processed_data.append({
                'file_name': file_name,
                'page': page,
                'chunk_num': chunk_num,
                'text': chunk,
                'model': response.model,
                'prompt_tokens': response.usage.prompt_tokens,
                'total_tokens': response.usage.total_tokens,
                'timestamp': current_time,
                'embedding': response.data[0].embedding
            })

    logger.info(f"Processed {len(processed_data)} chunks from {file_name}")
    return pd.DataFrame(processed_data)

def process_pdf_files():
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

    for file_name in get_pdf_files_from_local():
        processed_data = process_pdf(file_name)
        if processed_data is not None and not processed_data.empty:
            csv_file_name = f'{os.path.splitext(file_name)[0]}.csv'
            output_file = os.path.join(CSV_OUTPUT_DIR, csv_file_name)
            processed_data.to_csv(output_file, index=False)
            logger.info(f"Processed data for {file_name} saved to {output_file}")
        else:
            logger.warning(f"No data processed for {file_name}")

if __name__ == "__main__":
    process_pdf_files()
