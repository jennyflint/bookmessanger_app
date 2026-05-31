from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.job import JobStatusEnum, JobTypeEnum


class JobResponse(BaseModel):
    id: int
    status: JobStatusEnum
    type: JobTypeEnum
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
