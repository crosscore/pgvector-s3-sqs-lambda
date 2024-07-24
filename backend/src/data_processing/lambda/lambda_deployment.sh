#!/bin/bash

# Lambda関数名
FUNCTION_NAME="pdf_processor"

# 作業ディレクトリ
PACKAGE_DIR="lambda_package"

# 必要なディレクトリを作成
mkdir -p $PACKAGE_DIR

# 必要なライブラリをインストール
pip install -r requirements.txt -t $PACKAGE_DIR

# Lambda関数のコードをコピー
cp main.py s3_downloader.py pdf_vectorizer.py config.py .env $PACKAGE_DIR/

# Zipアーカイブを作成
cd $PACKAGE_DIR
zip -r ../$FUNCTION_NAME.zip .
cd ..

# AWS CLIを使用してLambda関数を更新
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://$FUNCTION_NAME.zip

# クリーンアップ
rm -rf $PACKAGE_DIR
rm $FUNCTION_NAME.zip

echo "Lambda function deployment complete."
