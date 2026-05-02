from pydantic import BaseModel


class BookResponse(BaseModel):
    id: int
    name: str
