import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

# database.py에서 DB와 Redis 연결선 가져오기
from database import engine, rd

router = APIRouter()

# 캡차용 turnstile_token 필드 삭제 완료!
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
        # 1. 대기열 방어벽 (Redis)
        # Redis의 'allowed_users'라는 명단에 이 유저가 있는지 확인 
        is_allowed = rd.sismember("allowed_users", req.user_id)
        
        if not is_allowed:
            # 명단에 없으면 큐에 넣고 순위만 반환 (DB 접근 원천 차단)
            now = time.time()
            rd.zadd("ticket_queue", {req.user_id: now})
            rank = rd.zrank("ticket_queue", req.user_id) + 1
            return {
                "status": "wait",
                "message": "아직 예매 순서가 아닙니다. 잠시만 대기해주세요",
                "waiting_number": rank
            }
        
        # 2. ==== 허가받은 인원만 들어오는 MariaDB 구역 ====
        with engine.connect() as conn:
            with conn.begin():
                # 비관적 락 (FOR UPDATE) - 중복 예매 방지
                select_query = text("SELECT status FROM seat WHERE seat_id = :id FOR UPDATE")
                seat = conn.execute(select_query, {"id": req.seat_id}).fetchone()

                if not seat or seat[0] != 'AVAILABLE':
                    return {
                        "status": "fail",
                        "message": "이미 예약이 완료된 좌석입니다.",
                    }
                
                # 좌석 상태 업데이트
                update_query = text("UPDATE seat SET status = 'OCCUPIED' WHERE seat_id = :id")
                conn.execute(update_query, {"id": req.seat_id})

                # 예약 내역 저장
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
        
        # 3. 예매 성공 후 명단에서 지워주기 (재사용 방지)
        rd.srem("allowed_users", req.user_id)
        
        return {
            "status": "success",
            "message": f"{req.seat_id}번 좌석 예약이 완료되었습니다!",
        }
    except HTTPException as he:
        raise he  
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"예약 중 오류 발생: {str(e)}")
