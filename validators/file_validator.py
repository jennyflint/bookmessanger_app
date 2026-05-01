from pathlib import Path

from fastapi import HTTPException, UploadFile

from utils.utils import parse_size


class FileValidator:
    def __init__(
        self,
        allowed_extensions: set[str] | None = None,
        allowed_content_types: set[str] | None = None,
        max_size: int | str | None = None,
    ):
        self.allowed_extensions = allowed_extensions
        self.allowed_content_types = allowed_content_types
        self.max_size = parse_size(max_size) if max_size else None

    async def validate(self, file: UploadFile) -> UploadFile:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()

        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise HTTPException(400, f"File extension not allowed: {ext}")

        if (
            self.allowed_content_types
            and file.content_type not in self.allowed_content_types
        ):
            raise HTTPException(400, f"File type not allowed: {file.content_type}")

        if self.max_size:
            file.file.seek(0, 2)
            size = file.file.tell()
            await file.seek(0)

            if size > self.max_size:
                raise HTTPException(
                    413,
                    f"File ({self.max_size} bytes) exceeds the maximum allowed size",
                )

        return file
