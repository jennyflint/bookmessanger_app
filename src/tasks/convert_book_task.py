from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.enums.websocket_enums import WebsocketTypeEnum
from src.models.book import Book, CompleteBook
from src.services.convert_book_service import ConvertBookService
from src.services.job_celery_service import JobCeleryService


@celery_app.task(name="convert_book_task")  # type: ignore[untyped-decorator]
def convert_book_task(
    job_id: int, format_type: FormatTypeEnum, template: TemplateTypeEnum
) -> str:
    job_service = JobCeleryService(job_id, is_publish=True)

    book = job_service.get_target_object_after_verify(Book)

    websocket_channel = f"user_notifications_{book.user_id}"
    ws_data = {
        "type": WebsocketTypeEnum.BOOK_CONVERTED,
        "book_id": book.id,
    }

    job_service.add_websocket_channel(websocket_channel, ws_data)
    return job_service.main(
        convert_task,
        book=book,
        format_type=format_type,
        template=template,
    )


def convert_task(
    db: Session,
    book: Book,
    format_type: FormatTypeEnum,
    template: TemplateTypeEnum,
) -> bool:
    filename = ""
    try:
        cbs = ConvertBookService(book=book, format_type=format_type, template=template)
        filename = cbs.main()
        complete_book = CompleteBook(book=book, format=format_type, name=filename)
        db.add(complete_book)
        db.commit()

    except Exception:
        return False
    else:
        return True
