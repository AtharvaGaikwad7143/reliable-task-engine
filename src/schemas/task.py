from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from src.db.models import TaskState

class TaskCreate(BaseModel):
    name: str
    payload: Dict[str, Any]

class TaskResponse(BaseModel):
    id: UUID
    name: str
    status: TaskState
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)