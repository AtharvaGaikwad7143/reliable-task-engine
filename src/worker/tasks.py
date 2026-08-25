import time
import asyncio
import random
import redis
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

WorkerSessionLocal = async_sessionmaker(
    bind=worker_engine,
    expire_on_commit=False
)

sync_redis = redis.from_url(settings.REDIS_URL, decode_responses = True)


async def _get_task_status(task_id: UUID) -> TaskState:
    async with WorkerSessionLocal() as db:
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalars().first()

        return task.status if task else None


def _is_cancellation_requested(task_id: UUID) -> bool:
    """Fast, synchronous check against Redis RAM. NO POSTGRES."""
    return sync_redis.get(f"cancel_task:{str(task_id)}") == "true"


async def _update_task_status(task_id: UUID, status: TaskState):

    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if task:
            if task.cancel_requested and status != TaskState.CANCELLED:
                print(f"Late cancellation detected for {task_id}. Forcing CANCELLED state.")
                task.status = TaskState.CANCELLED
            else:
                task.status = status
                
            await db.commit()


@celery_app.task(
    bind=True,
    name="process_task",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)

def process_task(self, task_id_str: str):

    task_id = UUID(task_id_str)

    # 1. IDEMPOTENCY CHECK
    current_status = asyncio.run(
        _get_task_status(task_id)
    )

    if current_status == TaskState.COMPLETED:
        print(
            f"Task {task_id} already completed. "
            "Skipping (Idempotency)."
        )
        return str(task_id)

    try:
        # 2. RUNNING / RETRYING
        new_state = (
            TaskState.RETRYING
            if self.request.retries > 0
            else TaskState.RUNNING
        )

        asyncio.run(
            _update_task_status(
                task_id,
                new_state
            )
        )

        print(
            f"Executing task {task_id}... "
            f"(Attempt {self.request.retries + 1})"
        )

        # 3. LONG-RUNNING CHUNKED WORK
        for i in range(10):

            # Check cancellation before each chunk
            cancel_requested = _is_cancellation_requested(task_id)

            if cancel_requested:
                asyncio.run(
                    _update_task_status(
                        task_id,
                        TaskState.CANCELLED
                    )
                )

                print(
                    f"Task {task_id} cancelled."
                )

                return str(task_id)

            # Simulate one chunk of work
            time.sleep(1)

            print(
                f"Task {task_id} "
                f"processing chunk {i + 1}/10..."
            )

            # Simulate transient failure
            if random.random() < 0.30:
                print(
                    f"Simulated transient failure "
                    f"for {task_id}!"
                )

                raise ConnectionError(
                    "Simulated network drop."
                )

        # 4. SUCCESS
        asyncio.run(
            _update_task_status(
                task_id,
                TaskState.COMPLETED
            )
        )

        print(
            f"Task {task_id} complete."
        )

        return str(task_id)

    except Exception as e:

        # Final attempt: permanently failed
        if self.request.retries >= self.max_retries:

            asyncio.run(
                _update_task_status(
                    task_id,
                    TaskState.FAILED
                )
            )

            print(
                f"Task {task_id} permanently failed: {e}"
            )

        raise