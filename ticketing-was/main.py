from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, rd # 여기도 필요합니다!
from security import SecurityFilterMiddleware  # 만든 파일 불러오기
import login
import signin
import reservation

app = FastAPI()

# CORS 설정 (보혜님의 실제 환경에 맞춘 업데이트)
origins = [
    "http://www.pulseticket.ke:30007", 
    "http://www.pulseticket.ke",
    "http://10.4.0.150:30007", 
    "http://10.4.0.203",       
    "http://10.4.0.150",       
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 업데이트된 리스트 적용!
    allow_credentials=True,
    allow_methods=["*"],         # 모든 방식(GET, POST 등) 허용
    allow_headers=["*"],         # 모든 헤더 허용
)

# 팀원분 & 보혜님 라우터 등록
app.include_router(login.router)
app.include_router(signin.router)
app.include_router(reservation.router, prefix="/api/reservations")
# 보안 미들웨어 적용
app.add_middleware(SecurityFilterMiddleware)

# --- 보혜님의 나머지 기능들을 여기에 그대로 유지합니다! ㅋ ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Integrated Ticketing System! 🚀"}

@app.get("/db-test")
def test_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {"status": "success", "db_result": "Connected to MariaDB!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

@app.post("/next")
def allow_next_users(count: int = 10): # 몇 명씩 들여보낼지
    try:
        # 가장 먼저 와서 줄을 선 사람부터 정해진 인원수만큼 이름을 호명(새치기 불가!)
        top_users = rd.zrange("ticket_queue", 0, count - 1)
        
        if not top_users:
            return {"status": "success", "message": "현재 대기열이 텅 비어있습니다."}
        
        rd.sadd("allowed_users", *top_users)
        rd.zrem("ticket_queue", *top_users)
        
        return {
            "status": "success",
            "message": f"{len(top_users)}명의 유저가 입장 허가를 받았습니다!",
            "allowed_users": top_users
        }
    except Exception as e:
        return {"status": "error", "message": f"대기열 이동 중 오류 발생: {str(e)}"}

@app.get("/")
async def root():
    return {"status": "Secure Service Running"}
