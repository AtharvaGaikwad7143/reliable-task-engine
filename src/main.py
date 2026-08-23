from fastapi import FastAPI
from src.api import tasks
from src.core.database import engine
from src.db.models import Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (For Dev Only. We will use Alembic for Prod.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Reliable Task Engine", lifespan=lifespan)

app.include_router(tasks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}