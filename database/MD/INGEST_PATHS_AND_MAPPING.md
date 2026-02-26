# Data Ingestion Paths & Mapping Report

이 문서는 프로젝트 내 데이터 파일의 경로를 스캔하고, `database/SCHEMA_DATA_DICTIONARY.md`의 스키마 정의를 바탕으로 적재(Ingestion) 매핑 추천을 정리한 것이다.

## 1. 스캔 요약
- **발견된 총 데이터 파일**: 66개
- **UNKNOWN 분류**: 8개 (주로 분석 결과물/시각화용 중간 데이터)

---

## 2. 파일별 매핑 상세 (주요 파일 위주)

| 번호 | 상대경로 | 파일유형 | 헤더/키 미리보기 | 추천 테이블 | 추천 근거 |
|:---:|:---|:---:|:---|:---|:---|
| 1 | `news/*.json` | JSON | `article_id, run_id, keyword_id, title, url, publisher, published_at...` | **news_article** | 스키마 컬럼과 거의 1:1 일치 |
| 2 | `YouTube_depth_analysis/youtube_data_integrated.csv` | CSV | `run_id, keyword_id, youtube_id, title, channel_title, view_count...` | **youtube_video** | 스키마 컬럼과 거의 1:1 일치 |
| 3 | `Top10_Trends/result/final_weighted_top10_*.csv` | CSV | `rank_title, total_score, google_absolute_volume, naver_trend_sum...` | **keyword_score** | 순위권 키워드 점수 및 지표 포함 |
| 4 | `Top10_Trends/raw_data/trend_report_*.json` | JSON | `category, base_date, rank_title, naver_daily_ratio...` | **trend_series** | `naver_daily_ratio` 시계열 데이터 포함 (변환 필요) |
| 5 | `Top10_Trends/data/preprocessed_*.csv` | CSV | `rank_title, google_absolute_volume, naver_trend_sum, naver_daily_ratio...` | **keyword_score** | 전처리된 점수 데이터 |
| 6 | `Deep_Analysis/data/youtube/youtube_data_integrated.csv` | CSV | `run_id, keyword_id, youtube_id, title, view_count...` | **youtube_video** | 분석용 통합 유튜브 데이터 |
| 7 | `Deep_Analysis/result/web_data/ocean_discriminator.csv` | CSV | `category, rank_title, total_score, ocean_status...` | **keyword_score** | 점수 기반 분석 결과 (확장 속성으로 처리 가능) |
| 8 | `naver_data/trend_report_*.json` | JSON | `category, base_date, results[{rank_title, naver_trend_sum...}]` | **trend_series** | 원천 트렌드 데이터 (변환 필요) |
| 9 | `Deep_Analysis/result/web_data/youtube_engagement_*.json` | JSON | `keyword, avg_view_count, avg_like_count, engagement_rate...` | **UNKNOWN** | 분석 요약본. `youtube_video`의 통계 데이터임. |
| 10 | `Deep_Analysis/data/youtube/trend_vs_youtube_merged.csv` | CSV | `rank_title, total_score, view_count_sum, correlation...` | **UNKNOWN** | 상관관계 분석용 중간 파일. |

---

## 3. 다음 단계 가이드

데이터 적재 시 다음 순서를 권장한다:

1.  **Collection Run 생성 (`collection_run`)**
    - 파일의 파일명이나 `base_date`를 기준으로 `run_id`를 먼저 생성한다.
2.  **Keyword Upsert (`keyword`)**
    - 모든 파일의 `rank_title` 또는 `keyword_text`를 `keyword` 테이블에 먼저 등록(Upsert)하여 `keyword_id`를 확보한다.
3.  **데이터 적재 순서**
    - `keyword_score` (TOP10 요약 데이터)
    - `trend_series` (일별 시계열 데이터 - JSON 배열 파싱 필요)
    - `news_article` (뉴스 상세)
    - `youtube_video` (유튜브 상세)

---

## 4. UNKNOWN 처리 가이드

- `UNKNOWN`으로 분류된 파일들은 대부분 시각화(D3.js, Chart.js 등)를 위해 가공된 JSON/CSV이다.
- 이러한 파일들은 직접 DB에 적재하기보다, DB에 적재된 원천 데이터(`news_article`, `youtube_video` 등)를 쿼리하여 API 수준에서 실시간 또는 캐시로 생성하는 것을 권장한다.
- 만약 분석 결과(예: 상관관계 계수) 자체를 영구 보관해야 한다면, 별도의 `analysis_result` 테이블 정의가 필요하다.
