#!/bin/bash

# 環境変数に基づいて異なる動作を選択
if [ "$RUN_MODE" = "vectorizer" ]; then
    exec python vectorizer.py
elif [ "$RUN_MODE" = "sqs_listener" ]; then
    exec python sqs_listener.py
else
    # デフォルトの動作：何もせずに待機
    exec "$@"
fi
