import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL이 .env에 없습니다.")

def delete_all_dummy_runs():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # 지우기 전에 몇 개나 있는지 확인
            cur.execute("SELECT count(*) FROM collection_run WHERE is_dummy = TRUE;")
            cnt = cur.fetchone()[0]

            cur.execute("DELETE FROM collection_run WHERE is_dummy = TRUE;")

        conn.commit()
        print(f"✅ 더미 run {cnt}개 삭제 완료 (CASCADE로 하위 데이터도 함께 삭제됨)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    delete_all_dummy_runs()