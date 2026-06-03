from enum import Enum
from typing import Annotated, Any

from authx import RequestToken, TokenPayload
from fastapi import (
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.book import Book, ExportBook
from src.models.user import User
from src.repositories.export_book_repository import ExportBookRepository
from src.schema.response.enum_response import EnumOptionResponse
from src.security import auth
from src.services.book_list_service import BookListService
from src.services.export_book_list_service import ExportBookListService
from src.services.export_book_service import ExportBookService
from src.services.file_service import FileService
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


async def get_current_user_from_websocket(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing token in URL"
        )

    try:
        req_token = RequestToken(token=token, location="query")
        payload = auth.verify_token(req_token)
    except Exception as e:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason=f"Invalid token: {e!s}"
        ) from e

    if payload.type != "access":
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Token must be an access token"
        )

    user_id = int(payload.sub)
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )

    if not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="User account is deactivated"
        )

    return user


WsCurrentUser = Annotated[User, Depends(get_current_user_from_websocket)]


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


def get_enum_options(enum_cls: type[Enum]) -> list[EnumOptionResponse]:
    return [
        EnumOptionResponse(
            value=item.value, label=item.name.replace("_", " ").capitalize()
        )
        for item in enum_cls
    ]


def get_book_list_service(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookListService:
    return BookListService(db, current_user)


def get_export_book_list_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportBookListService:
    return ExportBookListService(db)


def get_export_book_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportBookService:
    return ExportBookService(db)


def get_export_book_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportBookRepository:
    return ExportBookRepository(db)


async def get_export_book_if_owner(
    export_id: int,
    book: Annotated[Book, Depends(get_book_if_owner)],
    export_book_repository: Annotated[
        ExportBookRepository, Depends(get_export_book_repository)
    ],
) -> ExportBook:

    export_book = await export_book_repository.get_by_id(export_id)

    if not export_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export book not found"
        )

    if export_book.book_id != book.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this export book",
        )

    return export_book
