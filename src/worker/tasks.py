import time
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.pool import NullPool
from src.core.config import settings
from src.db.models import Task, TaskState
from src.worker.main import celery_app

worker_engine = create_async_engine(
    settings.DATABASE_URL, 
    poolclass=NullPool,
    echo=False
)
WorkerSessionLocal = async_sessionmaker(bind=worker_engine, expire_on_commit=False)

async def _update_task_status(task_id: UUID, status: TaskState):
    """Helper function to update the database asynchronously."""
    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if task:
            task.status = status
            await db.commit()

@celery_app.task(bind=True, name="process_task")
def process_task(self, task_id_str: str):
    """The synchronous Celery task that executes the work."""
    task_id = UUID(task_id_str)
    
    asyncio.run(_update_task_status(task_id, TaskState.RUNNING))
    print(f"Executing task {task_id}...")
    
    time.sleep(10) 
    
    asyncio.run(_update_task_status(task_id, TaskState.COMPLETED))
    print(f"Task {task_id} complete.")
    return str(task_id)