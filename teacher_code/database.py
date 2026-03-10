import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. DB 접속 정보 설정
DB_USER = "kedu"
DB_PASS = "P@ssw0rd"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "WebTest"

# 2. 특수문자(@) 처리를 위한 인코딩 (매우 중요)
# quote_plus를 사용하면 '@'가 '%40'으로 변환되어 경로 혼선을 막습니다.
safe_pass = urllib.parse.quote_plus(DB_PASS)

# 3. URL 조립 (f-string 사용 시 오타 주의)
# :safe_pass 뒤에 @가 붙어야 합니다. (user:pass@host 형식)
DB_URL = f"mysql+pymysql://{DB_USER}:{safe_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4. SQLAlchemy 설정
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테스트용 코드 (수업 시 확인용): 실행했을 때 URL이 어떻게 나오는지 출력해봅니다.
print(f"DEBUG: Generated DB URL is -> {DB_URL}")
