#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1
export PORT=8000

# 依存関係の確認とインストール
python -m pip install --upgrade pip
pip install pymysql==1.1.0
pip install -r requirements.txt

# Gunicornの起動（タイムアウトを300秒に設定）
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