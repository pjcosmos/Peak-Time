import os
import random
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL이 .env에 없습니다.")

CATEGORIES = [
    ("sports", "스포츠"),
    ("climate", "기후"),
    ("ent", "연예"),
]

KEYWORDS = [
    "손흥민", "이강인", "김연아", "프로야구", "KBO",
    "날씨", "미세먼지", "폭설", "한파", "장마",
    "아이유", "뉴진스", "BTS", "오스카", "넷플릭스",
    "비트코인", "엔비디아", "테슬라", "삼성전자", "애플",
]

DUMMY_NEWS = [
    ("더미 기사: 키워드 급상승", "https://example.com/news/1", "DemoPress"),
    ("더미 기사: 검색량 변화 분석", "https://example.com/news/2", "DemoDaily"),
]

DUMMY_YT = [
    ("dQw4w9WgXcQ", "더미 영상: 이슈 요약", "DemoChannel"),
    ("M7lc1UVf-VE", "더미 영상: 1분 브리핑", "DemoChannel2"),
]


def main():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            # 1) category upsert
            execute_values(
                cur,
                """
                INSERT INTO category (code, name_ko)
                VALUES %s
                ON CONFLICT (code) DO UPDATE SET name_ko = EXCLUDED.name_ko
                """,
                CATEGORIES,
            )

            # 2) get category_id for 'sports'
            cur.execute("SELECT category_id FROM category WHERE code=%s", ("sports",))
            category_id = cur.fetchone()[0]

            # 3) create dummy collection_run
            period_end = datetime.now().date()
            period_start = period_end - timedelta(days=6)

            cur.execute(
                """
                INSERT INTO collection_run
                (country_code, category_id, period_start, period_end, is_dummy)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING run_id
                """,
                ("KR", category_id, period_start, period_end),
            )
            run_id = cur.fetchone()[0]

            # 4) keyword upsert
            execute_values(
                cur,
                """
                INSERT INTO keyword (keyword_text)
                VALUES %s
                ON CONFLICT (keyword_text) DO NOTHING
                """,
                [(k,) for k in KEYWORDS],
            )

            # 5) get keyword_id map
            cur.execute(
                "SELECT keyword_id, keyword_text FROM keyword WHERE keyword_text = ANY(%s)",
                (KEYWORDS,),
            )
            rows = cur.fetchall()
            kw_to_id = {text: kid for kid, text in rows}

            # 6) insert keyword_score (Top10 나오도록 점수 분포 만들기)
            score_rows = []
            for i, kw in enumerate(KEYWORDS):
                kid = kw_to_id[kw]
                g = random.random()
                n = random.random()
                wg, wn = 0.40, 0.60

                # 상위 10개는 점수 조금 더 크게
                boost = 0.35 if i < 10 else 0.0
                pti = min(1.0, (wg * g + wn * n) + boost)

                score_rows.append((run_id, kid, round(g, 4), round(n, 4), wg, wn, round(pti, 4)))

            execute_values(
                cur,
                """
                INSERT INTO keyword_score
                (run_id, keyword_id, google_norm, naver_norm, weight_google, weight_naver, peak_time_index)
                VALUES %s
                ON CONFLICT (run_id, keyword_id) DO UPDATE SET
                    google_norm = EXCLUDED.google_norm,
                    naver_norm = EXCLUDED.naver_norm,
                    weight_google = EXCLUDED.weight_google,
                    weight_naver = EXCLUDED.weight_naver,
                    peak_time_index = EXCLUDED.peak_time_index,
                    computed_at = CURRENT_TIMESTAMP
                """,
                score_rows,
            )

            # 7) (선택) Step1 시계열 더미: 7일치(일단위)로 간단히
            series_rows_google = []
            series_rows_naver = []

            for kw in KEYWORDS:
                kid = kw_to_id[kw]
                for d in range(7):
                    ts = datetime.combine(period_start + timedelta(days=d), datetime.min.time())
                    series_rows_google.append((run_id, kid, ts, round(random.uniform(0, 100), 2)))
                    series_rows_naver.append((run_id, kid, ts, round(random.uniform(0, 1000), 2)))

            execute_values(
                cur,
                """
                INSERT INTO google_trend_series (run_id, keyword_id, ts, value)
                VALUES %s
                ON CONFLICT (run_id, keyword_id, ts) DO UPDATE SET value = EXCLUDED.value
                """,
                series_rows_google,
                page_size=1000,
            )

            execute_values(
                cur,
                """
                INSERT INTO naver_search_series (run_id, keyword_id, ts, value)
                VALUES %s
                ON CONFLICT (run_id, keyword_id, ts) DO UPDATE SET value = EXCLUDED.value
                """,
                series_rows_naver,
                page_size=1000,
            )

            # 8) Step2 더미: 상위 10개 키워드에만 뉴스/유튜브 2개씩
            top10_keywords = KEYWORDS[:10]
            news_rows = []
            yt_rows = []

            now_ts = datetime.now()

            for kw in top10_keywords:
                kid = kw_to_id[kw]

                for title, url, publisher in DUMMY_NEWS:
                    news_rows.append(
                        (run_id, kid, f"[{kw}] {title}", url, publisher, now_ts - timedelta(days=random.randint(0, 2)))
                    )

                for yid, title, ch in DUMMY_YT:
                    yt_rows.append(
                        (
                            run_id, kid, yid, f"[{kw}] {title}", ch,
                            now_ts - timedelta(days=random.randint(0, 5)),
                            random.randint(10_000, 3_000_000),
                            random.randint(100, 100_000),
                            random.randint(0, 20_000),
                        )
                    )

            execute_values(
                cur,
                """
                INSERT INTO news_article
                (run_id, keyword_id, title, url, publisher, published_at)
                VALUES %s
                """,
                news_rows,
            )

            execute_values(
                cur,
                """
                INSERT INTO youtube_video
                (run_id, keyword_id, youtube_id, title, channel_title, published_at, view_count, like_count, comment_count)
                VALUES %s
                """,
                yt_rows,
            )

        conn.commit()
        print(f"✅ 더미 seed 완료! run_id = {run_id} (is_dummy = true)")

    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()