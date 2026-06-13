import random
from pathlib import Path

from src.exceptions.avatar_exception import AvatarFolderNotFoundError
from src.settings.settings import app_settings


AVATARS_DIR = Path("storage/characters/avatars")
ALLOWED_EXTENSIONS = {".svg", ".png"}


class AvatarService:
    @staticmethod
    def get_random_avatars(limit: int = 30) -> list[str]:
        if not AVATARS_DIR.exists():
            raise AvatarFolderNotFoundError(AVATARS_DIR)

        all_avatars = [
            path
            for path in AVATARS_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ]

        if not all_avatars:
            return []

        sample_size = min(limit, len(all_avatars))
        random_avatars = random.sample(all_avatars, sample_size)

        app_url = app_settings.app_url
        return [
            f"{app_url}/static/avatars/{path.relative_to(AVATARS_DIR).as_posix()}"
            for path in random_avatars
        ]
