# 📋 INGEST_PLAN.md

## 1. 개요
`docs/FILE_PATHS.md`에 나열된 66개 파일을 분석하여, `docs/INGEST_TASK_FULL.md`의 명세에 따라 분석 완료된 최종 데이터만 선별하여 적재하는 계획을 수립함.

## 2. 파일 분류 및 매핑 상세

### A. 유형 1: 트렌드 시계열 (trend_series)
- **대상**:
  - `naver_data/trend_report_*.json` (4개)
  - `Top10_Trends/raw_data/trend_report_*.json` (4개)
- **판단 근거**: `results` 내 `naver_daily_ratio` (period, ratio) 포함.
- **매핑**: `trend_series` (source='naver')
- **제한**: 7일 미만 데이터 스킵.

### B. 유형 2: 최종 Top10 점수 (keyword_score)
- **대상**:
  - `Top10_Trends/result/final_weighted_top10_*.csv` (4개)
  - `Top10_Trends/result/analyzed_top10_*.csv` (4개) - `trend_type` 보강
  - `Top10_Trends/result/quadrant/positioning_map_*.csv` (4개) - `positioning` 보강
- **판단 근거**: `total_score`, `trend_type`, `positioning` 등 최종 분석 지표 포함.
- **매핑**: `keyword_score`

### C. 유형 3: 뉴스 분석 데이터 (news_article)
- **대상**:
  - `news/*.json` (naver, daum, google)
  - `Deep_Analysis/data/news/*.json`
- **판단 근거**: 기사 제목, URL, 발행일 및 분석된 키워드 매핑 정보.
- **매핑**: `news_article` (키워드별 상위 3개, rank_no 1~3)

### D. 유형 4: 유튜브 분석 데이터 (youtube_video)
- **대상**:
  - `YouTube_depth_analysis/youtube_data_integrated.csv`
  - `Deep_Analysis/data/youtube/youtube_data_integrated.csv`
- **판단 근거**: `view_count`, `like_count` 및 분석된 키워드/순위 정보.
- **매핑**: `youtube_video` (키워드별 상위 3개, rank_no 1~3)

### E. 제외 대상 (Raw Data / Skip)
- **제외 사유: 크롤링 원본(Raw) 데이터**:
  - `naver_data/collection_summary.json`
  - `Top10_Trends/data/preprocessed_*.csv` (중간 가공)
- **제외 사유: 분석 요약/시각화 전용**:
  - `Deep_Analysis/result/web_data/*.json`, `*.csv`
  - `Deep_Analysis/data/youtube/trend_vs_youtube_merged.csv` (상관관계 요약본)
- **기타**: 모든 `.png`, `.ipynb`, `.py`

---

## 3. 매핑 불가 및 스키마 보강 (Patch)
- **부재 컬럼**: `platform_label`, `quadrant_label` (keyword_score), `rank_no` (news, youtube) 등.
- **조치**: `database/py/0_schema_patch.py` 생성하여 Python DDL 실행.

---

## 4. 파이프라인 구성 (순차 실행)
1. `0_schema_patch.py`: 스키마 업데이트
2. `1_ingest_top10.py`: 카테고리/Run/키워드/점수 (기반)
3. `2_ingest_news.py`: 뉴스 (정규화 매핑)
4. `3_ingest_youtube.py`: 유튜브 (정규화 매핑)
5. `4_ingest_trends.py`: 시계열 (7일+)
6. `ingest_all.py`: 전체 실행 래퍼 및 최종 리포트 출력
