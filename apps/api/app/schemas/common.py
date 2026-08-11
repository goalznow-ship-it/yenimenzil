from pydantic import BaseModel


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class PaginatedResponse[T](BaseModel):
    data: list[T]
    meta: PaginationMeta
