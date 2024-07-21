import os
import pandas as pd
from pypdf import PdfReader
from openai import AzureOpenAI, OpenAI
import logging
from config import *
from langchain.text_splitter import CharacterTextSplitter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

if ENABLE_OPENAI:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("Using OpenAI API for embeddings")

text = "hello"

def create_embedding(text):
    if ENABLE_OPENAI:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
    print(response)

create_embedding(text)
