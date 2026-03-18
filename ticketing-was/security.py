import re
import html
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse # 에러 응답용 추가

app = FastAPI()

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        danger_pattern = re.compile(
            r"(\'|--|#|;|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|AND|OR|EXEC)\b|<script.*?>)", 
            re.IGNORECASE
        )

        # 1. URL 파라미터 검사
        query_params = str(request.query_params)
        if danger_pattern.search(query_params):
            return JSONResponse(status_code=403, content={"detail": "Security Threat Detected (URL)"})

        # 2. 본문 데이터 검사 (POST/PUT)
        if request.method in ["POST", "PUT"]:
            # 핵심: body를 읽을 때 에러가 나지 않도록 처리
            body = await request.body()
            body_str = body.decode(errors='ignore')
            if danger_pattern.search(body_str):
                # HTTPException 대신 직접 JSONResponse를 던지는 것이 미들웨어에서 더 안전합니다.
                return JSONResponse(status_code=403, content={"detail": "Security Threat Detected (Body)"})

        # 검사를 통과하면 다음 단계로 진행
        response = await call_next(request)
        return response

app.add_middleware(SecurityFilterMiddleware)

# 루트 경로 설정 (GET, POST 모두 허용)
@app.api_route("/", methods=["GET", "POST"])
async def root():
    return {"message": "Safe Ticketing System"}

# 미들웨어 내부 로직에 추가
async def dispatch(self, request, call_next):
    # 1. URL 뒤에 붙은 파라미터(query=DELETE 등) 검사
    query_params = str(request.query_params)
    if "DELETE" in query_params.upper() or "DROP" in query_params.upper():
        return JSONResponse(status_code=403, content={"detail": "Security Threat Detected!"})

    response = await call_next(request)
    return response
