import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('result', exist_ok=True)
os.makedirs('result/news_correlation', exist_ok=True)

# ⚠️ 한글 폰트 설정 (윈도우: 'Malgun Gothic', 맥: 'AppleGothic')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 영문 파일명과 한글 카테고리 매핑
categories = {
    'climate': '기후',
    'entertainment': '엔터테인먼트',
    'finance': '비즈니스 및 금융',
    'sports': '스포츠'
}

print("📰 [대중 트렌드 vs 언론 기사량] 상관관계 분석 시각화를 시작합니다...\n")

try:
    all_data = []
    
    # 1. 4개의 CSV 파일을 하나로 합치기
    for eng_cat, kor_cat in categories.items():
        # 방금 생성한 뉴스 포함 CSV 파일 로드
        df = pd.read_csv(f'data/news/trend_with_news_{eng_cat}.csv')
        df['category'] = kor_cat # 그래프에서 카테고리별 색상을 다르게 주기 위함
        all_data.append(df)
        
    # 데이터프레임 병합
    df_all = pd.concat(all_data, ignore_index=True)
    
    # 2. 전체 상관계수(Pearson Correlation) 계산
    correlation = df_all['total_score'].corr(df_all['google_news_count'])
    print(f"📈 전체 상관계수 도출: {correlation:.3f} (0에 가까울수록 관계없음, 1에 가까울수록 정비례)")
    
    # 3. 산점도(Scatter Plot) 시각화 그리기
    plt.figure(figsize=(11, 8))
    
    # 점 찍기
    sns.scatterplot(
        data=df_all, 
        x='total_score',          # X축: 대중의 관심 (트렌드 점수)
        y='google_news_count',    # Y축: 언론의 관심 (뉴스 기사 수)
        hue='category',           # 카테고리별로 색상을 다르게
        s=150,                    # 점 크기
        palette='Set1',
        alpha=0.8,
        edgecolor='white'
    )
    
    # 전체적인 경향성을 보여주는 점선(회귀선) 추가
    sns.regplot(
        data=df_all, 
        x='total_score', 
        y='google_news_count', 
        scatter=False, 
        color='gray', 
        line_kws={"linestyle": "--", "alpha": 0.5}
    )
    
    # 4. 차별화된 인사이트를 위해 텍스트 라벨 달기
    # 모든 글씨를 쓰면 겹치므로, 의미가 큰 데이터(점수 50점 이상 OR 기사 50건 이상)만 표시
    for idx, row in df_all.iterrows():
        if row['total_score'] >= 50 or row['google_news_count'] >= 50:
            plt.text(row['total_score'] + 1, row['google_news_count'] + 0.5, 
                     row['rank_title'], fontsize=10, weight='bold')

    # 축과 제목 설정
    plt.title(f'대중 트렌드(Total Score) vs 언론 보도량(News Count)\n[상관계수: {correlation:.2f}]', fontsize=16, weight='bold', pad=15)
    plt.xlabel('통합 트렌드 점수 (Total Score -> 대중의 관심도)', fontsize=12)
    plt.ylabel('구글 뉴스 발행 기사 수 (News Count -> 언론의 관심도)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # 우측 하단 여백에 범례 설정
    plt.legend(title='카테고리', loc='lower right')
    
    # 저장
    plt.tight_layout()
    output_filename = 'result/news_correlation/correlation_trend_news.png'
    plt.savefig(output_filename, dpi=300)
    plt.close()
    
    print(f"✅ 상관관계 시각화 완료! ({output_filename} 생성)")

except FileNotFoundError as e:
    print(f"❌ 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    print(f"❌ 에러 발생: {e}")