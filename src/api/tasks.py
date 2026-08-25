from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.core.database import get_db
from src.db.models import Task, TaskState
from src.schemas.task import TaskCreate, TaskResponse
from src.worker.tasks import process_task
from src.core.redis import redis_client
from src.api.deps import rate_limiter

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limiter)])
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

@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id : UUID, db : AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()

    if not task: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Task not found")
    
    if task.status in {TaskState.COMPLETED, TaskState.FAILED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Task cannot be cancelled")

    task.cancel_requested = True
    await db.commit()
    await redis_client.set(f"cancel_task:{str(task_id)}", "true", ex = 86400)
    await db.refresh(task)
    return task