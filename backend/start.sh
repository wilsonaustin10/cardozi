#!/bin/bash

# Detect mode based on Railway Service Variable
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "✅ Starting Celery Worker..."
    # Limit concurrency to 2 workers to stay within Railway memory limits
    # Use solo pool for simpler execution (no prefork overhead)
    celery -A src.worker.celery_app worker --loglevel=info --concurrency=2 --pool=solo
else
    echo "✅ Starting FastAPI Server..."
    # Railway injects $PORT automatically
    uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi