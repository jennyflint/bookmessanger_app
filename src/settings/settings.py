from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    playwright_ws_port: str = "3000"
    app_host: str = "localhost"
    marketing_url: str = ""
    app_url: str = ""
    cors_origin_urls: list[str] = []

    @property
    def playwright_ws_endpoint(self) -> str:
        return f"ws://playwright_browser:{self.playwright_ws_port}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


AlgorithmType = Literal["HS256",]


class AuthSettings(BaseSettings):
    # Google OAuth
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_server_metadata_url: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    google_client_kwargs: dict[str, str] = {"scope": "openid email profile"}
    redirect_oauth_uri: str = ""

    # JWT & Sessions
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    jwt_algorithm: AlgorithmType = "HS256"
    jwt_secret_key: str = ""
    session_secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class BookSettings(BaseSettings):
    allowed_extensions: set[str] = {".epub", ".txt", ".fb2"}
    allowed_content_types: set[str] = {
        "application/epub+zip",
        "text/plain",
        "application/octet-stream",
    }

    max_size: str = "20MB"
    prefix_book_name: str = "book_"
    book_html_template: Path = Path("uploads/books/users")
    storage: Path = Path("storage")

    @property
    def storage_book_upload_dir(self) -> Path:
        return Path("/app") / "storage" / "upload_books"

    @property
    def storage_book_original_upload_dir(self) -> Path:
        return Path("/app") / "storage" / "upload_books" / "original"

    @property
    def storage_model_book_dir(self) -> Path:
        return Path("/app") / "storage" / "model_books"

    @property
    def storage_html_template(self) -> Path:
        return Path("books") / "templates" / "html"

    @property
    def storage_export_book(self) -> Path:
        return Path("/app") / "storage" / "converted_books"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DatabaseSettings(BaseSettings):
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    db_host: str = "db"
    db_port: str = "5432"

    db_driver_async: str = "postgresql+asyncpg"
    db_driver_sync: str = "postgresql+psycopg2"

    @property
    def async_url(self) -> str:
        return (
            f"{self.db_driver_async}://{self.postgres_user}:{self.postgres_password}@"
            f"{self.db_host}:{self.db_port}/{self.postgres_db}"
        )

    @property
    def sync_url(self) -> str:
        return (
            f"{self.db_driver_sync}://{self.postgres_user}:{self.postgres_password}@"
            f"{self.db_host}:{self.db_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_ignore_empty=True
    )


class CharacterAvatar(BaseSettings):
    avatar_dir: Path = Path("storage/characters/avatars")


db_settings = DatabaseSettings()
book_settings = BookSettings()
app_settings = AppSettings()
auth_settings = AuthSettings()
character_avatar_settings = CharacterAvatar()
