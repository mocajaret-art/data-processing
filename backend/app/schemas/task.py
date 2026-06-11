import uuid
from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    file_id: uuid.UUID


class TaskResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_id: uuid.UUID
    status: str
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TaskDetail(TaskResponse):
    celery_task_id: str | None = None
    result_data: dict | None = None
    error_message: str | None = None
    file: dict | None = None
