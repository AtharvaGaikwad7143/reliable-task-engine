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
    worker_prefetch_multiplier=1,
    task_acks_late=True,                 # Do not ACK until the task finishes
    task_reject_on_worker_lost=True      # Re-queue if the worker process is killed abruptly
)

# Import tasks so Celery registers them
import src.worker.tasks