import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))

cur = conn.cursor()
cur.execute("SELECT 1;")
print("✅ DB 연결 성공!!:", cur.fetchone())

cur.close()
conn.close()