"""벡터 검색 공용 모듈.

- 임베딩: OpenRouter API로 Qwen3-Embedding-4B 호출 (문장 → 벡터)
- 저장/검색: ChromaDB (로컬, 무료)
- 핵심: 제목/내용/댓글을 각각 별도 문서로 저장하고 type 꼬리표를 붙여,
  검색 결과가 어디서 나왔는지 구분할 수 있게 함
"""

import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # backend/.env 의 OPENROUTER_API_KEY 로드

# OpenRouter에서 쓸 임베딩 모델
MODEL_NAME = "qwen/qwen3-embedding-4b"

# ChromaDB 저장 위치 (backend/chroma_db 폴더에 영구 저장)
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "board"

_client = None
_collection = None


def get_client() -> OpenAI:
    """OpenRouter용 OpenAI 클라이언트를 한 번만 만들어 재사용."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return _client


def get_collection():
    """ChromaDB 컬렉션을 한 번만 열어 재사용."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def reset_collection():
    """기존 컬렉션을 비우고 새로 만듦 (모델/차원 바뀔 때 사용)."""
    global _collection
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    return _collection


def embed(texts: list[str]) -> list[list[float]]:
    """여러 문장을 한 번에 벡터로 변환 (OpenRouter API 호출)."""
    res = get_client().embeddings.create(
        model=MODEL_NAME,
        input=texts,
        encoding_format="float",
    )
    return [d.embedding for d in res.data]


# ── 문서 id 규칙 (type별로 구분) ──
def _post_title_id(post_id: int) -> str:
    return f"title-{post_id}"


def _post_content_id(post_id: int) -> str:
    return f"content-{post_id}"


def _comment_id(comment_id: int) -> str:
    return f"comment-{comment_id}"


def index_post(post) -> None:
    """글 하나의 '제목'과 '내용'을 각각 별도 문서로 인덱싱."""
    col = get_collection()
    ids = [_post_title_id(post.id), _post_content_id(post.id)]
    docs = [post.title, post.content]
    metas = [
        {"type": "title", "post_id": post.id, "post_title": post.title},
        {"type": "content", "post_id": post.id, "post_title": post.title},
    ]
    col.upsert(ids=ids, documents=docs, embeddings=embed(docs), metadatas=metas)


def index_comment(comment, post_title: str = "") -> None:
    """댓글 하나를 별도 문서로 인덱싱."""
    col = get_collection()
    col.upsert(
        ids=[_comment_id(comment.id)],
        documents=[comment.content],
        embeddings=embed([comment.content]),
        metadatas=[
            {
                "type": "comment",
                "post_id": comment.post_id,
                "comment_id": comment.id,
                "post_title": post_title,
            }
        ],
    )


def delete_post(post_id: int) -> None:
    """글 삭제 시 그 글의 제목·내용 + 모든 댓글 벡터를 한 번에 제거.
    각 문서 metadata의 post_id로 매칭해서 cascade 삭제."""
    col = get_collection()
    col.delete(where={"post_id": post_id})


def delete_comment(comment_id: int) -> None:
    get_collection().delete(ids=[_comment_id(comment_id)])


def search(query: str, k: int = 10) -> list[dict]:
    """검색어와 의미가 가까운 청크 top-k 반환. 각 결과에 type(제목/내용/댓글) 포함."""
    col = get_collection()
    res = col.query(query_embeddings=embed([query]), n_results=k)

    results = []
    # chroma는 결과를 리스트의 리스트로 줌 (query가 여러 개일 수 있어서). 우린 [0]만.
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append(
            {
                "type": meta["type"],            # title / content / comment
                "post_id": meta["post_id"],
                "post_title": meta.get("post_title", ""),
                "comment_id": meta.get("comment_id"),
                "snippet": doc,                  # 실제 매칭된 텍스트
                "score": round(1 - dist, 4),     # 코사인 유사도 (1에 가까울수록 비슷)
            }
        )
    return results
