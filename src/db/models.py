import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base


Base = declarative_base()

class TaskState(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False) # e.g., "process_payment", "generate_report"
    status = Column(Enum(TaskState), default=TaskState.PENDING, nullable=False)
    payload = Column(JSONB, nullable=False, default={})
    result = Column(JSONB, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    cancel_requested = Column(Boolean, default=False, nullable=False)