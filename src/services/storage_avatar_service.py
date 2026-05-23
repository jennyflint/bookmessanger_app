from pathlib import Path

from src.settings.settings import character_avatar_settings


class StorageAvatarService:
    def __init__(self) -> None:
        self.avatar_dir = character_avatar_settings.avatar_dir

    def save(self, avatar_name: str, avatar_data: bytes, avatar_style: str) -> None:
        avatar_path = self.avatar_dir / avatar_style / avatar_name
        avatar_path.parent.mkdir(parents=True, exist_ok=True)
        with Path.open(avatar_path, "wb") as f:
            f.write(avatar_data)
