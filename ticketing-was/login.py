from fastapi import APIRouter, Form, Response
from sqlalchemy import create_engine, text

# 1. 라우터 설정 (main.py에서 /api/member로 연결됨)
router = APIRouter(prefix="/api/member")

# 2. DB 연결 설정
DB_URL = "mysql+pymysql://mysql:1234@mysql:3306/ticket"
engine = create_engine(DB_URL)

@router.post("/login")
async def login(
    response: Response,
    # 프론트엔드의 FormData('u_id', 'u_pass')와 정확히 1:1로 매칭됩니다.
    u_id: str = Form(...),
    u_pass: str = Form(...)
):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT user_id, user_name, email
                FROM user
                WHERE user_id = :u_id AND password = :u_pass
            """)

            # 받아온 변수 u_id, u_pass를 쿼리에 바인딩합니다.
            result = conn.execute(query, {"u_id": u_id, "u_pass": u_pass}).fetchone()

            if result:
                # 결과값 언패킹
                user_id, user_name, email = result

                return {
                    "status": "success",
                    "message": f"{user_name}님, 환영합니다!",
                    "nickname": user_name,
                    "email": email
                }
            else:
                return {
                    "status": "fail",
                    "message": "아이디 또는 비밀번호가 일치하지 않습니다."
                }

    except Exception as e:
        return {"status": "error", "message": f"서버 에러가 발생했습니다: {str(e)}"}