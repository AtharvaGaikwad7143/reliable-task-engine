from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Reliable Task Engine"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/task_engine"
    REDIS_URL: str = "redis://localhost:6379/0" 
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()