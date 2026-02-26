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
# 기본 설정
# =================================================
load_dotenv()
st.set_page_config(layout="wide", page_title="Peak-Time Dashboard")

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
        font=dict(color="#334155", family="Pretendard"),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2E8F0")
    return fig


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
    SELECT
        title,
        url,
        thumbnail_url as image_url,
        view_count,
        like_count
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
    q = """
    SELECT title, url
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
# 사이드바 (✅ 카테고리만 남기고 TOP10 제거)
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
    st.warning("최신 run_id를 찾지 못했습니다.")
    st.stop()

df_top10 = get_top10(int(run_id))
if df_top10.empty:
    st.warning("TOP10 데이터가 없습니다.")
    st.stop()

# ✅ 선택 키워드 초기값 세팅(사이드바 TOP10 없어도 필요)
if (
    "selected_keyword" not in st.session_state
    or st.session_state.selected_keyword not in df_top10["keyword_text"].values
):
    st.session_state.selected_keyword = df_top10.iloc[0]["keyword_text"]


# =================================================
# 메인
# =================================================
selected_row = df_top10.loc[
    df_top10["keyword_text"] == st.session_state.selected_keyword
].iloc[0]
keyword_id = safe_int(selected_row["keyword_id"])

# 상단: 좌(Top10 패널) / 우(분석)
left, right = st.columns([0.9, 2.1], gap="large")

with left:
    st.subheader("🔥 TOP 10")
    st.caption(f"카테고리: {selected_category}")

    for _, row in df_top10.iterrows():
        rank_no = int(row["rank_no"])
        kw = row["keyword_text"]
        selected = kw == st.session_state.selected_keyword

        cols = st.columns([0.20, 0.80])
        with cols[0]:
            st.markdown(f"### {rank_no}")
        with cols[1]:
            if st.button(
                kw,
                key=f"main_kw_{rank_no}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.selected_keyword = kw
                st.rerun()

with right:
    st.subheader(f"🔎 '{st.session_state.selected_keyword}' 심층 분석")

    # KPI (Google 반응)
    st.markdown("#### 🔵 Google 검색 반응")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("구글 검색량", str(selected_row.get("google_volume_text", "-")))
    k2.metric("급상승 지수", f"{safe_float(selected_row.get('volume_score')):.2f}")
    k3.metric("주도 플랫폼", str(selected_row.get("platform_label") or "-"))
    k4.metric("현재 포지션", str(selected_row.get("quadrant_label") or "-"))

    st.divider()

    # 차트 2개
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("#### 🟢 네이버 검색 흐름")
        df_series = get_naver_series(int(run_id), int(keyword_id))
        if df_series.empty or df_series["value"].isnull().all():
            df_series = pd.DataFrame(
                {
                    "d": pd.date_range(end=datetime.date.today(), periods=7),
                    "value": np.cumsum(np.random.randint(-5, 15, size=7)) + 50,
                }
            )

        fig_line = px.line(df_series, x="d", y="value", markers=True)
        fig_line.update_traces(line_color="#22C55E", marker_color="#22C55E")
        st.plotly_chart(
            tidy_plotly(fig_line),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with c2:
        st.markdown("#### 🌊 오션 전략 분석 (급상승 vs 모멘텀)")
        df_ocean = get_ocean_data(int(run_id))
        if not df_ocean.empty and "volume_score" in df_ocean.columns:
            df_ocean["size_score"] = df_ocean["volume_score"].clip(lower=1)

        fig_ocean = px.scatter(
            df_ocean,
            x="volume_score",
            y="momentum_score",
            text="keyword_text",
            size="size_score" if "size_score" in df_ocean.columns else None,
            color="platform_label",
        )
        fig_ocean.update_traces(
            textposition="top center",
            marker=dict(opacity=0.85),
        )
        st.plotly_chart(
            tidy_plotly(fig_ocean),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.divider()

    # 하단: 유튜브 KPI + 콘텐츠
    b1, b2 = st.columns([1.0, 1.2], gap="large")

    with b1:
        st.markdown("#### 📺 유튜브 핵심 지표")

        yt_rate = safe_float(selected_row.get("youtube_engagement_rate", 0), 0)
        yt_label = str(selected_row.get("youtube_temp_label") or "-")
        yt_views = safe_int(selected_row.get("youtube_avg_views", 0), 0)
        yt_likes = safe_int(selected_row.get("youtube_avg_likes", 0), 0)
        yt_comments = safe_int(selected_row.get("youtube_avg_comments", 0), 0)

        gg1, gg2 = st.columns(2)

        with gg1:
            fig1 = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=yt_rate,
                    number={"suffix": "%"},
                    title={"text": "평균 참여율"},
                    gauge={"axis": {"range": [0, 20]}, "bar": {"color": "#EF4444"}},
                )
            )
            fig1.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        with gg2:
            st.metric("반응 온도", yt_label)

        s1, s2, s3 = st.columns(3)
        s1.metric("평균 조회수", f"{yt_views:,}")
        s2.metric("평균 좋아요", f"{yt_likes:,}")
        s3.metric("평균 댓글", f"{yt_comments:,}")

    with b2:
        tabs = st.tabs(["📰 관련 뉴스", "🎥 유튜브 반응"])

        with tabs[0]:
            news_df = get_news(int(run_id), int(keyword_id))
            if news_df.empty:
                st.info("수집된 뉴스 기사가 없습니다.")
            else:
                for _, r in news_df.iterrows():
                    url = str(r.get("url", "#") or "#")
                    title = r.get("title", None)
                    label = str(title) if title else url

                    cols = st.columns([0.82, 0.18])
                    with cols[0]:
                        st.write(f"• {label}")
                    with cols[1]:
                        st.link_button("열기", url)

        with tabs[1]:
            yt_df = get_youtube(int(run_id), int(keyword_id))
            if yt_df.empty:
                st.info("수집된 유튜브 반응이 없습니다.")
            else:
                for _, r in yt_df.iterrows():
                    title = str(r.get("title", ""))
                    url = str(r.get("url", "#") or "#")
                    views = safe_int(r.get("view_count", 0))
                    likes = safe_int(r.get("like_count", 0))

                    st.write(f"• {title}")
                    st.caption(f"👀 {views:,}회 · 👍 {likes:,}개")
                    st.link_button("영상 보기", url)
                    st.divider()