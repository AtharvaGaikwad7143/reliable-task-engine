from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.core.database import get_db
from src.db.models import Task
from src.schemas.task import TaskCreate, TaskResponse
from src.worker.tasks import process_task

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    # 1. Create the database record in PENDING state
    new_task = Task(
        name=task_in.name,
        payload=task_in.payload
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    process_task.delay(str(new_task.id))

    return new_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task

# @router.post("/", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
# async def submit_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
#     new_task = Task(name=task_in.name, payload=task_in.payload)
#     db.add(new_task)
#     await db.commit()
#     await db.refresh(new_task)
    
#     # NEW: Dispatch to Celery/Redis
#     process_task.delay(str(new_task.id))

#     return new_task