import os
import time
import requests  # <-- 패키지 설치 필요: pip install requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

# database.py에서 DB 연결과 Redis 연결(rd) 가져오기
from database import engine, rd

# 환경변수 세팅
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

router = APIRouter()

class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int
    turnstile_token: str

def verify_turnstile_sync(token: str) -> bool:
    """비동기 대신 동기 방식으로 캡차를 검증합니다."""
    if not TURNSTILE_SECRET_KEY or not token:
        return False
    try:
        # requests를 사용하여 동기식(Sync) POST 요청을 보냅니다.
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET_KEY, "response": token},
            timeout=5.0
        )
        return response.json().get("success", False)
    except Exception as e:
        print(f"Captcha Verification Error: {e}")
        return False

@router.post("/reserve")
def reserve_ticket(req: ReservationRequest):  # async 제거!
    try:
        # --- 1단계: 대기열 확인 (동기 로직) ---
        is_allowed = rd.sismember("allowed_users", req.user_id)

        if not is_allowed:
            # 줄만 세우고 즉시 리턴
            now = time.time()
            rd.zadd("ticket_queue", {req.user_id: now})
            rank = rd.zrank("ticket_queue", req.user_id) + 1
            return {
                "status": "wait",
                "message": "아직 예매 순서가 아닙니다.",
                "waiting_number": rank
            }

        # --- 2단계: 입장 허가 유저만 '동기식 캡차 검증' ---
        is_test_mode = (DEBUG_MODE and req.turnstile_token == "JETER_TEST_TOKEN")
        
        if not is_test_mode:
            # verify_turnstile_sync를 호출하여 결과가 올 때까지 기다린 후 다음 줄로 넘어감
            if not verify_turnstile_sync(req.turnstile_token):
                raise HTTPException(status_code=403, detail="캡차 검증 실패!")

        # --- 3단계: 캡차 통과 후 MariaDB 작업 (강력한 동기 트랜잭션) ---
        with engine.connect() as conn:
            with conn.begin():
                # FOR UPDATE 락으로 좌석 선점 방지
                seat = conn.execute(
                    text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE"), 
                    {"id": req.seat_id}
                ).fetchone()

                if not seat or seat[0] != 'AVAILABLE':
                    return {"status": "fail", "message": "이미 예약된 좌석입니다."}

                # 업데이트 및 인서트
                conn.execute(text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id"), {"id": req.seat_id})
                
                conn.execute(text("""
                    INSERT INTO reservation (user_id, seat_id, perf_id, perf_title, select_date, select_time, place, price)
                    VALUES (:user_id, :seat_id, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
                """), {
                    "user_id": req.user_id, "seat_id": req.seat_id,
                    "perf_id": req.perf_id, "perf_title": req.perf_title,
                    "select_date": req.select_date, "select_time": req.select_time,
                    "place": req.place, "price": req.price
                })

        # --- 4단계: 마무리 ---
        rd.srem("allowed_users", req.user_id)
        return {"status": "success", "message": "예매 성공!"}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
