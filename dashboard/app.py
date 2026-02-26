import os
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# =================================================
# 기본 설정 및 커스텀 CSS
# =================================================
load_dotenv()
st.set_page_config(layout="wide", page_title="Peak-Time Dashboard")

# [CSS 주입] Metric 증감 색상을 파란색(구글 스타일)으로 강제 변경
st.markdown("""
<style>
/* st.metric의 델타(증감) 영역 텍스트 및 배경색을 구글 파란색으로 변경 */
[data-testid="stMetricDelta"] > div {
    color: #4285F4 !important;
    background-color: #E8F0FE !important;
}
/* 델타 영역의 화살표(아이콘) 색상 변경 */
[data-testid="stMetricDelta"] svg {
    fill: #4285F4 !important;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "selected_keyword" not in st.session_state:
    st.session_state.selected_keyword = None

# =================================================
# 유틸
# =================================================
def safe_float(x, default=0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, float) and np.isnan(x):
            return default
        return float(x)
    except Exception:
        return default

def safe_int(x, default=0) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, float) and np.isnan(x):
            return default
        return int(float(x))
    except Exception:
        return default

def tidy_plotly(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155"),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2E8F0")
    return fig

def get_trend_icon(rank):
    """DB에 트렌드 지표가 없을 경우 순위 기반으로 임의 할당하는 함수"""
    if rank <= 3:
        return '<div style="color: #D93025; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↑</div>'
    elif rank >= 8:
        return '<div style="color: #1A73E8; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↓</div>'
    else:
        return '<div style="color: #D93025; font-size: 12px; font-weight: bold; text-align: center; padding-top: 12px;">NEW</div>'

# =================================================
# DB 연결
# =================================================
@st.cache_resource
def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        st.error("DATABASE_URL 환경변수가 설정되어 있지 않습니다.")
        st.stop()

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return create_engine(url, pool_pre_ping=True)

engine = get_engine()

# =================================================
# 데이터 쿼리
# =================================================
@st.cache_data(ttl=60)
def get_latest_run_id(category_code: str):
    q = """
    SELECT cr.run_id
    FROM collection_run cr
    JOIN category c ON cr.category_id = c.category_id
    WHERE c.code = :code
    ORDER BY cr.created_at DESC
    LIMIT 1
    """
    with engine.connect() as conn:
        return conn.execute(text(q), {"code": category_code}).scalar()

@st.cache_data(ttl=60)
def get_top10(run_id: int) -> pd.DataFrame:
    q = """
    SELECT
        ks.rank_no, k.keyword_id, k.keyword_text,
        ks.google_volume_text, ks.volume_score, ks.momentum_score,
        ks.platform_label, ks.quadrant_label, ks.ocean_label,
        ks.youtube_avg_views, ks.youtube_avg_likes, ks.youtube_avg_comments,
        ks.youtube_engagement_rate, ks.youtube_temp_label
    FROM keyword_score ks
    JOIN keyword k ON k.keyword_id = ks.keyword_id
    WHERE ks.run_id = :run_id
    ORDER BY ks.rank_no ASC
    LIMIT 10
    """
    with engine.connect() as conn:
        return pd.read_sql(text(q), conn, params={"run_id": int(run_id)})

@st.cache_data(ttl=60)
def get_naver_series(run_id: int, keyword_id: int) -> pd.DataFrame:
    q = """
    SELECT d, value
    FROM trend_series
    WHERE run_id = :run_id
      AND keyword_id = :keyword_id
      AND source = 'naver'
    ORDER BY d ASC
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(q),
            conn,
            params={"run_id": int(run_id), "keyword_id": int(keyword_id)},
        )

@st.cache_data(ttl=60)
def get_ocean_data(run_id: int) -> pd.DataFrame:
    q = """
    SELECT k.keyword_text, ks.volume_score, ks.momentum_score, ks.platform_label
    FROM keyword_score ks
    JOIN keyword k ON k.keyword_id = ks.keyword_id
    WHERE ks.run_id = :run_id
    """
    with engine.connect() as conn:
        return pd.read_sql(text(q), conn, params={"run_id": int(run_id)})

@st.cache_data(ttl=60)
def get_youtube(run_id: int, keyword_id: int) -> pd.DataFrame:
    q = """
    SELECT title, url, thumbnail_url as image_url, view_count, like_count
    FROM youtube_video
    WHERE run_id = :run_id
      AND keyword_id = :keyword_id
    ORDER BY rank_no ASC
    LIMIT 5
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(q),
            conn,
            params={"run_id": int(run_id), "keyword_id": int(keyword_id)},
        )

@st.cache_data(ttl=60)
def get_news(run_id: int, keyword_id: int) -> pd.DataFrame:
    # 💡 뉴스 테이블에서 image_url 컬럼을 함께 가져오도록 수정되었습니다.
    q = """
    SELECT title, url, image_url
    FROM news_article
    WHERE run_id = :run_id
      AND keyword_id = :keyword_id
    ORDER BY article_id DESC
    LIMIT 5
    """
    with engine.connect() as conn:
        return pd.read_sql(
            text(q),
            conn,
            params={"run_id": int(run_id), "keyword_id": int(keyword_id)},
        )

# =================================================
# 사이드바
# =================================================
st.sidebar.title("Peak-Time")

category_map = {
    "스포츠": "sports",
    "기후": "climate",
    "엔터테인먼트": "entertainment",
    "비즈니스·금융": "finance_business",
}
selected_category = st.sidebar.selectbox("카테고리 선택", list(category_map.keys()))

run_id = get_latest_run_id(category_map[selected_category])
if not run_id:
    st.warning("최신 데이터를 찾지 못했습니다.")
    st.stop()

df_top10 = get_top10(int(run_id))
if df_top10.empty:
    st.warning("TOP10 데이터가 없습니다.")
    st.stop()

if (
    "selected_keyword" not in st.session_state
    or st.session_state.selected_keyword not in df_top10["keyword_text"].values
):
    st.session_state.selected_keyword = df_top10.iloc[0]["keyword_text"]

# =================================================
# 메인 레이아웃 (1:2 비율)
# =================================================
selected_row = df_top10.loc[df_top10["keyword_text"] == st.session_state.selected_keyword].iloc[0]
keyword_id = safe_int(selected_row["keyword_id"])

left_col, right_col = st.columns([1, 2], gap="large")

# -------------------------------------------------
# 1. 좌측 패널 (TOP 10 리스트)
# -------------------------------------------------
with left_col:
    st.subheader(f"🔥 {selected_category} TOP 10")
    
    for _, row in df_top10.iterrows():
        rank_no = int(row["rank_no"])
        kw = row["keyword_text"]
        
        # 레이아웃 비율: 순위(0.15), 버튼(0.65), 트렌드 아이콘(0.2)
        rank_c, btn_c, trend_c = st.columns([0.15, 0.65, 0.2])
        
        # 1) 순위 숫자 꾸미기
        rank_color = "#4285F4" if rank_no <= 3 else "#A0C3FF"
        with rank_c:
            st.markdown(
                f'<div style="color: {rank_color}; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">{rank_no}</div>', 
                unsafe_allow_html=True
            )
            
        # 2) 키워드 버튼
        with btn_c:
            if st.button(kw, key=f"kw_{rank_no}", use_container_width=True):
                st.session_state.selected_keyword = kw
                st.rerun()
                
        # 3) 트렌드 아이콘 꾸미기
        with trend_c:
            st.markdown(get_trend_icon(rank_no), unsafe_allow_html=True)

# -------------------------------------------------
# 2. 우측 패널 (심층 분석 뷰)
# -------------------------------------------------
with right_col:
    st.subheader(f"🔍 '{st.session_state.selected_keyword}' 심층 분석")
    
    # 상단: 구글 지표 (규모 & 폭발력만 표시)
    st.markdown("##### 🔵 Google 검색 반응") 
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        vol_val = str(selected_row.get("google_volume_text", "-"))
        st.metric(label="총 검색량 (Volume)", value=vol_val, delta="안정적 규모 유지")
    with g_col2:
        mom_val = f"{safe_float(selected_row.get('momentum_score')):.0f}%"
        st.metric(label="급상승 비율 (Momentum)", value=mom_val, delta="Breakout (폭발적 상승)")
        
    st.divider()

    # 중단: 네이버 검색 흐름
    st.markdown("##### 🟢 Naver 검색 흐름")
    df_series = get_naver_series(int(run_id), int(keyword_id))
    
    if df_series.empty or df_series["value"].isnull().all():
        st.info("Naver 일간 검색량 데이터가 없습니다.")
    else:
        fig_line = px.line(df_series, x="d", y="value", title="최근 7일 네이버 상대적 검색 추이",
                           markers=True, color_discrete_sequence=["#2DB400"])
        fig_line.update_traces(marker=dict(size=8, color="#2DB400"), line=dict(width=3))
        fig_line.update_layout(xaxis_title="날짜", yaxis_title="검색량")
        st.plotly_chart(tidy_plotly(fig_line), use_container_width=True)
    
    st.divider()
    
    # ==========================================================
    # 하단: 관련 뉴스 & 오션맵 vs 유튜브 반응 & 핵심지표 
    # ==========================================================
    
    # --- 1행: 섹션 헤더 ---
    h_col1, h_col2 = st.columns(2, gap="large")
    with h_col1:
        st.info("📰 관련 뉴스 & 전략 분석")
    with h_col2:
        st.error("🎥 유튜브 반응 & 지표")
        
    # --- 2행: 분석 차트 & 핵심 지표 ---
    c_col1, c_col2 = st.columns(2, gap="large")
    
    with c_col1:
        st.markdown("###### 🌊 오션 전략 분석")
        df_ocean = get_ocean_data(int(run_id))
        if not df_ocean.empty:
            df_ocean["size_score"] = df_ocean["volume_score"].clip(lower=1)
            fig_ocean = px.scatter(
                df_ocean, x="volume_score", y="momentum_score",
                hover_name="keyword_text", size="size_score", color="platform_label"
            )
            fig_ocean.update_traces(marker=dict(opacity=0.85))
            fig_ocean.update_layout(height=320, margin=dict(t=20, b=10, l=10, r=10))
            st.plotly_chart(tidy_plotly(fig_ocean), use_container_width=True)

    with c_col2:
        st.markdown("###### 📺 유튜브 핵심 지표")
        st.markdown("<div style='text-align: center; color: #555; font-size: 16px; font-weight: bold; margin-top: 10px; margin-bottom: -10px;'>평균 참여율</div>", unsafe_allow_html=True)
        
        yt_rate = safe_float(selected_row.get("youtube_engagement_rate", 0), 0)
        yt_views = safe_int(selected_row.get("youtube_avg_views", 0), 0)
        yt_likes = safe_int(selected_row.get("youtube_avg_likes", 0), 0)
        yt_comments = safe_int(selected_row.get("youtube_avg_comments", 0), 0) 

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=yt_rate, number={"suffix": "%"},
            gauge={"axis": {"range": [0, max(20, yt_rate+5)]}, "bar": {"color": "#EF4444"}}
        ))
        fig_gauge.update_layout(height=180, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

        k1, k2, k3 = st.columns(3)
        k1.metric("평균 조회수", f"{yt_views:,}")
        k2.metric("평균 좋아요", f"{yt_likes:,}")
        k3.metric("평균 댓글 수", f"{yt_comments:,}")

    st.write("")

    # --- 3행: 관련 기사 및 영상 리스트 (썸네일 이미지 포함, 제목 짤림 방지) ---
    st.write("")

    l_col1, l_col2 = st.columns(2, gap="large")
    with l_col1:
        st.markdown("###### 📰 관련 기사")
    with l_col2:
        st.markdown("###### 🎥 관련 영상")

    news_df = get_news(int(run_id), int(keyword_id))
    yt_df = get_youtube(int(run_id), int(keyword_id))

    news_list = news_df.head(3).to_dict('records') if not news_df.empty else []
    yt_list = yt_df.head(3).to_dict('records') if not yt_df.empty else []

    max_items = max(len(news_list), len(yt_list))

    if max_items == 0:
        st.info("수집된 기사 및 영상이 없습니다.")
    else:
        for i in range(max_items):
            r_col1, r_col2 = st.columns(2, gap="large")
            
            # 왼쪽: 기사
            with r_col1:
                if i < len(news_list):
                    n_item = news_list[i]
                    title = str(n_item.get("title", ""))
                    url = str(n_item.get("url", "#") or "#")
                    
                    news_image = str(n_item.get("image_url", "https://via.placeholder.com/90x68?text=News"))
                    if not news_image or news_image == "None":
                        news_image = "https://via.placeholder.com/90x68?text=News"
                    
                    # 제목 전체 표시 (말줄임표 제거, 최소 높이 지정)
                    news_html = f"""
                    <div style='display: flex; align-items: flex-start; margin-bottom: 15px; min-height: 68px;'>
                        <img src='{news_image}' style='width: 90px; height: 68px; object-fit: cover; border-radius: 8px; margin-right: 15px; border: 1px solid #f3f4f6; flex-shrink: 0;' onerror="this.src='https://via.placeholder.com/90x68?text=News'"/>
                        <div style='flex: 1; display: flex; flex-direction: column; min-height: 68px;'>
                            <div style='font-size: 14px; font-weight: 500; line-height: 1.4; color: #333; margin-bottom: 8px;'>{title}</div>
                            <div style='display: flex; justify-content: flex-end; margin-top: auto;'>
                                <a href='{url}' target='_blank' style='text-decoration:none; font-size:12px; padding:3px 10px; border:1px solid #d1d5db; border-radius:4px; color:#374151; background-color:#f9fafb; font-weight: 500;'>기사 열기</a>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(news_html, unsafe_allow_html=True)
                
            # 오른쪽: 영상
            with r_col2:
                if i < len(yt_list):
                    y_item = yt_list[i]
                    title = str(y_item.get("title", ""))
                    url = str(y_item.get("url", "#") or "#")
                    views = safe_int(y_item.get("view_count", 0))
                    likes = safe_int(y_item.get("like_count", 0))
                    
                    image_url = str(y_item.get("image_url", "https://via.placeholder.com/120x68?text=Video"))
                    if not image_url or image_url == "None":
                        image_url = "https://via.placeholder.com/120x68?text=Video"
                    
                    # 제목 전체 표시 (말줄임표 제거, 최소 높이 지정)
                    yt_html = f"""
                    <div style='display: flex; align-items: flex-start; margin-bottom: 15px; min-height: 68px;'>
                        <img src='{image_url}' style='width: 120px; height: 68px; object-fit: cover; border-radius: 8px; margin-right: 15px; border: 1px solid #f3f4f6; flex-shrink: 0;' onerror="this.src='https://via.placeholder.com/120x68?text=Video'"/>
                        <div style='flex: 1; display: flex; flex-direction: column; min-height: 68px;'>
                            <div style='font-size: 14px; font-weight: 500; line-height: 1.4; color: #333; margin-bottom: 8px;'>{title}</div>
                            <div style='font-size: 12px; color: #6b7280; display: flex; justify-content: space-between; align-items: center; margin-top: auto;'>
                                <span>👀 {views:,}회 · 👍 {likes:,}개</span>
                                <a href='{url}' target='_blank' style='margin-left: 12px; text-decoration:none; font-size:12px; padding:3px 10px; border:1px solid #e5e7eb; border-radius:4px; color:#1a73e8; background-color:#eff6ff; white-space: nowrap; font-weight: 500;'>영상 보기</a>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(yt_html, unsafe_allow_html=True)
            
            # 아이템 사이 구분선 (마지막 항목 제외)
            if i < max_items - 1:
                st.markdown("<hr style='margin: 0px 0px 15px 0px; border: 0; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)