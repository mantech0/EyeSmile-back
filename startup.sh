#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot
gunicorn src.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile - --log-level info 