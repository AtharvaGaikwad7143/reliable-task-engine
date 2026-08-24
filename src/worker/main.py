from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL, # We use Redis to store minimal Celery states if needed
)

# Configure Celery to find tasks automatically
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # This prevents Celery from accepting messages too fast before it finishes them
    worker_prefetch_multiplier=1 
)

# Import tasks so Celery registers them
import src.worker.tasks