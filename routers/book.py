from typing import Annotated, Any

from fastapi import APIRouter, Depends, UploadFile

from config.book import BASE_STORAGE_DIR
from dependencies import file_validator_dependency, get_current_user, get_file_service
from models.user import User
from services.file_service import FileService


router = APIRouter()

book_validator = file_validator_dependency(
    allowed_extensions={".pdf", ".txt"},
    allowed_content_types={"application/pdf", "text/plain"},
    max_size="15MB",
)


@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, book_validator],
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> dict[str, Any]:
    result = await file_service.save(
        file=file, sub_path=f"{BASE_STORAGE_DIR}/{current_user.id}"
    )

    return {"message": "File uploaded successfully", **result.model_dump()}
