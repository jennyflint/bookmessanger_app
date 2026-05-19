from pathlib import Path

from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.websocket_enums import WebsocketTypeEnum
from src.models.book import Book
from src.services.cli_parsing_book_service import CliParsingBookService
from src.services.job_celery_service import JobCeleryService


@celery_app.task(name="parsing_book_task")  # type: ignore[untyped-decorator]
def parsing_book_task(job_id: int) -> str:
    job_service = JobCeleryService(job_id, is_publish=True)
    book = job_service.get_target_object_after_verify(Book)
    websocket_channel = f"user_notifications_{book.user_id}"
    ws_data = {
        "type": WebsocketTypeEnum.CREATE_BOOK_MODEL,
        "book_id": book.id,
    }
    job_service.add_websocket_channel(websocket_channel, ws_data)
    return job_service.main(parsing_task, book=book)


def parsing_task(_db: Session, book: Book) -> bool:
    bookname = "book_" + str(book.id) + Path(book.original_name).suffix
    user_upload_dir = Path(str(book.user_id))
    user_model_dir = Path(str(book.user_id))
    input_file = str(user_upload_dir / bookname)
    output_file = str((user_model_dir / str(book.id)).with_suffix(".json"))
    try:
        print(8)
        celery_app.send_task(
            "parsing.book",
            args=[
                CliParsingBookService.default_command_parsing_book(
                    input_file, output_file
                )
            ],
            queue="cli_tasks",
        )
    except Exception as e:
        print(e)
        return False
    else:
        return True
