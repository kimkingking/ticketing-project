from sqlalchemy import Column, Integer, String, Date, Time, DateTime
from sqlalchemy.sql import func
from database import Base # 기존에 설정하신 Base 객체 임포트

class Reservation(Base):
    __tablename__ = 'reservation' # 실제 생성된 테이블 이름으로 변경하세요

    res_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(20), nullable=False)
    seat_id = Column(Integer, nullable=False)
    perf_id = Column(String(20), nullable=False)
    perf_title = Column(String(100), nullable=False)
    select_date = Column(Date, nullable=False)
    select_time = Column(Time, nullable=False)
    place = Column(String(150), nullable=False)
    price = Column(Integer, nullable=False)
    # res_date는 DB에서 CURRENT_TIMESTAMP로 자동 생성되게 하거나 아래처럼 서버시간 기준으로 설정
    res_date = Column(DateTime, server_default=func.now())
