#!/bin/bash
set -e

# 作業ディレクトリの設定
cd /home/site/wwwroot

# 環境変数の設定
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1
export PORT=8000

echo "Starting application setup..."

# 依存関係のインストール
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# データベースのマイグレーション
echo "Running database migrations..."
python -m alembic upgrade head || true

# Gunicornの起動
echo "Starting Gunicorn..."
exec gunicorn src.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --keep-alive 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output 