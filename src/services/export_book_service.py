from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.enums.export_book import ExportBookStatusEnum
from src.models.book import Book, ExportBook
from src.models.job import Job, JobTypeEnum
from src.schema.request.book_request import Character
from src.services.book_model.model_validator import ModelValidator
from src.tasks.convert_book_task import convert_book_task


class ExportBookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export(
        self,
        book: Book,
        book_model: dict[str, Any],
        characters: list[Character],
        format_file: FormatTypeEnum,
        template: TemplateTypeEnum,
    ) -> None:
        validator = ModelValidator(book_model, characters)
        validator.validate()
        export_book = await self._create_export_book(book, format_file)

        job = Job(
            object_id=export_book.id,
            object_table=export_book.__tablename__,
            type=JobTypeEnum.BOOK_CONVERTING,
        )
        self.db.add(job)

        await self.db.commit()
        await self.db.refresh(job)

        convert_book_task.delay(job.id, format_file, template, book.user_id)

    async def _create_export_book(self, book: Book, format_file: str) -> ExportBook:
        export_book = ExportBook(
            book_id=book.id, status=ExportBookStatusEnum.PENDING, format=format_file
        )

        self.db.add(export_book)

        await self.db.flush()
        return export_book
