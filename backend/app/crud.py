from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas


def get_posts(
    db: Session, skip: int = 0, limit: int = 20, keyword: str | None = None
) -> list[models.Post]:
    """글 목록을 최신순으로 조회. keyword가 있으면 제목/내용에서 검색."""
    stmt = select(models.Post)
    if keyword:
        # 제목 또는 내용에 keyword가 포함된 글만 (SQL: LIKE '%keyword%')
        stmt = stmt.where(
            models.Post.title.contains(keyword)
            | models.Post.content.contains(keyword)
        )
    stmt = stmt.order_by(models.Post.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_posts(db: Session) -> int:
    return db.query(models.Post).count()


def get_posts_count(db: Session, keyword: str | None = None) -> int:
    """글 총 개수. keyword가 있으면 매칭되는 것만 카운트 (페이지네이션용)."""
    stmt = select(func.count(models.Post.id))
    if keyword:
        stmt = stmt.where(
            models.Post.title.contains(keyword)
            | models.Post.content.contains(keyword)
        )
    return db.scalar(stmt) or 0


def get_post(db: Session, post_id: int) -> models.Post | None:
    return db.get(models.Post, post_id)


def create_post(db: Session, post: schemas.PostCreate) -> models.Post:
    db_post = models.Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(
    db: Session, db_post: models.Post, post: schemas.PostUpdate
) -> models.Post:
    # 보낸 필드만 반영 (부분 수정)
    for field, value in post.model_dump(exclude_unset=True).items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, db_post: models.Post) -> None:
    db.delete(db_post)
    db.commit()


# ───── 댓글 ─────
def get_comments(db: Session, post_id: int) -> list[models.Comment]:
    """특정 글의 댓글을 오래된 순으로 조회."""
    stmt = (
        select(models.Comment)
        .where(models.Comment.post_id == post_id)
        .order_by(models.Comment.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_comment(db: Session, comment_id: int) -> models.Comment | None:
    return db.get(models.Comment, comment_id)


def create_comment(
    db: Session, post_id: int, comment: schemas.CommentCreate
) -> models.Comment:
    db_comment = models.Comment(post_id=post_id, **comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, db_comment: models.Comment) -> None:
    db.delete(db_comment)
    db.commit()
