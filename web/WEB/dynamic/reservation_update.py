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
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

router = APIRouter()

# ==========================================
# [데이터 모델] 프론트엔드 JS 규격에 맞춤
# ==========================================
class PreCheckRequest(BaseModel):
    user_id: str
    perf_id: str
    select_date: str
    select_time: str
    turnstile_token: str

class ReservationRequest(BaseModel):
    user_id: str
    seat_num: str
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int

def verify_turnstile_sync(token: str) -> bool:
    """팀원의 견고한 동기식 캡차 검증 로직 유지"""
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
# [API 1] 좌석 조회 (booking.js 화면 렌더링용)
# ==========================================
@router.get("/seats")
def get_reserved_seats(perf_id: str, date: str, time: str):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT seat_num FROM seat 
                WHERE perf_id = :perf_id AND perf_date = :date AND perf_time = :time AND status = 'OCCUPIED'
            """)
            result = conn.execute(query, {"perf_id": perf_id, "date": date, "time": time}).fetchall()
            return {"status": "success", "reserved_seats": [row[0] for row in result]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# [API 2] 사전 진입 검증 (detail.js 용 - 대기열 & 캡차)
# ==========================================
@router.post("/reserve")
def reserve_precheck(req: PreCheckRequest):
    try:
        # [1단계] 대기열 확인 (팀원의 동기 로직 반영)
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

        # [2단계] 캡차 검증 (팀원의 테스트 모드 로직 반영)
        is_test_mode = (DEBUG_MODE and req.turnstile_token == "JETER_TEST_TOKEN")
        if not is_test_mode:
            if not verify_turnstile_sync(req.turnstile_token):
                raise HTTPException(status_code=403, detail="캡차 검증 실패!")

        return {"status": "success", "message": "검증 완료. 예매 페이지로 이동합니다."}

    except HTTPException as he:
        raise he
    except Exception as e:
        return {"status": "error", "message": f"검증 중 오류: {str(e)}"}

# ==========================================
# [API 3] 최종 예매 DB 저장 (booking.js 용)
# ==========================================
@router.post("")  
def confirm_reservation(req: ReservationRequest):
    try:
        with engine.begin() as conn:
            # [1단계] 중복 좌석 확인
            check_query = text("""
                SELECT seat_id FROM seat 
                WHERE perf_id = :perf_id AND perf_date = :select_date AND perf_time = :select_time AND seat_num = :seat_num
            """)
            existing_seat = conn.execute(check_query, {
                "perf_id": req.perf_id, "select_date": req.select_date,
                "select_time": req.select_time, "seat_num": req.seat_num
            }).fetchone()

            if existing_seat:
                return {"status": "fail", "message": "이미 예매가 완료된 좌석입니다."}

            # [2단계] 좌석 상태 OCCUPIED로 INSERT (동시성 방어)
            insert_seat_query = text("""
                INSERT INTO seat (seat_num, perf_id, perf_date, perf_time, status, version)
                VALUES (:seat_num, :perf_id, :select_date, :select_time, 'OCCUPIED', 1)
            """)
            try:
                conn.execute(insert_seat_query, {
                    "seat_num": req.seat_num, "perf_id": req.perf_id,
                    "select_date": req.select_date, "select_time": req.select_time
                })
            except IntegrityError:
                return {"status": "fail", "message": "간발의 차이로 다른 분이 먼저 예매했습니다."}

            seat_id_result = conn.execute(text("SELECT LAST_INSERT_ID()")).fetchone()
            real_seat_id = seat_id_result[0]

            # [3단계] 예약 장부 작성
            insert_res_query = text("""
                INSERT INTO reservation (user_id, seat_id, seat_num, perf_id, perf_title, select_date, select_time, place, price)
                VALUES (:user_id, :seat_id, :seat_num, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
            """)
            conn.execute(insert_res_query, {
                "user_id": req.user_id, "seat_id": real_seat_id, "seat_num": req.seat_num, 
                "perf_id": req.perf_id, "perf_title": req.perf_title, "select_date": req.select_date, 
                "select_time": req.select_time, "place": req.place, "price": req.price
            })

        # [4단계] 최종 예매 성공 후 대기열에서 유저 삭제 (팀원 로직 반영)
        rd.srem("allowed_users", req.user_id)
        return {"status": "success", "message": f"[{req.perf_title}] {req.seat_num} 좌석 예매 성공!"}

    except Exception as e:
        return {"status": "error", "message": f"서버 오류 발생: {str(e)}"}