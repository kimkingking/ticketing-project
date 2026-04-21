from fastapi import APIRouter, Form, Response
from sqlalchemy import text
from database import engine # 💡 통합된 DB 엔진 사용

router = APIRouter(prefix="/api/member")

@router.post("/login")
def login(  # 💡 동기 DB 통신을 위해 async 제거
    response: Response,
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
            result = conn.execute(query, {"u_id": u_id, "u_pass": u_pass}).fetchone()

            if result:
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