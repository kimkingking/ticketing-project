import re
import bcrypt  # 💡 암호화 라이브러리 추가
from fastapi import APIRouter, Form
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/api/member")

def format_phone_number(phone: str) -> str:
    clean_number = re.sub(r'[^0-9]', '', phone)
    if len(clean_number) == 11:
        return f"{clean_number[:3]}-{clean_number[3:7]}-{clean_number[7:]}"
    elif len(clean_number) == 10:
        return f"{clean_number[:3]}-{clean_number[3:6]}-{clean_number[6:]}"
    return phone

@router.post("/register")
def register(
    user_id: str = Form(...),
    password: str = Form(...),
    user_name: str = Form(...),
    phone: str = Form(...),
    addr: str = Form(...),
    email: str = Form(...)
):
    try:
        formatted_phone = format_phone_number(phone)
        
        # 💡 비밀번호 해싱 처리 (평문 비밀번호를 암호화)
        # 1. 비밀번호를 바이트 문자열로 인코딩
        # 2. 임의의 Salt를 생성하여 해싱
        # 3. DB 저장을 위해 다시 일반 문자열(utf-8)로 디코딩
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with engine.connect() as conn:
            check_sql = text("SELECT user_id FROM user WHERE user_id = :user_id")
            existing = conn.execute(check_sql, {"user_id": user_id}).fetchone()

            if existing:
                return {"status": "fail", "message": "이미 존재하는 아이디입니다."}

            insert_sql = text("""
                INSERT INTO user (user_id, password, user_name, phone, addr, email) 
                VALUES (:user_id, :password, :user_name, :phone, :addr, :email)
            """)
            
            conn.execute(insert_sql, {
                "user_id": user_id, 
                "password": hashed_password,  # 💡 평문 password 대신 암호화된 변수 삽입
                "user_name": user_name, 
                "phone": formatted_phone,
                "addr": addr, 
                "email": email
            })
            conn.commit() 
            return {"status": "success", "message": "가입되었습니다"}

    except Exception as e:
        print(f"DB Error: {e}") 
        return {"status": "fail", "message": "가입에 실패하였습니다"}