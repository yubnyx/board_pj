from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Query

from .. import schemas, vector

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=list[schemas.SearchResultItem])
def vector_search(
    q: str = Query(..., description="검색어"),
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="이 점수 이상만"),
    limit: int = Query(10, ge=1, le=50, description="최대 결과 수"),
):
    """의미(벡터) 검색. 글 단위로 묶고 어디서 매칭됐는지 표시."""
    # 1) 넉넉히 가져옴 (필터링 후 부족할 수 있으니 limit * 3)
    raw = vector.search(q, k=limit * 3)

    # 2) 점수 임계값 필터링
    raw = [r for r in raw if r["score"] >= min_score]

    # 3) post_id 별로 묶기 — 같은 글이 제목/내용/댓글 여러 군데서 매칭될 수 있음
    grouped: dict[int, dict] = defaultdict(lambda: {
        "post_id": None,
        "post_title": "",
        "matched_in": [],
        "top_score": 0.0,
        "snippets": [],
    })

    for r in raw:
        g = grouped[r["post_id"]]
        g["post_id"] = r["post_id"]
        g["post_title"] = r["post_title"]
        if r["type"] not in g["matched_in"]:
            g["matched_in"].append(r["type"])
        if r["score"] > g["top_score"]:
            g["top_score"] = r["score"]
        if len(g["snippets"]) < 3:
            g["snippets"].append(r["snippet"][:80])  # 80자 미리보기

    # 4) 글들을 최고 점수순 정렬, 상위 limit개
    items = sorted(grouped.values(), key=lambda x: x["top_score"], reverse=True)
    return items[:limit]