from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

MAX_FILE_SIZE: str = "15MB"
ALLOWED_CONTENT_TYPES: list[str] = ["text/plain"]
ALLOWED_EXTENSIONS: list[str] = [".txt"]
BOOK_HTML_TEMPLATE: Path = Path("uploads") / "books" / "users"
PREFIX_BOOK_NAME: str = "book_"

# Storage Directories
STORAGE_BOOK_UPLOAD_DIR: Path = Path("uploads") / "books" / "users"
