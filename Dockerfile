FROM python:3.11-slim

# Optimization flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for Celery
RUN groupadd -r celery && useradd -r -g celery celery

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Permissions for startup script and ownership
RUN chmod +x start.sh && chown -R celery:celery /app

# Default entrypoint
CMD ["bash", "start.sh"]