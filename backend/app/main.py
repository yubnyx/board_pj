from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import comments, posts, search

# 테이블이 없으면 생성 (init.sql로 이미 만들었다면 그냥 통과,있어도 없어도 상관없음)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="게시판 API")

# 프론트엔드(개발 서버)에서 호출할 수 있도록 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(search.router)

@app.get("/health") #서버 상태확인용 엔드포인트
def health():
    return {"status": "ok"}
