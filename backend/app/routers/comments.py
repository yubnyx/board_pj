from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas, vector
from ..database import get_db

router = APIRouter(prefix="/api", tags=["comments"])


@router.get(
    "/posts/{post_id}/comments", response_model=list[schemas.CommentResponse]
)
def list_comments(post_id: int, db: Session = Depends(get_db)):
    """특정 글의 댓글 목록 (오래된 순)."""
    post = crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="글을 찾을 수 없습니다.")
    return crud.get_comments(db, post_id)


@router.post(
    "/posts/{post_id}/comments",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
):
    """특정 글에 댓글 작성. parent_id가 있으면 답글(대댓글)."""
    post = crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="글을 찾을 수 없습니다.")

    # 답글이면 부모 댓글을 검증
    if comment.parent_id is not None:
        parent = crud.get_comment(db, comment.parent_id)
        if parent is None or parent.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="답글을 달 부모 댓글을 찾을 수 없습니다.",
            )
        # 1단계만 허용: 답글에는 답글을 달 수 없음
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="답글에는 답글을 달 수 없습니다.",
            )

    new_comment = crud.create_comment(db, post_id, comment)
    vector.index_comment(new_comment, post.title)  # 벡터 DB에 색인
    return new_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    """댓글 삭제."""
    db_comment = crud.get_comment(db, comment_id)
    if db_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="댓글을 찾을 수 없습니다.")
    crud.delete_comment(db, db_comment)
    vector.delete_comment(comment_id)  # 벡터 DB에서 삭제
