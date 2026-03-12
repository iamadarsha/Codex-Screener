from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel):
    ok: bool = True
    message: str = "success"


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_pages: int

    @classmethod
    def build(
        cls,
        items: list[Any],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse:
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
