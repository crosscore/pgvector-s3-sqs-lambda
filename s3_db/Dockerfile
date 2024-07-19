# rag-pgvector/s3_db/Dockerfile

FROM minio/minio:latest

# MinIOサーバーを起動するコマンドを設定
CMD ["server", "/data", "--console-address", ":9001"]

# ヘルスチェック用の設定
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1
