import os
import time
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from database import engine, rd

# [설정] 환경변수
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
# 실 서비스 시에는 환경변수에서 가져오고, 테스트 시에는 하드코딩
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "0x4AAAAAACon_-jaaYDj9s5-")

router = APIRouter()

# ==========================================
# [데이터 모델] 프론트엔드와 규격 통일
# ==========================================
class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int        # seat_id 기준 (지수 님의 UI 규격)
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int
    turnstile_token: str # 캡차 토큰 필수

def verify_turnstile_sync(token: str) -> bool:
    """동기식 캡차 검증 로직"""
    if not TURNSTILE_SECRET_KEY or not token: 
        return False
    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET_KEY, "response": token},
            timeout=5.0
        )
        return response.json().get("success", False)
    except Exception as e:
        print(f"Captcha Verification Error: {e}")
        return False

# ==========================================
# [통합 API] 대기열 + 캡차 + 예약
# ==========================================
@router.post("/reserve")
def reserve_ticket(req: ReservationRequest):
    try:
        # --- [1단계] 대기열 확인 (allowed_users에 없으면 대기열 진입) ---
        # 테스트 편의를 위해 대기열 로직을 잠시 주석 처리하거나 활용하세요.
        is_allowed = rd.sismember("allowed_users", req.user_id)
        if not is_allowed:
            now = time.time()
            rd.zadd("ticket_queue", {req.user_id: now})
            rank = rd.zrank("ticket_queue", req.user_id) + 1
            return {
                "status": "wait", 
                "message": "아직 예매 순서가 아닙니다.", 
                "waiting_number": rank
            }

        # --- [2단계] 캡차 검증 (403 에러 유도 핵심 지점) ---
        is_test_mode = (DEBUG_MODE and req.turnstile_token == "JETER_TEST_TOKEN")
        if not is_test_mode:
            if not verify_turnstile_sync(req.turnstile_token):
                # 토큰이 비었거나 틀리면 403을 뱉어 프론트에서 팝업을 띄우게 함
                raise HTTPException(status_code=403, detail="캡차 검증이 필요합니다.")

        # --- [3단계] 최종 예매 DB 저장 (MariaDB 트랜잭션) ---
        with engine.connect() as conn:
            with conn.begin():
                # 1. 좌석 상태 확인 및 락 (FOR UPDATE)
                query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(query, {"id": req.seat_id}).fetchone()

                if not seat or seat[0] != 'AVAILABLE':
                    return {"status": "fail", "message": "이미 예약이 완료된 좌석입니다."}

                # 2. 좌석 상태 변경
                conn.execute(
                    text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id"),
                    {"id": req.seat_id}
                )

                # 3. 예약 장부 기록
                conn.execute(text("""
                    INSERT INTO reservation (user_id, seat_id, perf_id, perf_title, select_date, select_time, place, price)
                    VALUES (:user_id, :seat_id, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
                """), {
                    "user_id": req.user_id, "seat_id": req.seat_id,
                    "perf_id": req.perf_id, "perf_title": req.perf_title,
                    "select_date": req.select_date, "select_time": req.select_time,
                    "place": req.place, "price": req.price
                })

        # --- [4단계] 성공 후 대기열에서 유저 제거 ---
        rd.srem("allowed_users", req.user_id)
        return {"status": "success", "message": "🎉 예매 성공! 즐거운 관람 되세요!"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")