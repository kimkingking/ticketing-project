import os
import time
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import engine, rd

# [설정] 환경변수 및 캡차 키
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "0x4AAAAAACon_-jaaYDj9s5-")

router = APIRouter()

# ==========================================
# [데이터 모델]
# ==========================================
# [1. detail.js 용] 대기열 확인용 (422 방지를 위해 token 기본값 설정)
class PreCheckRequest(BaseModel):
    user_id: str
    perf_id: str
    select_date: str
    select_time: str
    turnstile_token: str = "" # 프론트에서 안 보내도 에러 안 나게 처리

# [2. 최종 예매용] DB 좌석 저장 및 캡차 검증용
class ReservationRequest(BaseModel):
    user_id: str
    seat_num: str       # 💡 프론트에서 넘어오는 "S1" 형태 그대로 사용
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int
    turnstile_token: str = "" # 에러 방지용 기본값 추가

# ==========================================
# [보조 함수] 캡차 검증
# ==========================================
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

# ==========================================
# [API 1] 사전 진입 검증 (상세페이지 - 대기열만 체크)
# ==========================================
@router.post("/reserve")
def reserve_precheck(req: PreCheckRequest):
    try:
        # 1. 대기열 확인
        is_allowed = rd.sismember("allowed_users", req.user_id)
        if not is_allowed:
            now = time.time()
            rd.zadd("ticket_queue", {req.user_id: now}, nx=True)

            # 내 순위 계산
            rank = rd.zrank("ticket_queue", req.user_id) + 1
            return {"status": "wait", "message": "아직 예매 순서가 아닙니다.", "waiting_number": rank}

        # 대기열 통과 시 무조건 성공 처리
        return {"status": "success", "message": "검증 완료. 좌석 선택으로 이동합니다."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# [API 2] 최종 예매 진행 (예매 페이지 - 캡차 검증 후 DB 저장)
# ==========================================
@router.post("/confirm")
def confirm_reservation(req: ReservationRequest):
    try:
        # 1. 캡차 검증 (테스트 모드일 땐 패스)
        is_test_mode = (DEBUG_MODE and req.turnstile_token in ["", "JETER_TEST_TOKEN"])
        if not is_test_mode:
            if not verify_turnstile_sync(req.turnstile_token):
                raise HTTPException(status_code=403, detail="캡차 검증이 실패했습니다. 다시 인증해주세요.")

        with engine.connect() as conn:
            with conn.begin():
                # 2. 좌석 조회 (비관적 락으로 동시성 제어!)
                query = text("""
                    SELECT seat_id, status FROM seat
                    WHERE perf_id = :perf_id
                      AND perf_date = :date
                      AND perf_time = :time
                      AND seat_num = :seat_num
                    FOR UPDATE
                """)
                seat = conn.execute(query, {
                    "perf_id": req.perf_id, "date": req.select_date,
                    "time": req.select_time, "seat_num": req.seat_num
                }).fetchone()

                real_seat_id = None

                # 3-1. DB에 해당 좌석이 이미 만들어져 있을 때
                if seat:
                    if seat[1] != 'AVAILABLE':
                        return {"status": "fail", "message": "이미 예약이 완료된 좌석입니다."}

                    real_seat_id = seat[0]
                    conn.execute(
                        text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id"),
                        {"id": real_seat_id}
                    )
                # 3-2. DB에 좌석 데이터가 아예 없을 때 (지수님의 천재적인 로직!)
                else:
                    result = conn.execute(text("""
                        INSERT INTO seat (seat_num, perf_id, perf_date, perf_time, status, version)
                        VALUES (:seat_num, :perf_id, :date, :time, 'OCCUPIED', 1)
                    """), {
                        "seat_num": req.seat_num, "perf_id": req.perf_id,
                        "date": req.select_date, "time": req.select_time
                    })
                    real_seat_id = result.lastrowid # 방금 만들어진 진짜 아이디

                # 4. 예약 정보 삽입 (확보한 진짜 seat_id를 씁니다)
                conn.execute(text("""
                    INSERT INTO reservation (user_id, seat_id, perf_id, perf_title, select_date, select_time, place, price)
                    VALUES (:user_id, :seat_id, :perf_id, :perf_title, :select_date, :select_time, :place, :price)
                """), {
                    "user_id": req.user_id, "seat_id": real_seat_id,
                    "perf_id": req.perf_id, "perf_title": req.perf_title,
                    "select_date": req.select_date, "select_time": req.select_time,
                    "place": req.place, "price": req.price
                })

        # 예매 성공 후 대기열 허가 명단에서 깔끔하게 제거
        rd.srem("allowed_users", req.user_id)
        return {"status": "success", "message": "🎉 예매 성공! 즐거운 관람 되세요!"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")