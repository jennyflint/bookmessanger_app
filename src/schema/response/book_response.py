from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schema.response.job_response import JobResponse


class BookResponse(BaseModel):
    id: int
    name: str


class CompleteBookResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookDetailResponse(BaseModel):
    id: int
    original_name: str
    created_at: datetime
    updated_at: datetime
    complete_books: list[CompleteBookResponse] = []
    jobs: list[JobResponse] = []

    model_config = ConfigDict(from_attributes=True)

    def add_complete_book(self, cb_obj: CompleteBookResponse) -> None:
        if cb_obj and not any(x.id == cb_obj.id for x in self.complete_books):
            self.complete_books.append(CompleteBookResponse.model_validate(cb_obj))

    def add_job(self, job_obj: JobResponse) -> None:
        if job_obj and not any(x.id == job_obj.id for x in self.jobs):
            self.jobs.append(JobResponse.model_validate(job_obj))
