import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
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
    get_book_list_service,
    get_export_book_list_service,
    get_export_book_service,
)
from src.exceptions.validate_book_model_exception import ModelBookValidatorError
from src.models.book import Book
from src.models.job import Job, JobStatusEnum, JobTypeEnum
from src.schema.request.book_request import ConvertBookRequest
from src.schema.response.book_response import (
    BookDetailResponse,
    BookResponse,
    ExportBookResponse,
)
from src.schema.response.response import PaginatedResponse
from src.services.book_list_service import BookListService
from src.services.export_book_list_service import ExportBookListService
from src.services.export_book_service import ExportBookService
from src.services.upload_book_service import UploadBookService
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
    export_book_service: Annotated[ExportBookService, Depends(get_export_book_service)],
) -> dict[str, str]:
    stmt = (
        select(Job)
        .where(Job.object_table == Book.__tablename__, Job.object_id == book.id)
        .where(Job.type == JobTypeEnum.BOOK_PARSING)
        .order_by(Job.id.desc())
    )
    parsing_job = await db.scalar(stmt)

    if not parsing_job or parsing_job.status != JobStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book convert failed"
        )

    book_model = json.loads(Storage.get_book_model_by_book(book))

    if not book_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book model not found"
        )

    try:
        await export_book_service.export(
            book, book_model, request.characters, request.format, request.template
        )
    except ModelBookValidatorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return {"message": f"Book conversion started for book {book.id}."}


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


@router.get("/list")
async def get_user_books(
    book_list_service: Annotated[BookListService, Depends(get_book_list_service)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Quantity of books per page")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    sort_by: Annotated[
        str, Query(description="Field for sorting (id, original_name, created_at)")
    ] = "id",
    sort_desc: Annotated[bool, Query(description="Sort in descending order?")] = True,
    filter_name: Annotated[
        str | None, Query(description="Filter by original_name")
    ] = None,
) -> PaginatedResponse[BookDetailResponse]:

    return await book_list_service.get_user_books_with_details(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
        filter_name=filter_name,
    )


@router.get("/list/download/{book_id}")
async def download_list(
    book: Annotated[Book, Depends(get_book_if_owner)],
    export_book_list_service: Annotated[
        ExportBookListService, Depends(get_export_book_list_service)
    ],
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "id",
    sort_desc: bool = True,
) -> PaginatedResponse[ExportBookResponse]:
    return await export_book_list_service.get_export_books(
        book=book,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
