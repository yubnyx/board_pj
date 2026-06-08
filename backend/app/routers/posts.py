from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas, vector
from ..database import get_db

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=schemas.PaginatedPosts)
def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="제목/내용 검색어"),
    db: Session = Depends(get_db),
):

    """글 목록 조회 (최신순). keyword가 있으면 제목/내용에서 검색."""
    items = crud.get_posts(db,skip=skip,limit=limit,keyword=keyword)
    total = crud.get_posts_count(db, keyword=keyword)

    return schemas.PaginatedPosts(
        total=total,
        skip=skip,
        limit=limit,
        items=items
    )


@router.get("/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """글 상세 조회."""
    post = crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="글을 찾을 수 없습니다.")
    return post


@router.post("", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """글 작성."""
    new_post = crud.create_post(db, post)
    vector.index_post(new_post)  # 벡터 DB에 색인
    return new_post


@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(post_id: int, post: schemas.PostUpdate, db: Session = Depends(get_db)):
    """글 수정."""
    db_post = crud.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="글을 찾을 수 없습니다.")
    updated_post = crud.update_post(db, db_post, post)
    vector.index_post(updated_post)  # 벡터 DB에 색인
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """글 삭제."""
    db_post = crud.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="글을 찾을 수 없습니다.")
    crud.delete_post(db, db_post)
    vector.delete_post(post_id)  # 벡터 DB에서 삭제