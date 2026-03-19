import re
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 💡 '--' 뒤에 공백이 올 때만 잡도록 수정 (--\s) -> 폼 데이터 경계선 통과!
        # OR와 AND를 제외하여 더 유연하게 만든 버전
        danger_pattern = re.compile(
            # 💡 '-- ', '# ', '; ' 처럼 뒤에 공백이 붙는 공격 패턴과 핵심 SQL 명령어만 차단
            r"(--\s|#\s|;\s|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|INFORMATION_SCHEMA)\b|<script.*?>)",
            re.IGNORECASE
        )

        query_params = str(request.query_params)
        if danger_pattern.search(query_params):
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in URL"})

        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode(errors='ignore')
            
            if danger_pattern.search(body_str):
                return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in Body"})

            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        return await call_next(request)