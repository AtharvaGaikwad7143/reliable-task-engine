import time
import asyncio
from uuid import UUID
from sqlalchemy.future import select
from src.core.database import AsyncSessionLocal
from src.db.models import Task, TaskState
from src.worker.main import celery_app

async def _update_task_status(task_id: UUID, status: TaskState):
    """Helper function to update the database asynchronously."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if task:
            task.status = status
            await db.commit()

@celery_app.task(bind=True, name="process_task")
def process_task(self, task_id_str: str):
    """The synchronous Celery task that executes the work."""
    task_id = UUID(task_id_str)
    
    # 1. Mark task as RUNNING
    asyncio.run(_update_task_status(task_id, TaskState.RUNNING))
    
    print(f"Executing task {task_id}...")
    
    # 2. Simulate 10 seconds of hard work
    time.sleep(10) 
    
    # 3. Mark task as COMPLETED
    asyncio.run(_update_task_status(task_id, TaskState.COMPLETED))
    
    print(f"Task {task_id} complete.")
    return str(task_id)