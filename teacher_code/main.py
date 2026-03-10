from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from member import member
from board import board

app = FastAPI()

# CORS 설정 (개발 시 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 연결
app.include_router(member.router, prefix="/api/member")
app.include_router(board.router, prefix="/api/board")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)