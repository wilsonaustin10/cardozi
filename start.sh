#!/bin/bash

# Detect mode based on Railway Service Variable
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "🚧 Celery Worker disabled for Railway deployment"
    echo "   Using simulation mode instead. For production, set up dedicated worker service."
    # Keep the process alive but don't start celery
    tail -f /dev/null
else
    echo "✅ Starting FastAPI Server..."
    # Railway injects $PORT automatically
    uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi