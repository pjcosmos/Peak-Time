import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()  # .env 로드

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL loaded?", bool(DATABASE_URL))  # 디버그

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL이 .env 또는 환경변수에 없습니다. (.env 위치/이름 확인)")

SQL = """
TRUNCATE TABLE
  youtube_video,
  news_article,
  trend_series,
  keyword_score,
  collection_run,
  keyword,
  category
RESTART IDENTITY
CASCADE;
"""

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute(SQL)

conn.close()
print("✅ 모든 테이블 데이터 삭제 완료")