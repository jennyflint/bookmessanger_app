from pathlib import Path

from src.exceptions.storage_exception import FileNotExistError
from src.models.book import Book
from src.settings.settings import book_settings


class Storage:
    @staticmethod
    def get_book_model_by_book(book: Book) -> str:
        path = book_settings.storage
        path = path / book_settings.storage_model_book_dir
        path = path / str(book.user.id) / f"{book.id}.json"
        return Storage._read_file(str(path))

    @staticmethod
    def _read_file(path_to_file: str) -> str:
        if not Path(path_to_file).exists():
            raise FileNotExistError(path_to_file)

        with Path(path_to_file).open(encoding="utf-8") as file:
            content = file.read()
        return content
