import bcrypt  # 💡 암호화 라이브러리 추가
from fastapi import APIRouter, Form, Response
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/api/member")

@router.post("/login")
def login(
    response: Response,
    u_id: str = Form(...),
    u_pass: str = Form(...)
):
    try:
        with engine.connect() as conn:
            # 💡 1. 쿼리 수정: password 파라미터 조건 제거, SELECT 항목에 password 추가
            # 아이디(u_id)만으로 해당 유저의 모든 정보를 가져옵니다.
            query = text("""
                SELECT user_id, user_name, email, password
                FROM user
                WHERE user_id = :u_id
            """)
            result = conn.execute(query, {"u_id": u_id}).fetchone()

            # 💡 2. 유저가 존재할 경우 파이썬 단에서 비밀번호 검증
            if result:
                user_id, user_name, email, db_password = result
                
                # 사용자가 입력한 평문(u_pass)과 DB에 저장된 해시값(db_password)을 비교
                if bcrypt.checkpw(u_pass.encode('utf-8'), db_password.encode('utf-8')):
                    return {
                        "status": "success",
                        "message": f"{user_name}님, 환영합니다!",
                        "nickname": user_name,
                        "email": email
                    }
                else:
                    # 비밀번호가 틀린 경우
                    return {
                        "status": "fail",
                        "message": "아이디 또는 비밀번호가 일치하지 않습니다."
                    }
            else:
                # DB에 해당 아이디가 없는 경우
                return {
                    "status": "fail",
                    "message": "아이디 또는 비밀번호가 일치하지 않습니다."
                }

    except Exception as e:
        return {"status": "error", "message": f"서버 에러가 발생했습니다: {str(e)}"}