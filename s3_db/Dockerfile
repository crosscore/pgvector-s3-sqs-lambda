# rag-pgvector/s3_db/Dockerfile

FROM minio/minio:latest

RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc && \
    echo "alias ll='ls -alF'" >> ~/.bashrc && \
    echo "export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> ~/.bashrc

# MinIOサーバーを起動するコマンドを設定
CMD ["server", "/data", "--console-address", ":9001"]

# ヘルスチェック用の設定
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1
