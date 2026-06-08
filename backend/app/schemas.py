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
    """댓글 작성 요청 본문. parent_id가 있으면 그 댓글의 답글(대댓글)."""

    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    parent_id: Optional[int]
    content: str
    author: str
    created_at: datetime

# ───── 검색 결과 ─────
class SearchResultItem(BaseModel):
    """백터 검색 결과 한 건,한 글 단위로 묶여있고, 어디서 매칭됐는지 표시"""

    post_id: int
    post_title: str
    matched_in: list[str]  # "title", "content", "comment"
    top_score: float  # 매칭된 청크 중 가장 높은 점수(유사도)
    snippets: list[str]  # 매칭된 부분의 텍스트 미리보기(최대 3개)

#----페이지 분할-----
class PaginatedPosts(BaseModel):
    """페이지네이션된 글 목록 응답"""

    total: int  # 전체 글 수
    skip: int
    limit: int
    items: list[PostResponse]