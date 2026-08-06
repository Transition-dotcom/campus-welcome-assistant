"""
通用 Pydantic 模型。
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """通用分页响应。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """通用消息响应。"""
    message: str
