from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

# create_async_engine manages a pool of connections to the database
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,           # Set to True to log SQL queries during debugging
    pool_size=5,          # Maintain 5 connections in the pool
    max_overflow=10       # Allow up to 10 extra connections during traffic spikes
)

# async_sessionmaker creates new database sessions for each request
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db():
    """Dependency injection to provide a DB session to FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session