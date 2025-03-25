#!/bin/bash

# アプリケーションのルートディレクトリに移動
cd "$HOME/site/wwwroot"

# 環境変数の設定
export PYTHONPATH="$HOME/site/wwwroot"
export PORT="${PORT:-8000}"

# Gunicornの起動
gunicorn main:app \
    --bind=0.0.0.0:$PORT \
    --worker-class=uvicorn.workers.UvicornWorker \
    --timeout=60 \
    --workers=2 \
    --worker-connections=100 \
    --backlog=50 \
    --max-requests=100 \
    --max-requests-jitter=20 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output

