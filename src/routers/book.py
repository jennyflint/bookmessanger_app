from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database import get_db
from src.dependencies import (
    CurrentUser,
    file_validator_dependency,
    get_book_if_owner,
)
from src.models.book import Book
from src.models.job import Job, JobStatusEnum
from src.schema.request.book_request import ConvertBookRequest
from src.schema.response.book_response import BookResponse
from src.services.upload_book_service import UploadBookService
from src.tasks.convert_book_task import convert_book_task
from src.utils.storage import Storage


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


@router.post("/convert/{book_id}")
async def convert_book(
    request: ConvertBookRequest,
    book: Annotated[Book, Depends(get_book_if_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:

    stmt = (
        select(Job)
        .where(Job.object_table == Book.__tablename__, Job.object_id == book.id)
        .order_by(Job.id.desc())
    )
    job = await db.scalar(stmt)

    if not job or job.status != JobStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book convert failed"
        )

    convert_book_task.delay(job.id, request.format, request.template)

    return {"message": f"Book conversion started for job {job.id}."}


@router.get(
    "/model/{book_id}",
    responses={400: {"description": "Bad Request - File not found or invalid"}},
)
async def get_book_model(
    book: Annotated[Book, Depends(get_book_if_owner)],
) -> Response:
    try:
        json_data = Storage.get_book_model_by_book(book)

        return Response(content=json_data, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
