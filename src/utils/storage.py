from pathlib import Path

from src.config.book import STORAGE_MODEL_BOOK_DIR
from src.exceptions.storage_exception import FileNotExistError
from src.models.book import Book


class Storage:
    @staticmethod
    def get_book_model_by_book(book: Book) -> str:
        path_to_file = (
            f"{STORAGE_MODEL_BOOK_DIR}/{book.user.id}/{book.id}/{book.id}.json"
        )
        return Storage._read_file(path_to_file)

    @staticmethod
    def _read_file(path_to_file: str) -> str:
        if not Path(path_to_file).exists():
            raise FileNotExistError(path_to_file)

        with Path(path_to_file).open(encoding="utf-8") as file:
            content = file.read()
        return content
