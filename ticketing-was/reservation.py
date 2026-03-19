import os
import time
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import engine, rd

DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "0x4AAAAAACon_-jaaYDj9s5-")

router = APIRouter()

# [1. detail.js 용] 대기열 & 캡차 사전 검증만 수행
class PreCheckRequest(BaseModel):
    user_id: str
    perf_id: str
    select_date: str
    select_time: str
    turnstile_token: str

# [2. 최종 예매용] DB 좌석 저장까지 수행
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
    if not TURNSTILE_SECRET_KEY or not token: return False
    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET_KEY, "response": token},
            timeout=5.0
        )
        return response.json().get("success", False)
    except Exception as e:
        return False

# --- [API 1] 사전 진입 검증 (detail.js 에서 찌르는 곳) ---
@router.post("/reserve")
def reserve_precheck(req: PreCheckRequest):
    try:
        # 1. 대기열 확인
        is_allowed = rd.sismember("allowed_users", req.user_id)
        if not is_allowed:
            now = time.time()
            rd.zadd("ticket_queue", {req.user_id: now})
            rank = rd.zrank("ticket_queue", req.user_id) + 1
            return {"status": "wait", "message": "아직 예매 순서가 아닙니다.", "waiting_number": rank}

        # 2. 캡차 검증
        is_test_mode = (DEBUG_MODE and req.turnstile_token == "JETER_TEST_TOKEN")
        if not is_test_mode:
            if not verify_turnstile_sync(req.turnstile_token):
                raise HTTPException(status_code=403, detail="캡차 검증이 필요합니다.")

        # 성공 시 DB 작업 없이 통과 (좌석 선택 페이지로 넘어가기 위함)
        return {"status": "success", "message": "검증 완료. 좌석 선택으로 이동합니다."}

    except HTTPException as he:
        raise he
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- [API 2] 최종 예매 진행 (좌석 선택 페이지에서 찌르는 곳) ---
@router.post("/confirm")
def confirm_reservation(req: ReservationRequest):
    try:
        with engine.connect() as conn:
            with conn.begin():
                # 좌석 락 및 상태 확인 (팀원분 로직 그대로 유지)
                query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(query, {"id": req.seat_id}).fetchone()

                if not seat or seat[0] != 'AVAILABLE':
                    return {"status": "fail", "message": "이미 예약이 완료된 좌석입니다."}

                conn.execute(
                    text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id"),
                    {"id": req.seat_id}
                )

                conn.execute(text("""
                    INSERT INTO reservation (user_id, seat_id, perf_id, perf_title, select_date, select_time, place, price)
                    VALUES (:user_id, :seat_id, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
                """), {
                    "user_id": req.user_id, "seat_id": req.seat_id,
                    "perf_id": req.perf_id, "perf_title": req.perf_title,
                    "select_date": req.select_date, "select_time": req.select_time,
                    "place": req.place, "price": req.price
                })

        rd.srem("allowed_users", req.user_id)
        return {"status": "success", "message": "🎉 예매 성공! 즐거운 관람 되세요!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")