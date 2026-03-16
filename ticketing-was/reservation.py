# reservation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import time
from database import engine, rd  # 분리된 설정 파일에서 가져오기

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

@router.post("/reserve")
def reserve_ticket(req: ReservationRequest):
    try:
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

                # 5. ⭐ 예약 장부 작성 (이게 빠져있었어요! ㅋ)
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
    except Exception as e:
        # 에러 로그 출력
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"예약 중 오류 발생: {str(e)}")
