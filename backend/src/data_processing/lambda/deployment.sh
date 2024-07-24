#!/bin/bash

set -eo pipefail

FUNCTION_NAME="pdf_processor"
PACKAGE_DIR="lambda_package"
VENV_DIR="venv"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

cleanup() {
    log "Cleaning up..."
    rm -rf $PACKAGE_DIR
    rm -rf $VENV_DIR
    rm -f $FUNCTION_NAME.zip
}

trap 'log "Error occurred. Exiting..."; cleanup' ERR

cleanup

mkdir -p $PACKAGE_DIR

log "Creating virtual environment with Python 3.11..."
python3.11 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

log "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

log "Checking dependencies and versions..."
python -c "
import sys
import importlib

def get_version(module_name):
    try:
        module = importlib.import_module(module_name)
        return getattr(module, '__version__', 'Version not available')
    except ImportError:
        return f'Module {module_name} not found'

modules = ['openai', 'langchain_text_splitters', 'dotenv', 'boto3', 'pypdf', 'psycopg2', 'pydantic', 'pydantic_core']

print('Python version:', sys.version)
for module in modules:
    print(f'{module} version:', get_version(module))

print('All dependencies are present.')
"

log "Copying Lambda function code..."
cp lambda_function.py s3_downloader.py pdf_vectorizer.py config.py .env $PACKAGE_DIR/

log "Copying installed packages to Lambda package directory..."
cp -r $VENV_DIR/lib/python3.11/site-packages/* $PACKAGE_DIR/

log "Creating ZIP archive..."
(cd $PACKAGE_DIR && find . -type f -print0 | xargs -0 zip -r ../$FUNCTION_NAME.zip)

if [ ! -s "$FUNCTION_NAME.zip" ]; then
    log "Error: $FUNCTION_NAME.zip is empty or not created."
    exit 1
fi

log "Updating Lambda function..."
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://$FUNCTION_NAME.zip

aws lambda update-function-configuration --function-name $FUNCTION_NAME --runtime python3.11

cleanup

log "Lambda function deployment complete."

deactivate
