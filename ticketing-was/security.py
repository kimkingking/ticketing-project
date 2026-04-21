import re
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1️⃣ [화이트리스트] 로그인, 회원가입 경로는 보안 검사를 완전히 생략합니다.
        # 이렇게 해야 비밀번호에 어떤 특수문자가 들어가도 튕기지 않습니다.
        if request.url.path.startswith("/api/member/"):
            return await call_next(request)

        # 2️⃣ [공격 탐지 패턴] 사용자님이 주신 공격 예시를 정확히 잡아내는 정규식입니다.
        danger_pattern = re.compile(
            r"(\'|--\s|#\s|;\s|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND|EXEC)\b|<script.*?>)",
            re.IGNORECASE
        )

        # 3️⃣ https://www.wordreference.com/koen/%EA%B2%80%EC%82%AC GET 방식의 공격(URL 파라미터)을 검사합니다.
        # 예: ?id=' OR 1=1 -- 또는 ?search=<script>...
        query_params = str(request.query_params)
        if danger_pattern.search(query_params):
            print(f"🚨 [WAF 차단 - URL] 경로: {request.url.path} | 탐지: {query_params}")
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection or XSS Attempt Detected in URL"})

        # 4️⃣ [본문(Body) 검사] POST 요청 등의 본문 데이터를 검사합니다.
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode(errors='ignore')
            
            if danger_pattern.search(body_str):
                print(f"🚨 [WAF 차단 - Body] 경로: {request.url.path}")
                return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection Attempt Detected in Body"})

            # 읽은 본문을 다시 채워주어야 실제 API 로직에서 데이터를 읽을 수 있습니다.
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        return await call_next(request)