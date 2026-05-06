from pathlib import Path
from typing import Annotated

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import (
    get_file_service,
)
from src.models.book import Book
from src.models.job import Job, JobTypeEnum
from src.services.file_service import FileService
from src.settings.settings import book_settings
from src.tasks.parsing_book_task import parsing_book_task


class UploadBookService:
    def __init__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        file_service: Annotated[FileService, Depends(get_file_service)],
    ):
        self.file_service = file_service
        self.db = db

    async def upload_book(self, user_id: int, file: UploadFile) -> Book | None:
        if not file.filename:
            return None
        book = Book(original_name=file.filename, user_id=user_id)
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)

        sub_path = f"{book_settings.storage_book_upload_dir}/{user_id}"
        print(sub_path)
        filename = f"{book_settings.prefix_book_name}{book.id}"
        filename = filename + Path(file.filename).suffix.lower()

        await self.file_service.save(file=file, sub_path=sub_path, filename=filename)

        await self._create_job(book)

        return book

    async def _create_job(self, book: Book) -> Job:
        job = Job(
            object_id=book.id,
            object_table=book.__tablename__,
            type=JobTypeEnum.BOOK_PARSING,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        parsing_book_task.delay(job.id)
        return job
