import time
import asyncio
import random
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.pool import NullPool
from src.core.config import settings
from src.db.models import Task, TaskState
from src.worker.main import celery_app

worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool, echo=False)
WorkerSessionLocal = async_sessionmaker(bind=worker_engine, expire_on_commit=False)

async def _get_task_status(task_id: UUID) -> TaskState:
    """Helper to check current DB state."""
    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        return task.status if task else None

async def _update_task_status(task_id: UUID, status: TaskState):
    """Helper function to update the database asynchronously."""
    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if task:
            task.status = status
            await db.commit()

# NEW: max_retries=3, autoretry_for catches any Exception, retry_backoff adds exponential delay
@celery_app.task(bind=True, name="process_task", max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def process_task(self, task_id_str: str):
    task_id = UUID(task_id_str)
    
    # 1. IDEMPOTENCY CHECK
    # If this is a duplicate execution, the DB will already say COMPLETED.
    current_status = asyncio.run(_get_task_status(task_id))
    if current_status == TaskState.COMPLETED:
        print(f"Task {task_id} already completed. Skipping (Idempotency).")
        return str(task_id)

    # 2. Mark as RUNNING (or RETRYING if it's a retry)
    new_state = TaskState.RETRYING if self.request.retries > 0 else TaskState.RUNNING
    asyncio.run(_update_task_status(task_id, new_state))
    print(f"Executing task {task_id}... (Attempt {self.request.retries + 1})")
    
    # 3. Simulate work and a random failure (30% chance to fail and trigger a retry)
    time.sleep(5) 
    if random.random() < 0.30:
        print(f"Simulated transient failure for {task_id}!")
        raise ConnectionError("Simulated network drop.")
    
    # 4. Mark as COMPLETED
    asyncio.run(_update_task_status(task_id, TaskState.COMPLETED))
    print(f"Task {task_id} complete.")
    return str(task_id)