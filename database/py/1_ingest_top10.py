# database/py/1_ingest_top10.py
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# ✅ .env 로드 (프로젝트 루트에 .env 있어야 함)
load_dotenv()

# ✅ 카테고리 (DB에는 이 코드로 저장됨)
CATEGORIES = {
    "sports": "스포츠",
    "climate": "기후",
    "entertainment": "연예/문화",
    "finance_business": "금융/비즈니스",
}

# ✅ 실제 CSV 파일명에 쓰이는 코드 매핑
# - finance_business 카테고리는 CSV는 finance를 사용
FILE_CODE_MAP = {
    "sports": "sports",
    "climate": "climate",
    "entertainment": "entertainment",
    "finance_business": "finance",
}

# ✅ 이미 1,2,3은 넣었으니 4번만(= finance_business만) 실행
ONLY_INGEST_CODES = {"finance_business"}


def read_csv_safe(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8")
    except Exception:
        return pd.read_csv(path, encoding="cp949")


def get_db_url() -> str:
    """
    ✅ Railway(Postgres) 연결 URL을 안전하게 가져온다.
    - 1순위: 환경변수 DATABASE_URL (.env 포함)
    - 없으면 즉시 에러로 중단 (localhost로 붙는 사고 방지)
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL이 비어있습니다.\n"
            "1) 프로젝트 루트에 .env 파일 존재 확인\n"
            "2) .env에 DATABASE_URL=postgresql://... 형태로 입력했는지 확인\n"
            "3) 실행 환경(venv/uv/anaconda)에서 .env가 로드되는지 확인"
        )

    # Railway에서 가끔 postgres:// 로 주는 경우 호환 처리
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def ingest_top10():
    url = get_db_url()
    # 민감정보 보호: 앞부분만 출력
    print("✅ Using DATABASE_URL:", url.split("@")[0] + "@...")

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cursor = conn.cursor()

    stats = {}

    for code, name in CATEGORIES.items():
        # ✅ 4번만 넣기
        if code not in ONLY_INGEST_CODES:
            print(f"⏭️ Skip (already ingested): {code}")
            continue

        file_code = FILE_CODE_MAP.get(code, code)
        print(f"📂 Category(DB): {code}  |  CSV(file_code): {file_code}")

        # 0) category 확보
        cursor.execute("SELECT category_id FROM category WHERE code = %s", (code,))
        cat_res = cursor.fetchone()

        if cat_res:
            cat_id = cat_res[0]
        else:
            cursor.execute(
                "INSERT INTO category (code, name_ko) VALUES (%s, %s) RETURNING category_id",
                (code, name),
            )
            cat_id = cursor.fetchone()[0]

        # 1) Collection Run
        base_date = "2026-02-25"
        cursor.execute(
            """
            INSERT INTO collection_run (country_code, category_id, period_start, period_end, is_dummy)
            VALUES ('KR', %s, %s, %s, FALSE)
            ON CONFLICT (country_code, category_id, period_start, period_end, is_dummy)
            DO UPDATE SET created_at = CURRENT_TIMESTAMP
            RETURNING run_id
            """,
            (cat_id, base_date, base_date),
        )
        run_id = cursor.fetchone()[0]

        # 2) Load & Merge Data (✅ file_code 기준)
        main_f = f"Top10_Trends/result/final_weighted_top10_{file_code}.csv"
        print("📁 main_f:", main_f)

        if not os.path.exists(main_f):
            print(f"⚠️ 파일 없음: {main_f}")
            continue

        df = read_csv_safe(main_f)

        # Supplemental data
        f_a = f"Top10_Trends/result/analyzed_top10_{file_code}.csv"
        if os.path.exists(f_a):
            df = df.merge(
                read_csv_safe(f_a)[
                    ["rank_title", "trend_type", "google_ratio(%)", "naver_ratio(%)"]
                ],
                on="rank_title",
                how="left",
            )

        f_q = f"Top10_Trends/result/quadrant/positioning_map_{file_code}.csv"
        if os.path.exists(f_q):
            df = df.merge(
                read_csv_safe(f_q)[
                    ["rank_title", "positioning", "volume_score", "momentum_score"]
                ],
                on="rank_title",
                how="left",
            )

        df = df.sort_values("total_score", ascending=False).head(10)

        for rank_idx, (_, row) in enumerate(df.iterrows(), start=1):
            # keyword upsert
            cursor.execute(
                """
                INSERT INTO keyword (keyword_text)
                VALUES (%s)
                ON CONFLICT (keyword_text)
                DO UPDATE SET created_at = CURRENT_TIMESTAMP
                RETURNING keyword_id
                """,
                (row["rank_title"],),
            )
            k_id = cursor.fetchone()[0]

            # keyword_score upsert
            cursor.execute(
                """
                INSERT INTO keyword_score (
                    run_id, keyword_id, rank_no, peak_time_index,
                    google_volume_text, naver_trend_sum,
                    platform_label, quadrant_label,
                    volume_score, momentum_score,
                    google_share_pct, naver_share_pct
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, keyword_id)
                DO UPDATE SET
                    rank_no = EXCLUDED.rank_no,
                    peak_time_index = EXCLUDED.peak_time_index,
                    google_volume_text = EXCLUDED.google_volume_text,
                    naver_trend_sum = EXCLUDED.naver_trend_sum,
                    platform_label = EXCLUDED.platform_label,
                    quadrant_label = EXCLUDED.quadrant_label,
                    volume_score = EXCLUDED.volume_score,
                    momentum_score = EXCLUDED.momentum_score,
                    google_share_pct = EXCLUDED.google_share_pct,
                    naver_share_pct = EXCLUDED.naver_share_pct
                """,
                (
                    run_id,
                    k_id,
                    rank_idx,
                    row.get("total_score"),
                    str(row.get("google_absolute_volume")),
                    row.get("naver_trend_sum"),
                    row.get("trend_type"),
                    row.get("positioning"),
                    row.get("volume_score"),
                    row.get("momentum_score"),
                    row.get("google_ratio(%)"),
                    row.get("naver_ratio(%)"),
                ),
            )

        stats[code] = {"run_id": run_id, "count": len(df)}
        print(f"✅ {code}: {len(df)} keywords inserted/updated. run_id={run_id}")

    conn.commit()
    cursor.close()
    conn.close()
    return stats


if __name__ == "__main__":
    ingest_top10()