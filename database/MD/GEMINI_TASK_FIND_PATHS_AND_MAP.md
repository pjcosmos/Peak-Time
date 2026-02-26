# Gemini CLI Task: 프로젝트 파일 경로 스캔 + 스키마 매핑 추천 문서 생성

너는 로컬 프로젝트에서 데이터 적재 계획서를 생성하는 역할이다.
목표는 (1) 데이터 파일 경로를 모두 찾고, (2) 아래 스키마 컬럼 정의를 기준으로
각 파일이 어느 테이블에 들어가면 좋은지 추천하는 문서를 만드는 것이다.

---

## 입력: 스키마 컬럼 정의
아래 파일 내용을 기준으로 매핑하라:
- database/SCHEMA_DATA_DICTIONARY.md

---

## 해야 할 일 (반드시 순서대로)

### STEP 1) 프로젝트 루트 재귀 스캔
- 현재 디렉터리를 프로젝트 루트로 보고 재귀적으로 파일을 스캔한다.
- 제외 폴더:
  - .git, .venv, venv, __pycache__, node_modules, .idea, .vscode
- 대상 확장자:
  - .csv, .json, .ndjson, .xlsx, .parquet

### STEP 2) 파일 메타 수집
각 파일에 대해:
- 상대경로
- 파일 크기(bytes)
- 파일 유형(ext)
- CSV면 첫 줄 헤더 읽기
- JSON/NDJSON면 첫 오브젝트의 키 목록 읽기(가능하면)

### STEP 3) 스키마 매핑 추천
- 스키마(테이블/컬럼)와 파일 헤더/키를 비교하여 추천 테이블을 선택한다.
- 추천 후보 테이블:
  - keyword_score, trend_series, news_article, youtube_video, keyword
- 추천 규칙(휴리스틱):
  - keyword_score: rank/title/score/volume/naver_trend_sum 류 컬럼이 있으면 강하게 추천
  - trend_series: source + date(d) + value 류가 있으면 강하게 추천
  - news_article: title + url + publisher/published_at 류가 있으면 강하게 추천
  - youtube_video: youtube_id + channel_title + view_count/thumbnail_url 류가 있으면 강하게 추천
- 확신이 낮으면 UNKNOWN으로 분류하고, 왜 낮은지(헤더 없음/키 부족)를 기록한다.

### STEP 4) 결과 문서 생성
아래 파일을 생성/갱신해서 저장해:
- database/INGEST_PATHS_AND_MAPPING.md

문서에는 반드시 포함:
1) 발견한 파일 총 개수, UNKNOWN 개수
2) 파일별 표:
   - 번호, 상대경로, 파일유형, 헤더/키 미리보기(상위 15개), 추천 테이블, 추천 근거
3) 다음 단계 가이드:
   - run 생성 필요(collection_run)
   - keyword upsert 필요(keyword)
   - 이후 점수/시계열/뉴스/유튜브 순으로 적재 권장
4) UNKNOWN 처리 가이드(헤더 추가/파일명 힌트/샘플 제공 등)

---

## 출력 제한
- 최종 출력은 `database/INGEST_PATHS_AND_MAPPING.md` 문서 내용만 출력한다.
- 중간 작업 로그는 최소화하되, 실패 시 에러 원문은 출력한다.