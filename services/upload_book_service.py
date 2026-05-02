from pathlib import Path
from typing import Annotated

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.book import BASE_STORAGE_DIR, PREFIX_BOOK_NAME
from database import get_db
from dependencies import (
    get_file_service,
)
from models.book import Book
from services.file_service import FileService


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
        book = Book(original_name=file.filename)
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)

        sub_path = f"{BASE_STORAGE_DIR}/{user_id}"
        filename = f"{PREFIX_BOOK_NAME}{book.id}"
        filename = filename + Path(file.filename).suffix.lower()

        await self.file_service.save(file=file, sub_path=sub_path, filename=filename)

        return book
