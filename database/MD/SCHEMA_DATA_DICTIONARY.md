# Schema Data Dictionary (PostgreSQL)

본 문서는 프로젝트 데이터 적재(ingestion) 기준 스키마의 **테이블/컬럼 정의**를 정리한 것이다.

---

## category (카테고리 사전)

| Column | Type | Notes |
|---|---|---|
| category_id | BIGSERIAL PK | 카테고리 고유 ID |
| code | VARCHAR(50) UNIQUE | 카테고리 코드 (sports/climate/...) |
| name_ko | VARCHAR(50) | 한글 이름 |

---

## keyword (키워드 사전)

| Column | Type | Notes |
|---|---|---|
| keyword_id | BIGSERIAL PK | 키워드 ID |
| keyword_text | VARCHAR(255) UNIQUE | 키워드 텍스트 |
| created_at | TIMESTAMPTZ | 생성 시각 |

---

## collection_run (수집 실행 단위)

| Column | Type | Notes |
|---|---|---|
| run_id | BIGSERIAL PK | 수집 실행 ID |
| country_code | CHAR(2) | 국가 코드 (기본 KR) |
| category_id | BIGINT FK | → category(category_id) |
| period_start | DATE | 수집 시작일 |
| period_end | DATE | 수집 종료일 |
| is_dummy | BOOLEAN | 더미 여부 |
| created_at | TIMESTAMPTZ | 생성 시각 |

**UNIQUE**: (country_code, category_id, period_start, period_end, is_dummy)

---

## keyword_score (run별 TOP10 키워드 점수)

| Column | Type | Notes |
|---|---|---|
| run_id | BIGINT FK | → collection_run(run_id) |
| keyword_id | BIGINT FK | → keyword(keyword_id) |
| rank_no | INT | 순위 |
| peak_time_index | NUMERIC(10,4) | 점수 |
| google_share | NUMERIC(10,4) | 구글 비중 |
| naver_share | NUMERIC(10,4) | 네이버 비중 |
| google_volume_text | VARCHAR(50) | 구글 검색량 텍스트 |
| naver_trend_sum | NUMERIC(12,2) | 네이버 지수 합 |
| computed_at | TIMESTAMPTZ | 계산 시각 |

**PK**: (run_id, keyword_id)

---

## trend_series (시계열 일별 데이터)

| Column | Type | Notes |
|---|---|---|
| run_id | BIGINT FK | → collection_run(run_id) |
| keyword_id | BIGINT FK | → keyword(keyword_id) |
| source | VARCHAR(10) | 'google' or 'naver' |
| d | DATE | 날짜 |
| value | NUMERIC(12,2) | 해당 날짜 지수 |

**PK**: (run_id, keyword_id, source, d)

---

## news_article (뉴스 기사)

| Column | Type | Notes |
|---|---|---|
| article_id | BIGSERIAL PK | 기사 ID |
| run_id | BIGINT FK | → collection_run(run_id) |
| keyword_id | BIGINT FK | → keyword(keyword_id) |
| title | TEXT | 제목 |
| url | TEXT | 링크 |
| publisher | VARCHAR(255) | 언론사 |
| published_at | TIMESTAMPTZ | 발행일 |
| image_url | TEXT | 이미지 URL |
| collected_at | TIMESTAMPTZ | 수집 시각 |

---

## youtube_video (유튜브 영상)

| Column | Type | Notes |
|---|---|---|
| video_pk | BIGSERIAL PK | 내부 PK |
| run_id | BIGINT FK | → collection_run(run_id) |
| keyword_id | BIGINT FK | → keyword(keyword_id) |
| youtube_id | VARCHAR(50) | 유튜브 영상 ID |
| title | TEXT | 제목 |
| channel_title | VARCHAR(255) | 채널명 |
| published_at | TIMESTAMPTZ | 업로드 시각 |
| view_count | BIGINT | 조회수 |
| like_count | BIGINT | 좋아요 |
| comment_count | BIGINT | 댓글 수 |
| thumbnail_url | TEXT | 썸네일 |
| collected_at | TIMESTAMPTZ | 수집 시각 |

**UNIQUE**: (run_id, keyword_id, youtube_id)