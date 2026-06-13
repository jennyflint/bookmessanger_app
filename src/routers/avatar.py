from fastapi import APIRouter, HTTPException
from starlette import status

from src.exceptions.avatar_exception import AvatarFolderNotFoundError
from src.schema.response.avatar import AvatarListResponse
from src.services.avatar_service import AvatarService


router = APIRouter()


@router.get("/list")
def get_random_avatars(limit: int = 30) -> AvatarListResponse:
    try:
        avatars = AvatarService.get_random_avatars(limit)
    except AvatarFolderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avatars not found"
        ) from e
    return AvatarListResponse(items=avatars)
