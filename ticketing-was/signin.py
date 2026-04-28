import re
from fastapi import APIRouter, Form
from sqlalchemy import create_engine, text

# 1. 라우터 설정
router = APIRouter(prefix="/api/member")

# 2. DB 연결 설정 (한글 깨짐 방지를 위해 ?charset=utf8mb4 추가)
DB_URL = "mysql+pymysql://mysql:1234@mysql:3306/ticket?charset=utf8mb4"
engine = create_engine(DB_URL)

# 전화번호에 하이픈(-)을 자동으로 추가해주는 함수
def format_phone_number(phone: str) -> str:
    # 혹시 모를 기호 제거 후 숫자만 추출
    clean_number = re.sub(r'[^0-9]', '', phone)
    
    # 11자리 휴대폰 번호 (예: 01012345678 -> 010-1234-5678)
    if len(clean_number) == 11:
        return f"{clean_number[:3]}-{clean_number[3:7]}-{clean_number[7:]}"
    # 10자리 번호 (예: 0111234567 -> 011-123-4567)
    elif len(clean_number) == 10:
        return f"{clean_number[:3]}-{clean_number[3:6]}-{clean_number[6:]}"
    
    # 그 외의 경우는 들어온 그대로 반환
    return phone

@router.post("/register")
async def register(
    user_id: str = Form(...),
    password: str = Form(...),
    user_name: str = Form(...),
    phone: str = Form(...),
    addr: str = Form(...),
    email: str = Form(...)
):
    try:
        # DB 삽입 전 전화번호 포맷팅 실행
        formatted_phone = format_phone_number(phone)

        with engine.connect() as conn:
            
            # 1. 아이디 중복 확인
            check_sql = text("SELECT user_id FROM user WHERE user_id = :user_id")
            existing = conn.execute(check_sql, {"user_id": user_id}).fetchone()

            if existing:
                return {"status": "fail", "message": "이미 존재하는 아이디입니다."}

            # 2. 회원 데이터 삽입 (포맷팅된 전화번호 적용)
            insert_sql = text("""
                INSERT INTO user (user_id, password, user_name, phone, addr, email) 
                VALUES (:user_id, :password, :user_name, :phone, :addr, :email)
            """)
            
            conn.execute(insert_sql, {
                "user_id": user_id, 
                "password": password, 
                "user_name": user_name, 
                "phone": formatted_phone,  # 가공된 전화번호 변수 사용
                "addr": addr, 
                "email": email
            })
            
            conn.commit() 
            return {"status": "success", "message": "가입되었습니다"}

    except Exception as e:
        print(f"DB Error: {e}") 
        return {"status": "fail", "message": "가입에 실패하였습니다"}
