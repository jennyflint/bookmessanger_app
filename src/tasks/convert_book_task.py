import json

import redis
from sqlalchemy import select

from src.celery_app import celery_app
from src.database import SessionLocal
from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.enums.websocket_enums import WebsocketStatusEnum, WebsocketTypeEnum
from src.models.book import Book, CompleteBook
from src.models.job import Job
from src.services.convert_book_service import ConvertBookService
from src.settings.settings import app_settings


redis_client = redis.Redis.from_url(app_settings.redis_url)


@celery_app.task(name="convert_book_task")  # type: ignore[untyped-decorator]
def convert_book_task(
    job_id: int, format_type: FormatTypeEnum, template: TemplateTypeEnum
) -> str:

    with SessionLocal() as db:
        stmt_job = select(Job).where(Job.id == job_id)

        result_job = db.execute(stmt_job)
        job = result_job.scalar_one_or_none()

        if not job or job.object_table != Book.__tablename__:
            return f"Error: Job with ID {job_id} not found."

        stmt_book = select(Book).where(Book.id == job.object_id)

        result_book = db.execute(stmt_book)
        book = result_book.scalar_one_or_none()

        if not book:
            return f"Error: Book with ID {job.object_id} not found."

        filename = ""
        try:
            cbs = ConvertBookService(
                book=book, format_type=format_type, template=template
            )
            filename = cbs.main()

            complete_book = CompleteBook(book=book, format=format_type, name=filename)
            db.add(complete_book)
            db.commit()

            ws_data = {
                "type": WebsocketTypeEnum.BOOK_CONVERTED,
                "job_id": job_id,
                "book_id": book.id,
                "status": WebsocketStatusEnum.SUCCESS,
                "message": "Your book has been successfully converted!",
            }
            res_message = (
                f"Successfully started processing job {job_id}. Output file: {filename}"
            )
        except Exception as e:
            ws_data = {
                "type": WebsocketTypeEnum.BOOK_CONVERTED,
                "job_id": job_id,
                "book_id": book.id,
                "status": WebsocketStatusEnum.ERROR,
                "message": str(e),
            }

            res_message = f"Failed to process job {job_id}. Error: {e!s}"
        redis_client.publish(f"user_notifications_{book.user_id}", json.dumps(ws_data))

        return res_message
