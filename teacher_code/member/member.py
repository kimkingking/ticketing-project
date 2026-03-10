from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.post("/register")
def register(
    u_id: str = Form(...), 
    u_pass: str = Form(...), 
    u_name: str = Form(...), 
    u_nick: str = Form(...),
    u_age: int = Form(...), 
    u_email: str = Form(...),
    db: Session = Depends(get_db)
):
    try: 
        check_sql = text("SELECT u_id FROM member WHERE u_id = :u_id")
        existing = db.execute(check_sql, {"u_id": u_id}).fetchone()
        
        if existing: 
            return {"status": "fail", "message": "이미 존재하는 아이디입니다."}
        
        insert_sql = text("""
            INSERT INTO member (u_id, u_pass, u_name, nickname, age, email, reg_date) 
            VALUES (:u_id, :u_pass, :u_name, :u_nick, :u_age, :u_email, NOW())
        """)
        db.execute(insert_sql, {"u_id": u_id, "u_pass": u_pass, "u_name": u_name, "u_nick": u_nick, "u_age": u_age, "u_email": u_email})
        db.commit()
        return {"status": "success", "message": "가입되었습니다."}
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "가입에 실패하였습니다."}

@router.post("/login")
def login(
    u_id: str = Form(...), 
    u_pass: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        login_sql = text("""
            SELECT u_id, u_name 
            FROM member 
            WHERE u_id = :u_id AND u_pass = :u_pass
        """)
        user = db.execute(login_sql, {"u_id": u_id, "u_pass": u_pass}).fetchone()
        
        if not user: 
            return {"status": "fail", "message": "아이디 또는 비밀번호가 틀립니다."}
        
        return {
            "status": "success", 
            "message": f"{user[1]}님 환영합니다!", 
            "user": user[0], 
            "nickname": user[1]
        }
    except Exception as e:
        print(e.args)
        return {"status": "fail", "message": "로그인 중 오류가 발생했습니다."}