from typing import Annotated, Any

from authx import TokenPayload
from fastapi import Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.app import PLAYWRIGHT_WS_ENDPOINT
from src.database import get_db
from src.enums.enums import FormatTypeEnum
from src.models.book import Book
from src.models.user import User
from src.security import auth
from src.services.convert_service import ConvertService
from src.services.converters.convert import PdfConverter
from src.services.file_service import FileService
from src.services.module.playwright_pdf_module import PlaywrightPDFGenerator
from src.validators.file_validator import FileValidator


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(auth.access_token_required)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user_id = int(payload.sub)
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_file_service() -> FileService:
    return FileService()


def file_validator_dependency(
    *,
    allowed_extensions: set[str] | None = None,
    allowed_content_types: set[str] | None = None,
    max_size: int | str | None = None,
) -> Any:
    validator = FileValidator(
        allowed_extensions=allowed_extensions,
        allowed_content_types=allowed_content_types,
        max_size=max_size,
    )

    async def _validate(file: Annotated[UploadFile, File()]) -> UploadFile:
        return await validator.validate(file)

    return Depends(_validate)


def get_converter_service() -> ConvertService:
    playwright_gen = PlaywrightPDFGenerator(PLAYWRIGHT_WS_ENDPOINT)
    pdf_converter = PdfConverter(playwright_gen)
    service = ConvertService()
    service.register(FormatTypeEnum.PDF, pdf_converter)

    return service


async def get_book_if_owner(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Book:
    stmt = select(Book).where(Book.id == book_id)

    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    if book.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this book",
        )

    return book
