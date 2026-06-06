import base64
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.settings.settings import character_avatar_settings


class ReplaceModelValues:
    def __init__(self, book_model: dict[str, Any]) -> None:
        self.book_model = book_model

    def replace_characters(self, characters: list[dict[str, Any]]) -> None:
        base_avatars_dir = Path("/app") / character_avatar_settings.avatar_dir
        for char in characters:
            avatar_url = char.get("avatar")

            if avatar_url and avatar_url.endswith(".png"):
                parsed_path = urlparse(avatar_url).path

                if "avatars/" in parsed_path:
                    relative_path = parsed_path.split("avatars/")[-1]
                else:
                    relative_path = Path(parsed_path).name
                local_file_path = (base_avatars_dir / relative_path).with_suffix(".png")

                if local_file_path.exists():
                    try:
                        with local_file_path.open("rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode(
                                "utf-8"
                            )

                            char["avatar"] = f"data:image/png;base64,{encoded_string}"
                    except Exception as e:
                        print(f"Error reading file {local_file_path}: {e}")
                else:
                    print(f"Error file not found: {local_file_path}")

        update_mapping = {item["id"]: item for item in characters}

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
