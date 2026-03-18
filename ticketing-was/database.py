from sqlalchemy import create_engine
import redis

# was_user 계정 사용!
DB_URL = "mysql+pymysql://was_user:1234@mysql:3306/ticket?charset=utf8mb4"
engine = create_engine(DB_URL, echo=True)

rd = redis.Redis(host='redis-service', port=6379, db=0, decode_responses=True)
