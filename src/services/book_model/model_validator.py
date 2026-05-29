from typing import Any

from src.exceptions.validate_book_model_exception import CharacterInconsistentError
from src.schema.request.book_request import Character


class ModelValidator:
    def __init__(
        self, book_model: dict[str, Any], incoming_characters: list[Character]
    ) -> None:
        self.book_model = book_model
        self.incoming_characters = incoming_characters

    def validate(self) -> bool:

        self.validate_incoming_character()

        return True

    def validate_incoming_character(self) -> None:
        ids1 = {char["id"] for char in self.book_model.get("characters", [])}
        ids2 = {char.id for char in self.incoming_characters}

        missing_in_both = ids1 ^ ids2

        if missing_in_both:
            raise CharacterInconsistentError(missing_in_both)
