import base64
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.services.avatar_service import AvatarService
from src.settings.settings import character_avatar_settings


BASE_AVATAR_DIR = Path("/app") / character_avatar_settings.avatar_dir


class ReplaceModelValues:
    def __init__(self, book_model: dict[str, Any]) -> None:
        self.book_model = book_model

    def replace_characters(self, characters: list[dict[str, Any]]) -> None:
        self._encode_avatars_to_base64(characters)
        self._merge_updated_characters(characters)

    def _get_local_avatar_path(
        self, avatar_url: str | None, base_dir: Path
    ) -> Path | None:
        if not avatar_url or not avatar_url.endswith(".png"):
            return None

        parsed_path = urlparse(avatar_url).path
        if "avatars/" in parsed_path:
            relative_path = parsed_path.split("avatars/")[-1]
        else:
            relative_path = Path(parsed_path).name

        return (base_dir / relative_path).with_suffix(".png")

    def _read_image_as_base64(self, file_path: Path) -> str | None:
        if not file_path.exists():
            print(f"Error file not found: {file_path}")
            return None

        try:
            with file_path.open("rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _encode_avatars_to_base64(self, characters: list[dict[str, Any]]) -> None:
        if characters:
            for char in characters:
                char["avatar"] = self._encode_avatar_by_path(str(char.get("avatar")))

        else:
            avatars = AvatarService.get_random_avatars(
                len(self.book_model["characters"])
            )
            for i, avatar in enumerate(avatars):
                new_character = {
                    "avatar": self._encode_avatar_by_path(avatar),
                    "id": self.book_model["characters"][i].get("id"),
                }
                characters.append(new_character)

    def _encode_avatar_by_path(self, avatar: str) -> str | None:
        local_file_path = self._get_local_avatar_path(avatar, BASE_AVATAR_DIR)
        if local_file_path:
            base64_data = self._read_image_as_base64(local_file_path)
            if base64_data:
                return base64_data

        return None

    def _merge_updated_characters(
        self, updated_characters: list[dict[str, Any]]
    ) -> None:
        update_mapping = {
            item["id"]: item for item in updated_characters if "id" in item
        }

        merged_list = []
        for base_item in self.book_model.get("characters", []):
            merged_item = base_item.copy()
            char_id = merged_item.get("id")

            if char_id in update_mapping:
                merged_item.update(update_mapping[char_id])

            merged_list.append(merged_item)

        self.book_model["characters"] = merged_list

    def get_book_model(self) -> dict[str, Any]:
        return self.book_model
