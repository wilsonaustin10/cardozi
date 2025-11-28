from celery import Celery
from src.core.config import settings

# Initialize Celery app
celery = Celery(
    'cardozi_worker',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['src.worker.tasks']
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
)