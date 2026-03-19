import re
import urllib.parse
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1️⃣ [화이트리스트] 로그인, 회원가입 경로는 통과
        if request.url.path.startswith("/api/member/"):
            return await call_next(request)

        # 2️⃣ [공격 탐지 패턴] 
        # 더 강력해진 XSS 및 SQLi 탐지용 정규식
        danger_pattern = re.compile(
            r"(\'|--|#|;|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND|EXEC)\b|<script.*?>|alert\(|onerror=)",
            re.IGNORECASE
        )

        # 3️⃣ https://play.google.com/store/apps/details?id=com.spectrummeter&hl=ko 
        # 디코딩을 수행하여 %3c 같은 우회 시도를 잡아냅니다.
        query_params = urllib.parse.unquote(str(request.query_params))
        if danger_pattern.search(query_params):
            print(f"🚨 [Python WAF 차단 - URL] 경로: {request.url.path} | 탐지: {query_params}")
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection or XSS Attempt Detected in URL"})

        # 4️⃣ [본문(Body) 검사]
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = urllib.parse.unquote(body.decode(errors='ignore'))

            if danger_pattern.search(body_str):
                print(f"🚨 [Python WAF 차단 - Body] 경로: {request.url.path}")
                return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in Body"})

            # 읽은 본문을 다시 채워줌 (FastAPI가 나중에 읽을 수 있도록)
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        return await call_next(request)
