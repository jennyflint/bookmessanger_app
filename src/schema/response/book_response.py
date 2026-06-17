from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.enums.book import BookActionStatusEnum
from src.schema.response.job_response import JobResponse


class BookResponse(BaseModel):
    id: int
    name: str


class ExportBookResponse(BaseModel):
    id: int
    name: str | None = None
    book_id: int
    status: BookActionStatusEnum
    format: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookDetailResponse(BaseModel):
    id: int
    original_name: str
    created_at: datetime
    updated_at: datetime
    actions: list[JobResponse] = []

    model_config = ConfigDict(from_attributes=True)

    def add_job(self, job_obj: JobResponse) -> None:
        if job_obj and not any(x.id == job_obj.id for x in self.actions):
            self.actions.append(JobResponse.model_validate(job_obj))
