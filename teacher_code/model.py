from sqlalchemy import Column, Integer, String, Text, DateTime, CHAR
from database import Base
import datetime

class Member(Base):
    __tablename__ = "member"
    no = Column(Integer, primary_key=True, autoincrement=True)
    u_id = Column(String(20), unique=True, nullable=False)
    u_pass = Column(String(50), nullable=False)
    u_name = Column(String(20), nullable=False)
    nickname = Column(CHAR(20))
    age = Column(Integer)
    email = Column(CHAR(50))
    reg_date = Column(DateTime, default=datetime.datetime.now)

class Board(Base):
    __tablename__ = "board"
    strNumber = Column(Integer, primary_key=True, autoincrement=True)
    strName = Column(String(20), nullable=False)
    strPassword = Column(String(20), nullable=False)
    strEmail = Column(String(50))
    strSubject = Column(String(100), nullable=False)
    strContent = Column(Text, nullable=False)
    htmlTag = Column(CHAR(1), nullable=False, default='N')
    viewCount = Column(Integer, default=0)
    filename = Column(String(50))
    filesize = Column(Integer)
    writeDate = Column(DateTime, default=datetime.datetime.now)
