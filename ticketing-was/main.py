from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import redis
import json
import time

app = FastAPI()

# 1. DB 연결 설정 (한글 지원 charset 포함)
DB_URL = "mysql+pymysql://was_user:1234@mysql:3306/ticket?charset=utf8mb4"
engine = create_engine(DB_URL)

# 2. Redis 연결 설정
rd = redis.Redis(host='redis-service', port=6379, db=0, decode_responses=True)

# 3. 데이터 모델 정의
class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int

# [기본] 루트 페이지
@app.get("/")
def read_root():
    return {"message": "Welcome to the Ticketing System v22 (Full Features + Pessimistic Lock)!"}

# [기능 1] DB 연결 테스트용
@app.get("/db-test")
def test_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 2] Redis 연결 테스트용
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
            # 상태가 AVAILABLE인 좌석만 조회
            query = text("SELECT seat_id, seat_num FROM seat WHERE status = 'AVAILABLE'")
            result = conn.execute(query)
            seats = [{"seat_id": row[0], "seat_num": row[1]} for row in result]
            return {"available_seats": seats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 4] 티켓 예약하기 (Redis 대기열 + DB 비관적 락 적용)
@app.post("/reserve")
def reserve_ticket(req: ReservationRequest):
    try:
        # --- Redis 대기열 로직 ---
        now = time.time()
        rd.zadd("ticket_queue", {req.user_id: now})
        rank = rd.zrank("ticket_queue", req.user_id) + 1

        with engine.connect() as conn:
            # 트랜잭션 시작 (비관적 락의 필수 조건)
            with conn.begin():
                # 1. 비관적 락: 해당 좌석 로우를 점유하여 동시 접근 차단
                select_query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(select_query, {"id": req.seat_id}).fetchone()

                # 2. 좌석 상태 확인
                if not seat or seat[0] != 'AVAILABLE':
                    return {
                        "status": "fail",
                        "message": "이미 예매 중이거나 매진된 좌석입니다.",
                        "waiting_number": rank
                    }

                # 3. 좌석 상태 업데이트 (선점 상태 PENDING으로 변경)
                update_query = text("UPDATE seat SET status = 'PENDING' WHERE seat_id = :id")
                conn.execute(update_query, {"id": req.seat_id})

                # 4. 예약 내역 저장
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

        return {
            "status": "success",
            "message": f"{req.seat_id}번 좌석이 선점되었습니다. 결제를 진행해주세요.",
            "waiting_number": rank,
            "info": f"귀하는 {rank}번째 대기 순서입니다."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 5] 특정 유저 정보 조회
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
