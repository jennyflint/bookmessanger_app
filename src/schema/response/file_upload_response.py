from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    message: str
    original_name: str
    saved_name: str
    file_path: str
    content_type: str
