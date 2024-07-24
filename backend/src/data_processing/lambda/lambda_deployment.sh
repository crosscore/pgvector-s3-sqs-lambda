#!/bin/bash

set -e  # エラーが発生した時点でスクリプトを終了

# Lambda関数名
FUNCTION_NAME="pdf_processor"

# 作業ディレクトリ
PACKAGE_DIR="lambda_package"

# 既存のZIPファイルを削除
rm -f $FUNCTION_NAME.zip

# 必要なディレクトリを作成
mkdir -p $PACKAGE_DIR

# 仮想環境を作成してアクティベート
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt -t $PACKAGE_DIR

# デバッグ情報の出力
echo "Installed packages:"
pip list

echo "Content of $PACKAGE_DIR:"
ls -R $PACKAGE_DIR

# Lambda関数のコードをコピー
echo "Copying Lambda function code..."
cp lambda_function.py s3_downloader.py pdf_vectorizer.py config.py .env $PACKAGE_DIR/

# Zipアーカイブを作成
echo "Creating ZIP archive..."
cd $PACKAGE_DIR
zip -r -q ../$FUNCTION_NAME.zip .
cd ..

# ZIPファイルが正しく作成されたか確認
echo "Checking ZIP file..."
if [ ! -s "$FUNCTION_NAME.zip" ]; then
    echo "Error: $FUNCTION_NAME.zip is empty or not created."
    exit 1
fi

# ZIPファイルの内容を確認
echo "ZIP file contents:"
unzip -l $FUNCTION_NAME.zip

# AWS CLIを使用してLambda関数を更新
echo "Updating Lambda function..."
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://$FUNCTION_NAME.zip

# 更新の確認（東京時間で表示）
echo "Checking last modified time of the Lambda function (JST):"
LAST_MODIFIED=$(aws lambda get-function --function-name $FUNCTION_NAME --query 'Configuration.LastModified' --output text)

echo "Raw LAST_MODIFIED: $LAST_MODIFIED"

# macOS/BSD 標準の date コマンドを使用して UTC から JST に変換
UTC_DATE=$(echo $LAST_MODIFIED | sed 's/\([0-9]\{4\}\)-\([0-9]\{2\}\)-\([0-9]\{2\}\)T\([0-9]\{2\}\):\([0-9]\{2\}\):\([0-9]\{2\}\).*/\1\2\3\4\5.\6/')

echo "Processed UTC_DATE: $UTC_DATE"

# UTC時間をエポック秒に変換
EPOCH_SECONDS=$(date -j -f "%Y%m%d%H%M.%S" "${UTC_DATE}" "+%s")

# エポック秒に9時間（32400秒）を加算してJSTに変換
JST_EPOCH=$((EPOCH_SECONDS + 32400))

# JSTのエポック秒を読みやすい形式に変換
JST_TIME=$(date -r $JST_EPOCH "+%Y-%m-%d %H:%M:%S JST")

echo "Last modified: $JST_TIME"


# クリーンアップ
echo "Cleaning up..."
rm -rf $PACKAGE_DIR
rm $FUNCTION_NAME.zip

echo "Lambda function deployment complete."
