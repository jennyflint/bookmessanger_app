from pydantic import BaseModel


class AvatarListResponse(BaseModel):
    items: list[str]
