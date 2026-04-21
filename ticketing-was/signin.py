import re
from fastapi import APIRouter, Form
from sqlalchemy import text
from database import engine # 💡 통합된 DB 엔진 사용

router = APIRouter(prefix="/api/member")

def format_phone_number(phone: str) -> str:
    clean_number = re.sub(r'[^0-9]', '', phone)
    if len(clean_number) == 11:
        return f"{clean_number[:3]}-{clean_number[3:7]}-{clean_number[7:]}"
    elif len(clean_number) == 10:
        return f"{clean_number[:3]}-{clean_number[3:6]}-{clean_number[6:]}"
    return phone

@router.post("/register")
def register(  # 💡 동기 DB 통신을 위해 async 제거
    user_id: str = Form(...),
    password: str = Form(...),
    user_name: str = Form(...),
    phone: str = Form(...),
    addr: str = Form(...),
    email: str = Form(...)
):
    try:
        formatted_phone = format_phone_number(phone)
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
                "password": password, 
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