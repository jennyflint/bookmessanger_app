import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from src.exceptions.file_exception import FileSaveError
from src.schema.response.file_upload_response import FileUploadResponse


class FileService:
    def __init__(self, base_dir: str = "storage/"):
        self.base_dir = base_dir

    def _ensure_dir(self, path: Path | str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, ext: str) -> str:
        return f"{uuid.uuid4()}{ext}"

    async def save(
        self,
        file: UploadFile,
        sub_path: str = "",
        filename: str | None = None,
    ) -> FileUploadResponse:

        original_name = file.filename or "unknown"
        ext = Path(original_name).suffix.lower()
        dir_path = Path(self.base_dir) / sub_path
        self._ensure_dir(dir_path)
        safe_name = filename or self._generate_filename(ext)
        file_path = Path(dir_path) / safe_name

        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)
        except Exception as err:
            err_msg = f"Error saving file: {err}"
            raise FileSaveError(err_msg) from err

        return FileUploadResponse(
            message="File Uploaded Successfully",
            original_name=original_name,
            saved_name=safe_name,
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
        )
