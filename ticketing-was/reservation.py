import os
import time
import httpx  # 👈 추가 필요 (pip install httpx)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import engine, rd

# 1. 환경변수 설정
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")

router = APIRouter()

# HTTP 클라이언트를 하나만 띄워서 계속 재사용 (성능 극대화!)
http_client = httpx.AsyncClient()

# 2. 데이터 모델 (turnstile_token 필드 추가!)
class ReservationRequest(BaseModel):
    user_id: str
    seat_id: int
    perf_id: str
    perf_title: str
    select_date: str
    select_time: str
    place: str
    price: int
    turnstile_token: str  # 👈 캡차 검증을 위해 반드시 필요합니다.

# 3. 캡차 검증 비동기 함수
async def verify_turnstile(token: str) -> bool:
    if not TURNSTILE_SECRET_KEY:
        return False
    # 클라이언트를 매번 생성하지 않고 전역 클라이언트를 재사용합니다.
    response = await http_client.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={"secret": TURNSTILE_SECRET_KEY, "response": token}
    )
    return response.json().get("success", False)

# 4. 예약 API (async로 변경 필수!)
@router.post("/reserve")
async def reserve_ticket(req: ReservationRequest):
    try:
        # [STEP 0] 캡차 검증 및 테스트 우회 로직
        is_test_mode = (DEBUG_MODE and req.turnstile_token == "JETER_TEST_TOKEN")
        
        if not is_test_mode:
            if not await verify_turnstile(req.turnstile_token):
                raise HTTPException(status_code=403, detail="매크로/봇 접근이 감지되었습니다.")

        # 1. Redis 대기열 기록
        now = time.time()
        rd.zadd("ticket_queue", {req.user_id: now})
        rank = rd.zrank("ticket_queue", req.user_id) + 1

        with engine.connect() as conn:
            with conn.begin():
                # 2. 비관적 락: 해당 좌석을 꽉 잡습니다.
                select_query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(select_query, {"id": req.seat_id}).fetchone()

                # 3. 상태 체크
                if not seat or seat[0] != 'AVAILABLE':
                    return {
                        "status": "fail",
                        "message": "이미 예약이 완료된 좌석입니다.",
                        "waiting_number": rank
                    }

                # 4. 바로 OCCUPIED(점유됨)로 변경
                update_query = text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id")
                conn.execute(update_query, {"id": req.seat_id})

                # 5. 예약 장부 작성
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
            "message": f"{req.seat_id}번 좌석 예약이 완료되었습니다!",
            "waiting_number": rank
        }
    except HTTPException as he:
        raise he  # 403 에러 등은 그대로 던집니다.
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"예약 중 오류 발생: {str(e)}")
