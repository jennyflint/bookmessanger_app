import random
from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette import status

from src.schema.response.avatar import AvatarListResponse
from src.settings.settings import app_settings


router = APIRouter()
AVATARS_DIR = Path("storage/characters/avatars")
ALLOWED_EXTENSIONS = {".svg", ".png"}


@router.get("/list")
def get_random_avatars(limit: int = 30) -> AvatarListResponse:
    if not AVATARS_DIR.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avatars not found"
        )

    all_avatars = [
        path
        for path in AVATARS_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    if not all_avatars:
        return AvatarListResponse(items=[])

    sample_size = min(limit, len(all_avatars))
    random_avatars = random.sample(all_avatars, sample_size)

    app_url = app_settings.app_url
    result = [
        f"{app_url}/static/avatars/{path.relative_to(AVATARS_DIR).as_posix()}"
        for path in random_avatars
    ]

    return AvatarListResponse(items=result)
