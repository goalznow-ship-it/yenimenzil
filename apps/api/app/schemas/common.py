from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta
