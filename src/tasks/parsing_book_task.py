import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.websocket_enums import WebsocketTypeEnum
from src.models.book import Book
from src.services.job_celery_service import JobCeleryService
from src.settings.settings import book_settings, cli_parsing_book_script


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
    bookname = str(book.id) + Path(book.original_name).suffix
    user_upload_dir = book_settings.storage_book_upload_dir / str(book.user_id)
    user_model_dir = book_settings.storage_model_book_dir / str(book.user_id)
    input_file = str(user_upload_dir / bookname)
    output_file = str((user_model_dir / str(book.id)).with_suffix(".json"))
    try:
        subprocess.run(  # noqa: S603
            cli_parsing_book_script.command_parsing_book(input_file, output_file),
            capture_output=True,
            text=True,
            shell=False,
            check=True,
        )

    except subprocess.CalledProcessError:
        return False
    else:
        return True
