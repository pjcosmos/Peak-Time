# database/py/0_schema_patch.py

import os
import psycopg2
from dotenv import load_dotenv  # ✅ .env 로드용 추가

load_dotenv()  # ✅ .env 파일 읽기


def patch_schema():
    print("🚀 Starting schema patch...")

    # 1️⃣ DATABASE_URL 가져오기
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # 2️⃣ Railway postgres:// → postgresql:// 변환
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # 3️⃣ DB 연결
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cursor = conn.cursor()

    patches = [
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS platform_label VARCHAR(100);",
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS quadrant_label VARCHAR(100);",
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS volume_score NUMERIC(10,4);",
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS momentum_score NUMERIC(10,4);",
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS google_share_pct NUMERIC(10,4);",
        "ALTER TABLE keyword_score ADD COLUMN IF NOT EXISTS naver_share_pct NUMERIC(10,4);",
        "ALTER TABLE news_article ADD COLUMN IF NOT EXISTS rank_no INT;",
        "ALTER TABLE news_article ADD COLUMN IF NOT EXISTS source VARCHAR(50);",
        "ALTER TABLE youtube_video ADD COLUMN IF NOT EXISTS rank_no INT;",
        "ALTER TABLE youtube_video ADD COLUMN IF NOT EXISTS url TEXT;"
    ]

    for query in patches:
        try:
            cursor.execute(query)
            print(f"✅ Success: {query}")
        except Exception as e:
            print(f"❌ Error: {query}")
            print(f"   ↳ {e}")

    cursor.close()
    conn.close()
    print("✨ Schema patch completed.")


if __name__ == "__main__":
    patch_schema()