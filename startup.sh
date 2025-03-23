#!/bin/bash

# 作業ディレクトリの設定
cd /home/site/wwwroot

# 環境変数の設定
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1
export PORT=8000

# 依存関係のインストール
python -m pip install --upgrade pip
pip install -r requirements.txt

# データベースのマイグレーション
python -m alembic upgrade head

# Gunicornの起動
gunicorn src.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000 \
    --timeout 300 \
    --keep-alive 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output 