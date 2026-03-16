import os
import time
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

# 팀원분의 데이터베이스 연결 도구
from database import engine, rd

# 환경변수 세팅 (보안 & 디버그)
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

router = APIRouter()
http_client = httpx.AsyncClient()

class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int
    turnstile_token: str  # 👈 캡차 검증용 토큰

async def verify_turnstile(token: str) -> bool:
    if not TURNSTILE_SECRET_KEY:
        return False
    # JMeter 테스트를 위한 하이패스권 ㅋ
    if DEBUG_MODE and token == "JETER_TEST_TOKEN":
        return True
    response = await http_client.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={"secret": TURNSTILE_SECRET_KEY, "response": token}
    )
    return response.json().get("success", False)

# 1️⃣ [POST] 예약 신청 (보안 검증 + 대기열 등록)
@router.post("/reserve")
async def reserve_ticket(req: ReservationRequest):
    try:
        # 보안 검증 (JMeter는 JETER_TEST_TOKEN을 써야 합니다! ㅋ)
        if not await verify_turnstile(req.turnstile_token):
            raise HTTPException(status_code=403, detail="매크로/봇 접근이 감지되었습니다.")

        now = time.time()
        rd.zadd("ticket_queue", {req.user_id: now})
        rank = rd.zrank("ticket_queue", req.user_id) + 1

        with engine.connect() as conn:
            with conn.begin():
                select_query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(select_query, {"id": req.seat_id}).fetchone()

                if not seat or seat[0] != 'AVAILABLE':
                    return {"status": "fail", "message": "이미 예약된 좌석입니다.", "waiting_number": rank}

                update_query = text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id")
                conn.execute(update_query, {"id": req.seat_id})

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

        return {"status": "success", "message": f"{req.seat_id}번 좌석 예약이 완료되었습니다!", "waiting_number": rank}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"예약 중 오류 발생: {str(e)}")

# 2️⃣ [GET] 좌석 조회 (422 에러 해결 버전 ㅋ)
@router.get("/seats")
def get_seats(perf_id: str = Query(...), date: str = None, time: str = None):
    try:
        with engine.connect() as conn:
            query = text("SELECT seat_id, seat_num FROM seat WHERE status = 'AVAILABLE'")
            result = conn.execute(query)
            seats = [{"seat_id": row[0], "seat_num": row[1]} for row in result]
            return {"available_seats": seats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 3️⃣ [GET] 대기 순번 확인 (보혜님의 필살기! ㅋ)
@router.get("/status")
def get_queue_status(user_id: str):
    try:
        rank = rd.zrank("ticket_queue", user_id)
        if rank is not None:
            return {"status": "success", "waiting_number": rank + 1}
        return {"status": "success", "waiting_number": 0}
    except Exception as e:
        print(f"Queue Status Error: {e}")
        return {"status": "error", "message": "대기열 확인 오류"}
