from sqlalchemy import select

from src.celery_app import celery_app
from src.database import SessionLocal
from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.models.book import Book, CompleteBook
from src.models.job import Job
from src.services.convert_book_service import ConvertBookService


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

        cbs = ConvertBookService(book=book, format_type=format_type, template=template)
        filename = cbs.main()

        complete_book = CompleteBook(book=book, format=format_type, name=filename)

        db.add(complete_book)
        db.commit()

        return f"Successfully started processing job {job_id}. Output file: {filename}"
