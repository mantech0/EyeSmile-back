#!/bin/bash
cd /home/site/wwwroot

# Gunicornの設定
gunicorn src.main:app \
    --bind=0.0.0.0:8000 \
    --timeout=60 \
    --workers=2 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --worker-connections=100 \
    --backlog=50 \
    --max-requests=100 \
    --max-requests-jitter=20 \
    --graceful-timeout=30 \
    --keep-alive=2 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output

