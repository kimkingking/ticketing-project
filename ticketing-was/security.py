import re
import urllib.parse
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 💡 [핵심 1] CORS 사전 요청(OPTIONS)은 무조건 통과 (프론트엔드 에러 방지)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 💡 [핵심 2] 화이트리스트: 로그인, 회원가입 경로는 안전하게 통과 (비밀번호 특수문자 허용)
        if request.url.path.startswith("/api/member/"):
            return await call_next(request)

        # [공격 탐지 패턴] 대소문자 무시, 명확한 XSS/SQLi 차단
        danger_pattern = re.compile(
            r"(\'|--|#|;|\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND|EXEC)\b|<script.*?>)",
            re.IGNORECASE
        )

        # https://play.google.com/store/apps/details?id=com.spectrummeter&hl=ko %3c 같은 URL 인코딩 우회 방지
        query_params = urllib.parse.unquote(str(request.query_params))
        if danger_pattern.search(query_params):
            print(f"🚨 [Python WAF 차단 - URL] 경로: {request.url.path} | 탐지: {query_params}")
            return JSONResponse(status_code=403, content={"detail": "WAF: SQL Injection or XSS Attempt Detected in URL"})

        # [Body 데이터 검사] POST, PUT, PATCH 등
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = urllib.parse.unquote(body.decode(errors='ignore'))

                    if danger_pattern.search(body_str):
                        print(f"🚨 [Python WAF 차단 - Body] 경로: {request.url.path}")
                        return JSONResponse(status_code=403, content={"detail": "WAF: Malicious Payload Detected in Body"})

                    # 💡 [핵심 3] FastAPI Body 증발 방지: 읽어들인 Body를 다시 원래 자리에 끼워 넣음
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
            except Exception as e:
                print(f"⚠️ [WAF 검사 중 예외 발생 - 통과시킴] {str(e)}")
                # 검사 중 에러가 나더라도 정상 서비스는 돌아가도록 예외 처리

        # 모든 검사를 무사히 통과하면 원래 API 로직으로 이동
        return await call_next(request)