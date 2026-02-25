import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# .env 파일 환경변수 로드
load_dotenv()

# 5. 페이지 설정
st.set_page_config(layout="wide", page_title="Peak-Time Trend Dashboard")

# -----------------------
# DB 연결 (Railway Postgres)
# -----------------------
def get_db_url():
    # 1. 환경변수(.env)에서 먼저 주소 가져오기
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
        
    # 2. .env에 없다면 Streamlit secrets 확인 (에러 방지 처리)
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except FileNotFoundError:
        pass
        
    return None

@st.cache_resource
def get_engine():
    db_url = get_db_url()
    if not db_url:
        st.error("DATABASE_URL이 설정되어 있지 않습니다. (.env 파일 또는 환경변수를 확인해주세요)")
        st.stop()

    # Railway가 postgres:// 로 줄 때 보정
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    if db_url.startswith("postgresql://"):
        # SQLAlchemy 드라이버 명시
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return create_engine(db_url, pool_pre_ping=True)

engine = get_engine()

# -----------------------
# 세션 상태 초기화
# -----------------------
if "selected_keyword_id" not in st.session_state:
    st.session_state.selected_keyword_id = None
if "selected_keyword_text" not in st.session_state:
    st.session_state.selected_keyword_text = None

# -----------------------
# DB 조회 함수들
# -----------------------
@st.cache_data(ttl=60)
def load_categories():
    q = """
    SELECT category_id, code, name_ko
    FROM category
    ORDER BY name_ko ASC;
    """
    return pd.read_sql(text(q), engine)

@st.cache_data(ttl=60)
def load_latest_run_id(category_id: int, country_code: str = "KR", is_dummy: bool = False):
    q = """
    SELECT run_id
    FROM collection_run
    WHERE country_code = :country_code
      AND category_id = :category_id
      AND is_dummy = :is_dummy
    ORDER BY created_at DESC
    LIMIT 1;
    """
    df = pd.read_sql(
        text(q),
        engine,
        params={"country_code": country_code, "category_id": category_id, "is_dummy": is_dummy},
    )
    return int(df.iloc[0]["run_id"]) if not df.empty else None

@st.cache_data(ttl=60)
def load_top10(run_id: int):
    q = """
    SELECT
        ks.rank_no,
        k.keyword_id,
        k.keyword_text,
        ks.peak_time_index
    FROM keyword_score ks
    JOIN keyword k ON k.keyword_id = ks.keyword_id
    WHERE ks.run_id = :run_id
    ORDER BY ks.rank_no ASC
    LIMIT 10;
    """
    return pd.read_sql(text(q), engine, params={"run_id": run_id})

@st.cache_data(ttl=60)
def load_trend_series_7d(run_id: int, keyword_id: int):
    # 최근 7일(google/naver 합쳐서 최대 14행) 가져온 후 날짜 오름차순 정렬
    q = """
    SELECT
        ts.d AS "날짜",
        ts.value AS "검색량",
        CASE
            WHEN lower(ts.source) = 'google' THEN 'Google'
            WHEN lower(ts.source) = 'naver'  THEN 'Naver'
            ELSE ts.source
        END AS "플랫폼"
    FROM trend_series ts
    WHERE ts.run_id = :run_id
      AND ts.keyword_id = :keyword_id
    ORDER BY ts.d DESC
    LIMIT 14;
    """
    df = pd.read_sql(text(q), engine, params={"run_id": run_id, "keyword_id": keyword_id})
    if df.empty:
        return df
    df = df.sort_values(["날짜", "플랫폼"], ascending=[True, True]).reset_index(drop=True)
    return df

@st.cache_data(ttl=60)
def load_news_top3_latest(run_id: int, keyword_id: int):
    q = """
    SELECT title, url, publisher, published_at
    FROM news_article
    WHERE run_id = :run_id
      AND keyword_id = :keyword_id
    ORDER BY published_at DESC NULLS LAST, collected_at DESC
    LIMIT 3;
    """
    return pd.read_sql(text(q), engine, params={"run_id": run_id, "keyword_id": keyword_id})

@st.cache_data(ttl=60)
def load_youtube_top3_by_views(run_id: int, keyword_id: int):
    q = """
    SELECT title, channel_title, youtube_id, view_count, published_at
    FROM youtube_video
    WHERE run_id = :run_id
      AND keyword_id = :keyword_id
    ORDER BY view_count DESC NULLS LAST, published_at DESC
    LIMIT 3;
    """
    return pd.read_sql(text(q), engine, params={"run_id": run_id, "keyword_id": keyword_id})

def infer_trend_badge(top10_df: pd.DataFrame, keyword_id: int):
    """
    네 스키마에 up/down/new가 없어서 임시 규칙:
    peak_time_index 상위3=up, 하위3=down, 나머지=new
    """
    s = top10_df.sort_values("peak_time_index", ascending=False).reset_index(drop=True)
    pos = int(s.index[s["keyword_id"] == keyword_id][0]) + 1
    if pos <= 3:
        return "up"
    if pos >= 8:
        return "down"
    return "new"

# -----------------------
# 4. 사이드바: 카테고리 선택 (DB 기반)
# -----------------------
st.sidebar.title("Peak-Time")

cats = load_categories()
if cats.empty:
    st.warning("category 테이블이 비어있습니다. 시드 데이터부터 넣어주세요.")
    st.stop()

selected_cat_name = st.sidebar.selectbox("카테고리 선택", cats["name_ko"].tolist())
selected_cat = cats[cats["name_ko"] == selected_cat_name].iloc[0]
category_id = int(selected_cat["category_id"])

# 최신 run 찾기
run_id = load_latest_run_id(category_id=category_id, country_code="KR", is_dummy=False)
if not run_id:
    st.warning("해당 카테고리에 collection_run(최신, KR, is_dummy=false)이 없습니다.")
    st.stop()

# 3. 화면 분할 (1:2 비율)
left_col, right_col = st.columns([1, 2])

# 2. 좌측 패널 (TOP 10 리스트)
with left_col:
    st.subheader(f"🔥 {selected_cat_name} TOP 10")

    top10 = load_top10(run_id)
    if top10.empty:
        st.warning("keyword_score 데이터가 없습니다.")
        st.stop()

    for _, row in top10.iterrows():
        i = int(row["rank_no"])
        kw_id = int(row["keyword_id"])
        kw_text = row["keyword_text"]

        rank_col, btn_col, trend_col = st.columns([0.15, 0.65, 0.2])

        # 1) 순위 숫자 꾸미기
        rank_color = "#4285F4" if i <= 3 else "#A0C3FF"
        with rank_col:
            st.markdown(
                f'<div style="color: {rank_color}; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">{i}</div>',
                unsafe_allow_html=True
            )

        # 2) 키워드 버튼
        with btn_col:
            if st.button(kw_text, key=f"kw_{kw_id}", use_container_width=True):
                st.session_state.selected_keyword_id = kw_id
                st.session_state.selected_keyword_text = kw_text
                st.rerun()

        # 3) 트렌드 아이콘 꾸미기 (임시 배지)
        with trend_col:
            trend = infer_trend_badge(top10, kw_id)
            if trend == "up":
                trend_html = '<div style="color: #D93025; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↑</div>'
            elif trend == "down":
                trend_html = '<div style="color: #1A73E8; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↓</div>'
            else:
                trend_html = '<div style="color: #D93025; font-size: 12px; font-weight: bold; text-align: center; padding-top: 12px;">NEW</div>'
            st.markdown(trend_html, unsafe_allow_html=True)

# 1. 우측 패널 (심층 분석 뷰)
with right_col:
    if st.session_state.selected_keyword_id:
        kw_id = st.session_state.selected_keyword_id
        kw_text = st.session_state.selected_keyword_text

        st.subheader(f"🔍 '{kw_text}' 심층 분석")

        # 상단: 구글 vs 네이버 7일 검색량 비교 라인 차트
        df = load_trend_series_7d(run_id, kw_id)
        if df.empty:
            st.info("trend_series 데이터가 없습니다.")
        else:
            fig = px.line(
                df,
                x="날짜",
                y="검색량",
                color="플랫폼",
                title="최근 7일 검색 트렌드 비교",
                markers=True,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        # 하단: 관련 뉴스 및 유튜브 반응 (TOP3)
        news_col, youtube_col = st.columns(2)

        with news_col:
            st.info("📰 관련 뉴스 (최신 TOP3)")
            news_df = load_news_top3_latest(run_id, kw_id)
            if news_df.empty:
                st.write("관련 뉴스가 없습니다.")
            else:
                for idx, n in news_df.iterrows():
                    pub = n["publisher"] if pd.notna(n["publisher"]) else ""
                    dt = n["published_at"]
                    dt_txt = dt.strftime("%Y-%m-%d %H:%M") if pd.notna(dt) else ""
                    st.write(f"**{idx+1}. [{pub}] {n['title']}**")
                    if dt_txt:
                        st.caption(f"발행: {dt_txt}")
                    st.write(n["url"])

        with youtube_col:
            st.error("🎥 유튜브 반응 (조회수 TOP3 비교)")
            yt_df = load_youtube_top3_by_views(run_id, kw_id)
            if yt_df.empty:
                st.write("관련 유튜브 영상이 없습니다.")
            else:
                yt_df["view_count"] = yt_df["view_count"].fillna(0).astype(int)
                top1_views = int(yt_df["view_count"].max()) or 1

                for idx, y in yt_df.iterrows():
                    views = int(y["view_count"])
                    ratio = views / top1_views

                    st.write(f"**{idx+1}. {y['title']}**")
                    st.caption(f"{y['channel_title']} · 조회수 {views:,} · TOP1 대비 {ratio:.0%}")
                    st.progress(min(max(ratio, 0.0), 1.0))

                    if pd.notna(y["youtube_id"]):
                        st.write(f"https://www.youtube.com/watch?v={y['youtube_id']}")
    else:
        st.write("👈 분석할 키워드를 좌측 리스트에서 선택해주세요.")