import os
import json
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter

input_folder = "../../data/pdf"
output_csv_folder = "../../data/output_01/csv"
output_json_folder = "../../data/output_01/json"
output_txt_folder = "../../data/output_01/txt"

def extract_text_from_pdf(file_path):
    loader = PyPDFLoader(file_path)
    return loader.load()

def process_pdf_to_dataframe(file_name, pages):
    text_splitter = CharacterTextSplitter(
        chunk_size=0,
        chunk_overlap=0,
        separator="\n"
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
                'text': chunk
            })
            total_chunks += 1

    return pd.DataFrame(data), total_chunks

def save_as_json(file_name, pages):
    json_data = []
    for page in pages:
        unified_source = page.metadata['source'].replace('\\', '/')
        json_data.append({
            "page_content": page.page_content,
            "metadata": {
                **page.metadata,
                "source": unified_source
            }
        })

    output_file = os.path.join(output_json_folder, f"{os.path.splitext(file_name)[0]}.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def save_as_txt(file_name, pages):
    combined_text = "\n\n".join(page.page_content for page in pages)
    output_file = os.path.join(output_txt_folder, f"{os.path.splitext(file_name)[0]}.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_text)

def process_file(file_name):
    file_path = os.path.join(input_folder, file_name)
    pages = extract_text_from_pdf(file_path)

    if not pages:
        print(f"Warning: No text extracted from {file_name}")
        return

    print(f"Processing {file_name}: {len(pages)} pages")

    df, total_chunks = process_pdf_to_dataframe(file_name, pages)
    if df.empty:
        print(f"Warning: No chunks created for {file_name}")
        return

    print(f"Processed {file_name}: {len(pages)} pages, {total_chunks} chunks")

    base_name = os.path.splitext(file_name)[0]
    output_csv_file = os.path.join(output_csv_folder, f"{base_name}.csv")
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)
    df.to_csv(output_csv_file, index=False, quoting=1)

    save_as_json(file_name, pages)
    save_as_txt(file_name, pages)
    print(f"Created CSV, JSON, and TXT files for {file_name}")

def main():
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith('.pdf'):
            process_file(file_name)

if __name__ == "__main__":
    main()
