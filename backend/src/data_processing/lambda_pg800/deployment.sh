#!/bin/bash

set -eo pipefail  # エラーが発生した時点でスクリプトを終了し、パイプのエラーも検出

# Lambda関数名
FUNCTION_NAME="pdf_processor"

# 作業ディレクトリ
PACKAGE_DIR="lambda_package"

# ログ関数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# クリーンアップ関数
cleanup() {
    log "Cleaning up..."
    rm -rf $PACKAGE_DIR
    rm -f $FUNCTION_NAME.zip
}

# エラーハンドリング
trap 'log "Error occurred. Exiting..."; cleanup' ERR

# 既存のパッケージディレクトリとZIPファイルを削除
cleanup

# 必要なディレクトリを作成
mkdir -p $PACKAGE_DIR

log "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt -t $PACKAGE_DIR --no-cache-dir

# 依存関係のチェックとバージョン情報の出力
log "Checking dependencies and versions..."
python -c "
import sys
sys.path.insert(0, '$PACKAGE_DIR')
import openai
import langchain_text_splitters
import dotenv
import boto3
import pypdf
import psycopg2
import pydantic
import pydantic_core

print('Python version:', sys.version)
print('openai version:', openai.__version__)
print('langchain_text_splitters version:', langchain_text_splitters.__version__)
print('python-dotenv version:', dotenv.__version__)
print('boto3 version:', boto3.__version__)
print('pypdf version:', pypdf.__version__)
print('psycopg2 version:', psycopg2.__version__)
print('pydantic version:', pydantic.__version__)
print('pydantic_core version:', pydantic_core.__version__)
print('All dependencies are present.')
"

log "Copying Lambda function code..."
cp lambda_function.py s3_downloader.py pdf_vectorizer.py config.py .env $PACKAGE_DIR/

log "Creating ZIP archive..."
(cd $PACKAGE_DIR && zip -r ../$FUNCTION_NAME.zip .)

if [ ! -s "$FUNCTION_NAME.zip" ]; then
    log "Error: $FUNCTION_NAME.zip is empty or not created."
    exit 1
fi

log "Updating Lambda function..."
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://$FUNCTION_NAME.zip

cleanup

log "Lambda function deployment complete."
