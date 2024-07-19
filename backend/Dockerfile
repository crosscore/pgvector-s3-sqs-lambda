# rag-pgvecotr/backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vectorizer.py .

CMD ["python", "vectorizer.py"]
