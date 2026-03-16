from fastapi import FastAPI
from sqlalchemy import text
# 🌟 reservation.py에서 라우터(매뉴얼)와 DB 도구(engine, rd)를 한꺼번에 다 가져옵니다!
from reservation import router as reservation_router, engine, rd

app = FastAPI()

# 가져온 라우터를 조립합니다.
app.include_router(reservation_router)

# [기본] 루트 페이지
@app.get("/")
def read_root():
    return {"message": "Welcome to the Ticketing System v22 (2 Files Setup)!"}

# [기능 1] DB 연결 테스트용
@app.get("/db-test")
def test_db():
    try:
        # reservation.py에서 가져온 engine을 사용!
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# [기능 2] Redis 연결 테스트용
@app.get("/redis-test")
def test_redis():
    try:
        # reservation.py에서 가져온 rd를 사용!
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
