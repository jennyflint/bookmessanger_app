from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

MAX_FILE_SIZE: str = "15MB"
ALLOWED_CONTENT_TYPES: list[str] = ["text/plain"]
ALLOWED_EXTENSIONS: list[str] = [".txt"]
BOOK_HTML_TEMPLATE: Path = Path("uploads") / "books" / "users"
PREFIX_BOOK_NAME: str = "book_"

# Storage Directories
STORAGE: Path = Path("storage")
STORAGE_BOOK_UPLOAD_DIR: Path = STORAGE / "books" / "users"
STORAGE_MODEL_BOOK_DIR: Path = STORAGE / "books" / "models" / "json"
STORAGE_HTML_TEMPLATE: Path = STORAGE / "books" / "templates" / "html"
STORAGE_COMPLETE_BOOK: Path = STORAGE / "books" / "complete" / "books"
