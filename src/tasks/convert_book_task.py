from typing import Any

from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.enums.websocket_enums import WebsocketStatusEnum, WebsocketTypeEnum
from src.models.book import Book, CompleteBook
from src.models.job import Job
from src.services.convert_book_service import ConvertBookService
from src.services.job_celery_service import JobCeleryService, TaskResult


@celery_app.task(name="convert_book_task")  # type: ignore[untyped-decorator]
def convert_book_task(
    job_id: int, format_type: FormatTypeEnum, template: TemplateTypeEnum
) -> str:
    job_service = JobCeleryService(job_id, is_publish=True)
    return job_service.main(convert_task, format_type=format_type, template=template)


def convert_task(
    db: Session,
    job: Job,
    target_object: Any,
    format_type: FormatTypeEnum,
    template: TemplateTypeEnum,
) -> TaskResult:
    if not isinstance(target_object, Book):
        err_msg = (
            f"Expected target_object to be of type Book, "
            f"got {type(target_object).__name__}"
        )
        raise TypeError(err_msg)

    filename = ""
    book = target_object
    res_message = ""
    try:
        cbs = ConvertBookService(book=book, format_type=format_type, template=template)
        filename = cbs.main()

        complete_book = CompleteBook(book=book, format=format_type, name=filename)
        db.add(complete_book)
        db.commit()

        ws_data = {
            "type": WebsocketTypeEnum.BOOK_CONVERTED,
            "job_id": job.id,
            "book_id": book.id,
            "status": WebsocketStatusEnum.SUCCESS,
            "message": "Your book has been successfully converted!",
        }
        res_message = (
            f"Successfully started processing job {job.id}. Output file: {filename}"
        )
    except Exception as e:
        ws_data = {
            "type": WebsocketTypeEnum.BOOK_CONVERTED,
            "job_id": job.id,
            "book_id": book.id,
            "status": WebsocketStatusEnum.ERROR,
            "message": str(e),
        }
        res_message = f"Failed to process job {job.id}: Error -> {e!s}"

    return TaskResult(
        message=res_message,
        channel=f"user_notifications_{book.user_id}",
        ws_data=ws_data,
    )
