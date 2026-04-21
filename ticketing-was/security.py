import re
import urllib.parse
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 💡 1. CORS 사전 요청 무조건 통과 (프론트엔드 에러 원천 차단)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 💡 2. 화이트리스트: 로그인/회원가입 경로 예외 처리
        if request.url.path.startswith("/api/member/"):
            return await call_next(request)

        # 💡 3. 공격 탐지 패턴 (URL 파라미터만 안전하게 검사)
        danger_pattern = re.compile(
            r"(\'|--|#|;|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND|EXEC)\b|<script.*?>)",
            re.IGNORECASE
        )

        # URL 인코딩(%3c 등)을 풀어서 꼼꼼히 검사
        query_params = urllib.parse.unquote(str(request.query_params))
        path_str = urllib.parse.unquote(str(request.url.path))

        if danger_pattern.search(query_params) or danger_pattern.search(path_str):
            print(f"🚨 [Python WAF 차단] 경로: {request.url.path}")
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection or XSS Attempt Detected"})

        # 💡 4. Body 데이터는 절대 건드리지 않고 넘깁니다! (이래야 정상 API가 먹통이 안 됩니다)
        return await call_next(request)