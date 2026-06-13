import json
import logging
from pathlib import Path

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.database import SessionLocal
from src.enums.websocket_enums import WebsocketTypeEnum
from src.models.book import Book
from src.models.job import Job, JobStatusEnum
from src.services.cli_parsing_book_service import CliParsingBookService
from src.services.job_celery_service import JobCeleryService
from src.settings.settings import app_settings


redis_client = redis.Redis.from_url(app_settings.redis_url)

logger = logging.getLogger(__name__)


@celery_app.task(name="parsing_book_task")  # type: ignore[untyped-decorator]
def parsing_book_task(job_id: int) -> str:
    job_service = JobCeleryService(job_id, is_publish=True, is_callback=True)
    book = job_service.get_target_object_after_verify(Book)
    websocket_channel = f"user_notifications_{book.user_id}"
    ws_data = {
        "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
        "book_id": book.id,
    }
    job_service.add_websocket_channel(websocket_channel, ws_data)
    return job_service.main(parsing_task, book=book, job_id=job_id)


@celery_app.task(name="parsing_book_callback")  # type: ignore[untyped-decorator]
def parsing_book_callback(
    result_from_worker: dict[str, str], book_id: int, user_id: int, job_id: int
) -> str:
    status = None
    if result_from_worker.get("status") == "success":
        status = JobStatusEnum.COMPLETED
        ws_data = {
            "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
            "book_id": book_id,
            "status": status,
        }
    else:
        status = JobStatusEnum.FAILED
        ws_data = {
            "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
            "book_id": book_id,
            "status": status,
        }
    with SessionLocal() as db:
        stmt = select(Job).where(Job.id == job_id)

        result = db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            return f"Error: Job with ID {job_id} not found."

        job.status = status
        db.commit()

        redis_client.publish(f"user_notifications_{user_id}", json.dumps(ws_data))
        return f"Successfully started processing job {job_id}"


def parsing_task(_db: Session, book: Book, job_id: int) -> bool:
    bookname = "book_" + str(book.id) + Path(book.original_name).suffix
    user_upload_dir = Path(str(book.user_id))
    user_model_dir = Path(str(book.user_id))
    input_file = str(user_upload_dir / bookname)
    output_file = str((user_model_dir / str(book.id)).with_suffix(".json"))
    callback = celery_app.signature(
        "parsing_book_callback",
        kwargs={"book_id": book.id, "job_id": job_id, "user_id": book.user_id},
        options={"queue": "celery"},
    )
    try:
        celery_app.send_task(
            "parsing.book",
            args=[
                CliParsingBookService.default_command_parsing_book(
                    input_file, output_file
                )
            ],
            queue="cli_tasks",
            link=callback,
        )
    except Exception:
        logger.exception(f"Error parsing book {book.id}")
        return False
    else:
        return True
