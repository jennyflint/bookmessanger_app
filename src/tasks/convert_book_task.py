import logging

from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.enums import FormatTypeEnum
from src.enums.export_book import ExportBookStatusEnum
from src.enums.websocket_enums import WebsocketTypeEnum
from src.models.book import ExportBook
from src.services.convert_book_service import ConvertBookService
from src.services.job_celery_service import JobCeleryService


logger = logging.getLogger(__name__)


@celery_app.task(name="convert_book_task")  # type: ignore[untyped-decorator]
def convert_book_task(job_id: int, format_type: FormatTypeEnum, user_id: int) -> str:
    job_service = JobCeleryService(job_id, is_publish=True)

    export_book = job_service.get_target_object_after_verify(ExportBook)
    websocket_channel = f"user_notifications_{user_id}"
    ws_data = {
        "type": WebsocketTypeEnum.BOOK_CONVERTED,
        "book_id": export_book.id,
        "convert_item_id": export_book.id,
    }

    job_service.add_websocket_channel(websocket_channel, ws_data)
    return job_service.main(
        convert_task,
        export_book=export_book,
        format_type=format_type,
    )


def convert_task(
    db: Session,
    export_book: ExportBook,
    format_type: FormatTypeEnum,
) -> bool:
    export_book = db.merge(export_book)
    export_book.status = ExportBookStatusEnum.PENDING
    db.commit()

    book = export_book.book
    try:
        characters_data = export_book.characters
        if not isinstance(characters_data, list):
            characters_data = []
        cbs = ConvertBookService(
            book=book,
            format_type=format_type,
            template=export_book.template,
            characters=characters_data,
        )
        filename = cbs.main()

        export_book.status = ExportBookStatusEnum.COMPLETED
        export_book.export_filename = filename

    except Exception:
        logger.exception(f"Error converting book {export_book.id}")
        export_book.status = ExportBookStatusEnum.FAILED
        return False
    finally:
        db.commit()

    return True
