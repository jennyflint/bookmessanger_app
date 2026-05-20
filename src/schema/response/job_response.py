from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.job import JobStatusEnum


class JobResponse(BaseModel):
    id: int
    status: JobStatusEnum
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
