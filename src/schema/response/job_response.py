from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: int
    object_id: int
    object_table: str
    count_attempts: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
