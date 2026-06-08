from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 글을 지우면 딸린 댓글도 함께 삭제됩니다.
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 어느 글의 댓글인지. posts.id 와 연결되고, 글 삭제 시 같이 삭제됩니다.
    post_id = Column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    # 어느 댓글의 답글인지. NULL이면 일반 댓글, 값이 있으면 그 댓글의 답글(대댓글).
    # 부모 댓글이 삭제되면 답글도 함께 삭제됩니다.
    parent_id = Column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    post = relationship("Post", back_populates="comments")
