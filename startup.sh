#!/bin/bash
cd /home/site/wwwroot

# Gunicornの設定
gunicorn src.main:app \
    --bind=0.0.0.0:8000 \
    --timeout=180 \
    --workers=2 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --worker-connections=250 \
    --backlog=100 \
    --max-requests=250 \
    --max-requests-jitter=50 \
    --graceful-timeout=120 \
    --keep-alive=5 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output

