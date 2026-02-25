import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

def run_sql_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    # 주의: migration.sql 안에 BEGIN/COMMIT이 있으면 autocommit=False로 둠
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"✅ Migration applied: {path}")
    except Exception as e:
        conn.rollback()
        print("❌ Migration failed:")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_sql_file("database/migration.sql")
    