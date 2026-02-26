0️⃣ 목적
프로젝트 내 모든 CSV/JSON 파일을 자동으로 탐색하여,

파일 내용을 실제로 읽고

각 파일을 적절한 DB 테이블에 매핑하고

Railway PostgreSQL에 Python(SQLAlchemy) 으로 적재하는 스크립트를 생성한다.
이때, DB 종속성과 무결성을 위해 반드시 파이프라인(단계별 스크립트) 구조로 나누어 실행한다.

⚠️ 절대 금지
파일명만 보고 분류/추측 금지 (반드시 컬럼/키 2~3개 이상 확인)

SQL 콘솔(PSQL)에서 직접 실행하는 .sql 스크립트 단독 산출 금지

sports 등 1개 카테고리만 처리 / 하드코딩 금지

run_id 및 keyword_id 숫자 하드코딩 금지

Top10 일부만 insert 금지 / 키워드 1개만 테스트 금지

모든 데이터를 하나의 파일(ingest_all.py 등)에서 한 번에 적재 금지

1️⃣ 전체 처리 대상
docs/FILE_PATHS.md에 나열된 모든 .csv, .json 파일

단 하나도 빠뜨리지 말 것

제외할 파일이 있다면 반드시 로그 및 docs/INGEST_PLAN.md에 명시할 것

2️⃣ 카테고리 처리 규칙 (매우 중요)
아래 4개 카테고리를 모두 처리해야 한다.

sports / climate / entertainment / finance_business

✅ 필수 구현
반드시 카테고리 루프 구조로 작성

특정 카테고리만 하드코딩 금지

각 카테고리는 서로 다른 run_id를 가져야 한다.

3️⃣ run_id 생성 규칙 (매우 중요)
각 카테고리별로 아래 조합으로 collection_run upsert 후 run_id 확보:

(country_code, category_id, period_start, period_end, is_dummy=false)

✅ 필수 조건
카테고리별 run_id는 서로 달라야 함

모든 데이터는 해당 카테고리의 run_id로 묶어 적재

run_id 숫자 하드코딩 금지

반드시 RETURNING run_id 사용

4️⃣ 파일 분류 및 필터링 방식 (파일명 추측 금지)
4-1. 크롤링 원본(Raw) 데이터 배제 및 분석 완료 데이터 식별 (필수)
팀원들의 크롤링 원본 파일과 분석 완료 파일이 혼재되어 있으므로, 분석이 완료된 최종 데이터만 적재한다.

뉴스/유튜브 파일 판별 시, 단순 URL이나 제목만 있는 파일은 무작정 적재하지 않는다.

부여된 rank (1~3위), 분석된 score 등 최종 결과 컬럼이 존재하는지 반드시 확인한다.

분석 컬럼이 없는 '크롤링 원본'으로 판단되는 파일은 스킵하고, docs/INGEST_PLAN.md에 "제외 사유: 크롤링 원본(Raw) 데이터"로 기록한다.

4-2. 분류 유형 (5개)
CSV는 header + 최소 20행 샘플, JSON은 상위 key 2~3개 이상 + 최소 20개 item 샘플을 읽고 판별한다.

네이버 트렌드 시계열 (trend_series, source='naver')

구글 트렌드 시계열 (trend_series, source='google')

최종 Top10 점수 결과 (keyword_score)

뉴스 데이터 (news_article)

유튜브 데이터 (youtube_video)

4-3. 결과 문서화 (필수)
docs/INGEST_PLAN.md에 모든 파일에 대해 아래 형식으로 기록:

파일 경로 / 판단 근거(columns/keys 2~3개) / 분류 결과 / 매핑 테이블 / 변환 규칙 요약 (또는 제외 사유)

5️⃣ DB 매핑 및 TOP10 규칙
5-1. keyword & keyword_score (Top10 전부 처리)
keyword 테이블: category_id + keyword_text 기준 중복 방지 upsert 필수.

keyword_score 테이블: Top10 키워드 10개 전부 적재. (파일에 rank가 없으면 기준을 정해 정렬 기록)

5-2. 상세 데이터 처리 규칙 (Top10 키워드 기준)
trend_series: (run_id, keyword_id, source, d) 키로 upsert. 반드시 7일 이상의 데이터가 있어야 함 (미만 시 누락 로그 출력 후 스킵).

news_article: 키워드별 정확히 3개 (rank 1~3)

youtube_video: 키워드별 정확히 3개 (rank 1~3)

6️⃣ “매핑 불가 파일” 처리 규칙 (스키마 보강, Python-only)
기존 스키마로 의미 있게 적재가 불가능한 파일의 경우:

docs/INGEST_PLAN.md에 매핑 불가 사유 및 필요 스키마 변경 제안 기록.

database/py/0_schema_patch.py를 생성하여 필요한 DDL(컬럼 추가 등)을 Python 내부에서 실행되도록 작성 (idempotent 보장).

7️⃣ 🚨 반드시 생성해야 할 파일 (단계별 파이프라인 산출물)
외래 키(Foreign Key) 종속성 에러를 방지하기 위해, 하나의 거대한 스크립트 대신 아래와 같이 순차적으로 실행되는 개별 파이썬 스크립트들을 생성한다.

database/py/0_schema_patch.py (조건부)

매핑 불가 파일이 있을 경우, 필요한 컬럼/테이블을 추가하는 DDL 실행. (멱등성 보장)

database/py/1_ingest_top10.py (기반 데이터 적재)

4개 카테고리(sports, climate, entertainment, finance_business) 루프 실행.

collection_run 테이블에 upsert 후 카테고리별 run_id 생성 및 확보.

Top10 결과 파일 분석 ➔ keyword 테이블에 키워드 upsert (keyword_id 확보).

확보한 run_id와 keyword_id 조합으로 keyword_score 테이블에 10개 전부 적재.

database/py/2_ingest_news.py (뉴스 적재)

DB에서 현재 카테고리별 최신 run_id와 keyword_id 정보를 조회하여 매핑.

뉴스 분석 파일 확인 ➔ 키워드별 정확히 3개의 news_article 적재.

database/py/3_ingest_youtube.py (유튜브 적재)

DB에서 최신 run_id, keyword_id 조회하여 매핑.

유튜브 분석 파일 확인 ➔ 키워드별 정확히 3개의 youtube_video 적재.

database/py/4_ingest_trends.py (시계열 데이터 적재)

DB에서 최신 run_id, keyword_id 조회하여 매핑.

구글/네이버 트렌드 파일 분석 ➔ 7일 이상의 시계열 데이터를 trend_series에 적재.

database/py/run_pipeline.py (통합 실행기 - 선택 사항)

0_schema_patch.py부터 4_ingest_trends.py까지 순차 실행하고 전체 성공/실패 로그를 요약하는 래퍼(Wrapper) 스크립트.

8️⃣ 🚨 데이터 무결성 및 ID 교차 검증 (Strict Text-based Matching)
2단계(뉴스), 3단계(유튜브), 4단계(시계열) 스크립트는 맹목적으로 최신 ID를 가져와서는 안 된다.

텍스트 기반 완벽 매핑: 현재 읽고 있는 CSV/JSON 파일에서 추출한 keyword(텍스트)와 category를 기준으로 DB를 조회하여 정확히 일치하는 keyword_id를 가져온다.

검증 실패 시 강력한 예외 처리: 파일에 있는 키워드가 1단계(Top10) DB에 존재하지 않는다면, 절대 임의로 적재하거나 새로운 keyword_id를 생성하지 말고, 해당 데이터를 Skip 처리한다.

누락 로그 의무: Skip 발생 시 콘솔에 [매핑 실패] 카테고리: {카테고리명}, 키워드: {키워드 텍스트} - Top10 DB에 존재하지 않음 이라고 명확하게 출력할 것.

9️⃣ 구현 요구사항 (Python/SQLAlchemy)
환경변수: DATABASE_URL (Railway 제공)

SQLAlchemy 사용 (Core 또는 ORM 무관)

upsert는 PostgreSQL ON CONFLICT ... DO UPDATE 사용 권장

트랜잭션: 카테고리/파일 단위로 일관되게 적용하되, 실패한 파일이 있어도 전체 중단하지 말고 요약 로그를 남길 것.

🔟 로그/검증 출력 (필수)
각 단계별 파이프라인 스크립트 실행 마지막에 반드시 다음을 출력:

처리된 카테고리 수 및 카테고리별 run_id

카테고리별 검증:

keyword_score 적재 키워드 수 (= 10인지)

trend_series 일수 최소값 (>= 7인지)

news_article 적재 개수 (키워드 * 3인지)

youtube_video 적재 개수 (키워드 * 3인지)

누락/실패/매핑 실패 파일 목록

매핑 불가 파일 목록 (+ schema_patch 필요 여부)

8️⃣ 🚨 데이터 무결성 및 ID 교차 검증 (Normalized Text-based Matching)
2단계(뉴스), 3단계(유튜브), 4단계(시계열) 스크립트는 맹목적으로 최신 ID를 가져와서는 안 된다. 특히 데이터 소스 간 띄어쓰기나 대소문자 차이로 인한 매핑 누락을 방지하기 위해 반드시 텍스트 정규화 후 비교한다.

정규화 기반 매핑 (Text Normalization):

비교를 수행할 때, 파일의 keyword와 DB의 keyword_text 양쪽 모두 1) 모든 공백 제거 (띄어쓰기 무시), 2) 영문은 소문자로 통일하는 전처리(Normalization)를 거친 후 비교한다.

예: "오징어 게임"과 "오징어게임", "Apple"과 "apple "은 모두 같은 키워드로 인식하여 keyword_id를 가져온다.

검증 실패 시 강력한 예외 처리: - 정규화 비교를 거쳤음에도 파일에 있는 키워드가 1단계(Top10) DB에 존재하지 않는다면, 절대 임의로 적재하거나 새로운 keyword_id를 생성하지 말고 해당 데이터를 Skip 처리한다.

누락 로그 의무: - Skip 발생 시 콘솔에 [매핑 실패] 카테고리: {카테고리명}, 원본 키워드: {키워드 텍스트} - Top10 DB에 존재하지 않음 이라고 명확하게 출력할 것.