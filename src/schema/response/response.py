from math import ceil
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.limit) if self.limit > 0 else 0

    @property
    def current_page(self) -> int:
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1


class PaginatedResponse[T](BaseModel):
    data: list[T]
    meta: PaginationMeta


class StatusResponse(BaseModel):
    message: str
    success: bool
