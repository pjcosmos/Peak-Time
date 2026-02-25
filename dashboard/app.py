import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# 5. 페이지 설정
st.set_page_config(layout="wide", page_title="Peak-Time Trend Dashboard")

# -------------------------------------------------------------------
# [신규 추가] 커스텀 CSS (Metric 증감 색상을 파란색으로 강제 변경)
# -------------------------------------------------------------------
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

# 더미 데이터 생성 함수 (트렌드 상태 추가: 'up', 'down', 'new')
def get_dummy_keywords(category):
    keywords = {
        "비즈니스·금융": [("삼성전자", "up"), ("엔비디아", "up"), ("비트코인", "down"), ("금리 인상", "up"), ("K-뷰티", "new"), 
                   ("친환경 에너지", "up"), ("스타트업", "down"), ("나스닥", "up"), ("부동산 시장", "up"), ("환율", "down")],
        "스포츠": [("손흥민", "up"), ("이강인", "up"), ("K리그", "down"), ("메이저리그", "up"), ("챔피언스리그", "new"), 
                 ("파리 올림픽", "up"), ("프로야구", "up"), ("농구 월드컵", "down"), ("테니스", "up"), ("골프", "new")],
        "엔터테인먼트": [("뉴진스", "up"), ("BTS", "up"), ("아이브", "down"), ("오징어 게임 2", "up"), ("칸 영화제", "new"), 
                    ("신곡 발매", "up"), ("웹툰 원작 드라마", "up"), ("K-팝", "down"), ("넷플릭스", "up"), ("유튜브 트렌드", "new")],
        "기후": [("탄소 중립", "up"), ("엘니뇨", "up"), ("이상 기후", "down"), ("재생 에너지", "up"), ("미세먼지", "new"), 
                ("폭염 경보", "up"), ("해수면 상승", "down"), ("전기차", "up"), ("플라스틱 프리", "up"), ("생태계 보호", "new")]
    }
    return keywords.get(category, [])

# 네이버 전용 더미 차트 데이터 (구글 제외)
def get_dummy_naver_chart_data():
    dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    data = {
        "날짜": dates,
        "검색량": [10, 35, 20, 55, 60, 45, 90], # 임의의 우상향 흐름
        "플랫폼": ["Naver"] * 7
    }
    return pd.DataFrame(data)

# 4. 사이드바: 카테고리 선택
st.sidebar.title("Peak-Time")
category = st.sidebar.selectbox(
    "카테고리 선택",
    ["비즈니스·금융", "스포츠", "엔터테인먼트", "기후"]
)

# 3. 화면 분할 (1:2 비율)
left_col, right_col = st.columns([1, 2])

# 2. 좌측 패널 (TOP 10 리스트)
with left_col:
    st.subheader(f"🔥 {category} TOP 10")
    keywords_data = get_dummy_keywords(category)
    
    for i, (kw, trend) in enumerate(keywords_data, 1):
        # 레이아웃 비율: 순위(0.15), 버튼(0.65), 트렌드 아이콘(0.2)
        rank_col, btn_col, trend_col = st.columns([0.15, 0.65, 0.2])
        
        # 1) 순위 숫자 꾸미기 (1~3위는 파란색, 나머지는 옅은 파란색)
        rank_color = "#4285F4" if i <= 3 else "#A0C3FF"
        with rank_col:
            st.markdown(
                f'<div style="color: {rank_color}; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">{i}</div>', 
                unsafe_allow_html=True
            )
            
        # 2) 키워드 버튼
        with btn_col:
            if st.button(kw, key=f"kw_{i}", use_container_width=True):
                st.session_state.selected_keyword = kw
                st.rerun()
                
        # 3) 트렌드 아이콘 꾸미기
        with trend_col:
            if trend == "up":
                trend_html = '<div style="color: #D93025; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↑</div>'
            elif trend == "down":
                trend_html = '<div style="color: #1A73E8; font-size: 18px; font-weight: bold; text-align: center; padding-top: 8px;">↓</div>'
            else: # new
                trend_html = '<div style="color: #D93025; font-size: 12px; font-weight: bold; text-align: center; padding-top: 12px;">NEW</div>'
            
            st.markdown(trend_html, unsafe_allow_html=True)

# 1. 우측 패널 (심층 분석 뷰)
with right_col:
    if st.session_state.selected_keyword:
        st.subheader(f"🔍 '{st.session_state.selected_keyword}' 심층 분석")
        
        # 상단: 구글 지표 (규모 & 폭발력) - Metric Card 활용
        st.markdown("##### 🔵 Google 검색 반응") 
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.metric(label="총 검색량 (Volume)", value="10만+", delta="안정적 규모 유지")
        with g_col2:
            st.metric(label="급상승 비율 (Momentum)", value="400%", delta="Breakout (폭발적 상승)")
            
        st.divider()

        # 중단: 네이버 지표 (시계열 흐름) - Line Chart 활용
        st.markdown("##### 🟢 Naver 검색 흐름")
        df = get_dummy_naver_chart_data()
        fig = px.line(df, x="날짜", y="검색량", title="최근 7일 네이버 상대적 검색 추이",
                      markers=True, template="plotly_white", color_discrete_sequence=["#2DB400"])
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # 하단: 관련 뉴스 및 유튜브 반응
        news_col, youtube_col = st.columns(2)
        
        with news_col:
            st.info("📰 관련 뉴스")
            st.write(f"- [구글] {st.session_state.selected_keyword} 관련 최신 동향 분석")
            st.write(f"- [네이버] {st.session_state.selected_keyword} 시장 영향력 확대")
            st.write(f"- [다음] {st.session_state.selected_keyword} 관련 전문가 인터뷰")
            
        with youtube_col:
            st.error("🎥 유튜브 반응")
            st.write(f"- '심층 분석: {st.session_state.selected_keyword}의 진실' (조회수 10만)")
            st.write(f"- '{st.session_state.selected_keyword} 5분 만에 마스터하기' (조회수 5.2만)")
            st.write(f"- '{st.session_state.selected_keyword} 논란의 핵심 정리' (조회수 2.4만)")
    else:
        st.write("👈 분석할 키워드를 좌측 리스트에서 선택해주세요.")