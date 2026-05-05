import json

import redis
from sqlalchemy import select

from src.celery_app import celery_app
from src.config.app import REDIS_URL
from src.database import SessionLocal
from src.enums.websocket_enums import WebsocketStatusEnum, WebsocketTypeEnum
from src.models.book import Book
from src.models.job import Job, JobStatusEnum


redis_client = redis.Redis.from_url(REDIS_URL)


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

        stmt_book = select(Book).where(Book.id == job.object_id)

        result_book = db.execute(stmt_book)
        book = result_book.scalar_one_or_none()

        if not book:
            return f"Error: Book with ID {job.object_id} not found."

        # Todo need add script for run parsing book
        try:
            message = {
                "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
                "job_id": job_id,
                "book_id": book.id,
                "status": WebsocketStatusEnum.SUCCESS,
                "message": "Your book has been successfully converted!",
            }
        except Exception as e:
            message = {
                "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
                "job_id": job_id,
                "book_id": book.id,
                "status": WebsocketStatusEnum.ERROR,
                "message": str(e),
            }

        redis_client.publish(f"user_notifications_{book.user_id}", json.dumps(message))
        return f"Successfully started processing job {job_id}"
