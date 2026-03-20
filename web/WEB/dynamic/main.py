from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import redis
import json
import time
import login  
import signin
import reservation

app = FastAPI()

DB_URL = "mysql+pymysql://root:1234@mysql:3306/ticket"
engine = create_engine(DB_URL)

rd = redis.Redis(host='redis-service', port=6379, db=0, decode_responses=True)

# 🚨 와일드카드(*) 대신 프론트엔드 도메인만 적어줍니다.
origins = [
    "http://www.pulseticket.ke:30007",
    "https://www.pulseticket.ke",  # ✅ 필수 추가!
    "https://pulseticket.ke",      # ✅ 필수 추가!
    "http://10.4.0.203",           # (현재 접속 중인 IP도 혹시 몰라 추가)
    "https://10.4.0.203",
    "http://10.4.0.201", 
    "http://10.4.0.150:30007",
    "http://10.4.0.150"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,      # 쿠키 허용 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)
app.include_router(signin.router)
app.include_router(reservation.router, prefix="/api/reservations")

@app.get("/")
async def root():
    return {"message": "티켓팅 API 서버가 작동 중입니다."}

@app.get("/db-test")
async def db_test():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MySQL/MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✨ [NEW] 잃어버렸던 대기열 관리자(매니저) API 복구!
@app.post("/next")
def allow_next_users(count: int = 10): 
    try:
        # 가장 먼저 와서 줄을 선 사람부터 정해진 인원수(count)만큼 호명
        top_users = rd.zrange("ticket_queue", 0, count - 1)
        
        if not top_users:
            return {"status": "success", "message": "현재 대기열이 텅 비어있습니다."}
        
        # 호명된 사람들을 입장 허가 명단(allowed_users)으로 이동시키고 대기열에서 삭제
        rd.sadd("allowed_users", *top_users)
        rd.zrem("ticket_queue", *top_users)
        
        return {
            "status": "success",
            "message": f"{len(top_users)}명의 유저가 입장 허가를 받았습니다!",
            "allowed_users": top_users
        }
    except Exception as e:
        return {"status": "error", "message": f"대기열 이동 중 오류 발생: {str(e)}"}

@app.get("/api/reservations/{user_id}")
def get_user_reservations(user_id: str):
    try:
        with engine.connect() as conn:
            # 파이썬에서 JSON으로 쉽게 변환되도록 날짜와 시간 포맷을 지정하여 SELECT
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

            # 조회된 데이터를 딕셔너리 리스트로 변환하여 반환
            return [dict(row) for row in result]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 조회 중 오류 발생: {str(e)}")