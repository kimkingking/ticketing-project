from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import redis  # Redis를 위해 추가!
import json   # 데이터 처리를 위해 추가
import time

app = FastAPI()

# 1. DB 연결 설정 (MariaDB/MySQL)
DB_URL = "mysql+pymysql://mysql:1234@mysql:3306/ticket"
engine = create_engine(DB_URL)

# 2. Redis 연결 설정 (K8s 서비스 이름인 'redis-service' 사용)
rd = redis.Redis(host='redis-service', port=6379, db=0, decode_responses=True)

# [수정됨] 팀원 ERD에 맞춘 예매 요청 데이터
class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ticketing System v17 (with Redis)!"}

# [기능 1] DB 연결 테스트용
@app.get("/db-test")
def test_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 2] Redis 연결 테스트용 (추가된 기능!)
@app.get("/redis-test")
def test_redis():
    try:
        rd.set("test_key", "Redis is Alive! 🚀")
        value = rd.get("test_key")
        return {"status": "success", "redis_result": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 3] 예약 가능한 좌석 조회
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

# [기능 4] 티켓 예약하기 (DB 저장)
@app.post("/reserve")
def reserve_ticket(req: ReservationRequest):
    try:
        with engine.connect() as conn:
            with conn.begin(): 
                update_query = text("UPDATE seat SET status = 'OCCUPIED', version = version + 1 WHERE seat_id = :seat_id AND status = 'AVAILABLE'")
                result = conn.execute(update_query, {"seat_id": req.seat_id})

                if result.rowcount == 0:
                    return {"status": "fail", "message": "이미 예매되었거나 존재하지 않는 좌석입니다."}

                insert_query = text("""
                    INSERT INTO reservation (user_id, seat_id, perf_id, perf_title, select_date, select_time, place, price)
                    VALUES (:user_id, :seat_id, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
                """)
                conn.execute(insert_query, {
                    "user_id": req.user_id, "seat_id": req.seat_id,
                    "perf_id": req.perf_id, "perf_title": req.perf_title,
                    "select_date": req.select_date, "select_time": req.select_time,
                    "place": req.place, "price": req.price
                })

                return {"status": "success", "message": f"{req.seat_id}번 좌석 예매가 완료되었습니다!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM user WHERE user_id = :user_id")
            result = conn.execute(query, {"user_id": user_id}).fetchone()
            if result:
                # 튜플 인덱스로 접근 (row[0], row[1] 등)
                return {"user_name": result[1], "user_phone": result[2]}
            return {"error": "User not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
