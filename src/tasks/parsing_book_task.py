from sqlalchemy import select

from src.celery_app import celery_app
from src.database import SessionLocal
from src.models.job import Job, JobStatusEnum


@celery_app.task(name="parsing_book_task")  # type: ignore[untyped-decorator]
def parsing_book_task(job_id: int) -> str:

    with SessionLocal() as db:
        stmt = select(Job).where(Job.id == job_id)

        result = db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            return f"Error: Job with ID {job_id} not found."

        job.status = JobStatusEnum.PROCESSING
        db.commit()

        # Todo need add script for run parsing book

        return f"Successfully started processing job {job_id}"
