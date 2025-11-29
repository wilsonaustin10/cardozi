#!/bin/bash

# Detect mode based on Railway Service Variable
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "✅ Starting Celery Worker for Browser Use agent workflows..."
    # Use --uid to avoid root user warnings and enable browser automation
    celery -A src.worker.celery_app worker --loglevel=info --uid=nobody
else
    echo "✅ Starting FastAPI Server..."
    # Railway injects $PORT automatically
    uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi