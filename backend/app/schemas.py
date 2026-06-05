from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1, max_length=100)


class PostCreate(PostBase):
    """글 작성 요청 본문."""


class PostUpdate(BaseModel):
    """글 수정 요청 본문. 보낸 필드만 수정됩니다."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1, max_length=100)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ───── 댓글 ─────
class CommentCreate(BaseModel):
    """댓글 작성 요청 본문."""

    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1, max_length=100)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    content: str
    author: str
    created_at: datetime
