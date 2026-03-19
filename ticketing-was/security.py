import re
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 강화된 SQL 인젝션 패턴 (공백 우회 및 핵심 키워드 추가)
        danger_pattern = re.compile(
            r"(\'|--|#|;|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|AND|OR|EXEC|INFORMATION_SCHEMA)\b|<script.*?>)",
            re.IGNORECASE
        )

        # [검사 1] URL 파라미터 검사
        query_params = str(request.query_params)
        if danger_pattern.search(query_params):
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in URL"})

        # [검사 2] 본문(Body) 데이터 검사 (POST, PUT 등)
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode(errors='ignore')
            
            if danger_pattern.search(body_str):
                return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in Body"})

            # ★ 중요: 읽은 본문을 백엔드 로직에서도 쓸 수 있게 다시 채워줌 (핵심 해결책)
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        # 통과 시 다음 단계로 진행
        response = await call_next(request)
        return response
