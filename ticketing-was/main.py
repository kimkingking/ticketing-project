from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
import json
import time

# [설정] DB와 Redis 연결은 database.py에서 통합 관리합니다.
from database import engine, rd

# [보안] 이중 방어용 커스텀 보안 미들웨어
from security import SecurityFilterMiddleware

# [라우터]
import login  
import signin
import reservation

app = FastAPI()

# ==========================================
# [미들웨어 등록] 순서가 매우 중요합니다!
# ==========================================

# 1️⃣ 안쪽 껍질: 보안 WAF 미들웨어 (실제 비즈니스 로직 직전에 실행)
app.add_middleware(SecurityFilterMiddleware)

# 2️⃣ 바깥쪽 껍질: CORS 미들웨어 (FastAPI는 나중에 추가한 게 먼저 실행됨)
# 이렇게 해야 브라우저의 OPTIONS 요청을 CORS가 먼저 안전하게 처리해줍니다.
origins = [
    "http://www.pulseticket.ke:30007",
    "https://www.pulseticket.ke",  
    "https://pulseticket.ke",      
    "http://www.pulseticket.ke",
    "http://10.4.0.203",           
    "https://10.4.0.203",
    "http://10.4.0.201", 
    "http://10.4.0.150:30007",
    "http://10.4.0.150"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,     
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# [라우터 등록]
# ==========================================
app.include_router(login.router)
app.include_router(signin.router)
app.include_router(reservation.router, prefix="/api/reservations")

# ==========================================
# [API 엔드포인트]
# ==========================================

@app.get("/")
async def root():
    return {"message": "Welcome to the Integrated Ticketing System! 🚀 (서버 정상 작동 중)"}

@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MySQL/MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✨ 대기열 관리자 API
@app.post("/next")
def allow_next_users(count: int = 10): 
    try:
        top_users = rd.zrange("ticket_queue", 0, count - 1)
        
        if not top_users:
            return {"status": "success", "message": "현재 대기열이 텅 비어있습니다."}
        
        rd.sadd("allowed_users", *top_users)
        rd.zrem("ticket_queue", *top_users)
        
        return {
            "status": "success",
            "message": f"{len(top_users)}명의 유저가 입장 허가를 받았습니다!",
            "allowed_users": top_users
        }
    except Exception as e:
        return {"status": "error", "message": f"대기열 이동 중 오류 발생: {str(e)}"}

# ✨ 예약 내역 조회 API
@app.get("/api/reservations/{user_id}")
def get_user_reservations(user_id: str):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    res_id, user_id, seat_id, seat_num, perf_id, perf_title,
                    DATE_FORMAT(select_date, '%Y-%m-%d') as select_date,
                    TIME_FORMAT(select_time, '%H:%i:%s') as select_time,
                    place, price,
                    DATE_FORMAT(res_date, '%Y-%m-%d %H:%i:%s') as res_date
                FROM reservation
                WHERE user_id = :uid
                ORDER BY res_date DESC
            """)
            result = conn.execute(query, {"uid": user_id}).mappings().all()
            return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 조회 중 오류 발생: {str(e)}")

# ✨ 빈 좌석 조회 API
@app.get("/seats")
def get_seats():
    try:
        with engine.connect() as conn:
            query = text("SELECT seat_id, seat_num FROM seat WHERE status = 'AVAILABLE'")
            result = conn.execute(query)
            seats = [{"seat_id": row[0], "seat_num": row[1]} for row in result]
            return {"available_seats": seats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✨ 단일 유저 조회 API
@app.get("/users/{user_id}")
def get_user(user_id: str):
    try:
        with engine.connect() as conn:
            query = text("SELECT user_id, user_name, user_phone FROM user WHERE user_id = :user_id")
            result = conn.execute(query, {"user_id": user_id}).fetchone()
            if result:
                return {"user_id": result[0], "user_name": result[1], "user_phone": result[2]}
            return {"error": "User not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}