"""DB의 모든 글/댓글을 벡터 저장소(ChromaDB)에 인덱싱하는 스크립트.

실행: backend 폴더에서  ./venv/bin/python index.py
(처음엔 임베딩 모델 다운로드로 시간이 걸립니다.)
"""

from app import models, vector
from app.database import SessionLocal


def run():
    db = SessionLocal()
    try:
        posts = db.query(models.Post).all()
        comments = db.query(models.Comment).all()
        title_by_post = {p.id: p.title for p in posts}

        print(f"인덱싱 시작: 글 {len(posts)}개, 댓글 {len(comments)}개")
        vector.reset_collection()  # 기존 인덱스 비우고 새로 (모델 바뀌었으니)

        # 글: 제목 + 내용을 각각 문서로
        for p in posts:
            vector.index_post(p)
        # 댓글: 각각 문서로 (소속 글 제목도 함께 저장)
        for c in comments:
            vector.index_comment(c, post_title=title_by_post.get(c.post_id, ""))

        total = vector.get_collection().count()
        print(f"✅ 인덱싱 완료. 저장된 벡터 문서 수: {total}")
        print("   (글 1개당 제목·내용 2개 + 댓글 1개당 1개)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
