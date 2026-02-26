# 🚀 Peak-Time: 데이터 기반 통합 트렌드 분석 대시보드

## 📖 프로젝트 소개
Peak-Time은 구글 트렌드와 네이버 데이터랩의 검색 데이터를 융합하여 단순한 이슈가 아닌 '진짜 트렌드'를 발굴하는 데이터 기반 분석 대시보드입니다. 단순한 검색 순위를 넘어 언론 기사(공급) 및 유튜브 영상(영상 소비) 데이터를 결합하여 대중의 수요와 언론 공급 간의 불일치를 분석하고, 마케팅 및 콘텐츠 전략 수립에 실질적인 가치를 제공합니다. 

## 🛠 기술 스택
* **Frontend:** Streamlit, Plotly, Custom HTML/CSS
* **Backend & Data Pipeline:** Python, Pandas, NumPy, SQLAlchemy
* **Database:** PostgreSQL (Railway Cloud)
* **Scraping & APIs:** Selenium, Naver Search Trend API, YouTube Data API v3, Google News RSS

## ✨ 주요 기능

### 1. 크로스 플랫폼 데이터 융합 및 지표 정규화
* 서로 체급이 다른 구글 데이터(절대 검색량, 급상승 비율)와 네이버 데이터(일간 비율 추이, 성장세 기울기)를 Min-Max 정규화하여 동등한 스케일에서 평가합니다.
* 검색 규모(Volume)에 70%, 단기 화제성(Momentum)에 30%의 가중치를 부여하여 안정적이면서도 화제성 있는 '통합 TOP 10 랭킹'을 도출합니다.
* 구글 트렌드 데이터 수집 시, Selenium JS 스냅샷 스크립트를 사용하여 동적 렌더링 지연으로 인한 누락 없이 데이터를 안정적으로 크롤링합니다.

### 2. 수요-공급 불일치 기반 '오션 전략 분석'
* 전체 키워드의 '평균 트렌드 점수(수요)'와 '평균 기사량(공급)'을 교차 분석합니다.
* 대중은 많이 검색하지만 언론 보도는 적은 **블루오션**, 경쟁이 치열한 **레드오션**, 언론만 떠드는 **미디어 버블**, 아직 빛을 보지 못한 **마이너/잠복기** 등 4가지 상태로 자동 판별하여 포지셔닝 맵(Scatter 차트)으로 시각화합니다.

### 3. 유튜브 찐팬 온도계 (참여도 분석)
* 조회수 중심의 평가를 탈피하고, `(평균 좋아요 + 평균 댓글 수) / 평균 조회수` 기반의 '참여율(Engagement Rate)'을 계산합니다.
* 해당 키워드가 단순 정보 소비용인지, 강력한 팬덤형 키워드인지 게이지 차트를 통해 직관적인 온도로 제공합니다.

### 4. 반응형 Streamlit 웹 대시보드
* **UX 최적화:** 1:2 화면 분할을 통해 좌측 패널(카테고리별 TOP 10 리스트)에서 특정 키워드를 클릭 시, 우측 패널(심층 분석)이 `st.session_state`를 활용하여 새로고침 없이 즉각 업데이트됩니다.
* **이종 데이터 맞춤 시각화:** 일별 시계열이 없는 구글 트렌드는 '핵심 지표(Metric Card)'로, 7일 추이가 있는 네이버 데이터랩은 '시계열 라인 차트(Plotly)'로 시각화합니다.
* **고도화된 미디어 렌더링:** `st.markdown`과 HTML/CSS Flexbox를 활용해, DB에서 불러온 뉴스 기사와 유튜브 영상의 썸네일, 제목, 주요 지표를 완벽한 수평 대칭형 UI 구조로 세련되게 렌더링합니다. Custom CSS로 구글 브랜드 컬러에 맞춘 테마 오버라이딩을 적용했습니다.

### 5. 원클릭 자동화 파이프라인
* 데이터 전처리 로직(문자열 파싱, 회귀 계산), 가중치 분석, 4분면 라벨링, 시각화 파일 생성 과정을 `run_pipeline.py` 하나로 묶어 파이프라인을 자동화했습니다.

## 🗄 데이터베이스 구조 (Schema)
프로젝트는 다수 팀원의 동시 접근 및 수집 시점별 버전 관리를 위해 Railway 클라우드 기반 PostgreSQL을 사용합니다. 데이터 무결성을 위해 모든 정보는 특정 수집 시점(`run_id`) 단위로 종속됩니다.

* `category` / `keyword`: 카테고리 정보 및 유니크 키워드 사전
* `collection_run`: 특정 일자의 수집 실행 단위 (가장 상위 부모 테이블)
* `keyword_score`: 키워드별 통합 점수, 플랫폼 점유율, 오션 전략 라벨
* `trend_series`: 구글 및 네이버의 일간 상대적 검색 추이 라인 차트 데이터
* `news_article`: 각 키워드와 매핑된 최신 관련 기사 (발행일, 썸네일 URL 포함)
* `youtube_video`: 유튜브 검색 API에서 가져온 관련 영상 상세 통계 (조회수, 좋아요, 댓글 수)

## 💻 설치 및 실행 방법

### 1. 레포지토리 클론 및 의존성 설치
Python 3.9 이상의 환경을 권장하며, 데이터 수집을 위한 Chrome WebDriver 환경이 요구됩니다.
```bash
git clone [https://github.com/your-username/Peak-Time.git](https://github.com/your-username/Peak-Time.git)
cd Peak-Time
pip install -r requirements.txt
pip install psycopg2-binary