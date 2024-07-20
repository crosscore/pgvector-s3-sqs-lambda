import os
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from config import *
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    loader = PyPDFLoader(file_path)
    return loader.load()

def process_pdf_to_dataframe(file_name, pages):
    text_splitter = CharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separator=SEPARATOR
    )

    data = []
    total_chunks = 0
    for page_num, page in enumerate(pages):
        page_text = page.page_content
        chunks = text_splitter.split_text(page_text) if page_text else []

        if not chunks and page_text:
            chunks = [page_text]

        for chunk in chunks:
            data.append({
                'file_name': file_name,
                'file_type': 'pdf',
                'page': str(page_num),
                'chunk_number': total_chunks,
                'content': chunk
            })
            total_chunks += 1

    return pd.DataFrame(data), total_chunks

def extract_and_process_pdf(file_path):
    file_name = os.path.basename(file_path)
    pages = extract_text_from_pdf(file_path)

    if not pages:
        logger.warning(f"No text extracted from {file_name}")
        return None

    logger.info(f"Processing {file_name}: {len(pages)} pages")

    df, total_chunks = process_pdf_to_dataframe(file_name, pages)
    if df.empty:
        logger.warning(f"No chunks created for {file_name}")
        return None

    logger.info(f"Processed {file_name}: {len(pages)} pages, {total_chunks} chunks")
    return df
