#!/bin/bash
set -e

# 作業ディレクトリの設定
cd /home/site/wwwroot

# 環境変数の設定
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1
export PORT=8000
export WEB_CONCURRENCY=2

echo "Starting application setup..."

# 依存関係のインストール
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# データベースのマイグレーション
echo "Running database migrations..."
python -m alembic upgrade head || true

# Gunicornの起動（メモリ最適化設定）
echo "Starting Gunicorn..."
exec gunicorn src.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --worker-tmp-dir /dev/shm \
    --max-requests 250 \
    --max-requests-jitter 25 \
    --graceful-timeout 60 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --worker-connections 250 \
    --backlog 100 \
    --limit-request-line 4094 \
    --limit-request-fields 100 \
    --limit-request-field_size 8190 