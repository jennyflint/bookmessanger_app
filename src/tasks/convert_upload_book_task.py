import logging
from pathlib import Path

from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.enums.book import BookActionStatusEnum
from src.exceptions.file_exception import FileSaveError
from src.models.book import UploadBookConverter
from src.models.job import Job, JobTypeEnum
from src.services.converters.converter_to_txt import converter_factory
from src.services.job_celery_service import JobCeleryService
from src.settings.settings import book_settings
from src.tasks.parsing_book_task import parsing_book_task
from src.utils.storage import Storage


logger = logging.getLogger(__name__)


@celery_app.task(name="convert_upload_book_task")  # type: ignore[untyped-decorator]
def convert_upload_book_task(job_id: int) -> str:
    job_service = JobCeleryService(job_id, is_publish=True)

    upload_book = job_service.get_target_object_after_verify(UploadBookConverter)

    return job_service.main(
        convert_task,
        upload_book=upload_book,
    )


def convert_task(
    db: Session,
    upload_book: UploadBookConverter,
) -> bool:
    upload_book = db.merge(upload_book)
    upload_book.status = BookActionStatusEnum.PENDING
    book = upload_book.book
    db.commit()

    request_data = {
        "format": upload_book.extension,
        "path_to_file": str(
            Storage.get_upload_book(book.user_id, upload_book.filename)
        ),
    }

    try:
        converter = converter_factory.validate_python(request_data)
        text_lines = converter.convert()
        sub_path = f"{book_settings.storage_book_upload_dir}/{book.user_id}"
        filename = f"{book_settings.prefix_book_name}{book.id}.txt"

        try:
            with Path(f"{sub_path}/{filename}").open("w", encoding="utf-8") as file:
                for item in text_lines:
                    file.write(f"{item}\n")
        except Exception as err:
            err_msg = f"Error saving file: {err}"
            raise FileSaveError(err_msg) from err

        upload_book.status = BookActionStatusEnum.COMPLETED

    except Exception:
        logger.exception(f"Error converting book {upload_book.id}")
        upload_book.status = BookActionStatusEnum.FAILED
        db.commit()
        return False

    job = Job(
        object_id=book.id,
        object_table=book.__tablename__,
        type=JobTypeEnum.BOOK_PARSING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    parsing_book_task.delay(job.id)

    return True
