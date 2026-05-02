from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from starlette import status

from dependencies import (
    CurrentUser,
    file_validator_dependency,
)
from schema.response.book_response import BookResponse
from services.upload_book_service import UploadBookService


router = APIRouter()

book_validator = file_validator_dependency(
    allowed_extensions={".pdf", ".txt"},
    allowed_content_types={"application/pdf", "text/plain"},
    max_size="15MB",
)


@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, book_validator],
    current_user: CurrentUser,
    upload_book_service: Annotated[UploadBookService, Depends()],
) -> BookResponse:

    book = await upload_book_service.upload_book(current_user.id, file)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book upload failed"
        )

    return BookResponse(id=book.id, name=book.original_name)
