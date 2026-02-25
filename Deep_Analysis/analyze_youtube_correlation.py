import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ⚠️ 한글 폰트 설정 (윈도우: 'Malgun Gothic', 맥: 'AppleGothic')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 카테고리 매핑 딕셔너리
category_map = {
    'climate': '기후',
    'entertainment': '엔터테인먼트',
    'finance': '비즈니스 및 금융',
    'sports': '스포츠'
}

print("🎥 [유튜브 vs 검색 트렌드] 상관관계 심층 분석을 시작합니다...\n")
os.makedirs('result/visualize', exist_ok=True)

try:
    all_trend_data = []
    
    # 1. 4개 카테고리의 트렌드 데이터(total_score 포함) 모두 불러오기
    for eng_cat, kor_cat in category_map.items():
        df = pd.read_csv(f'data/news/trend_with_news_{eng_cat}.csv')
        df['category'] = kor_cat # 병합을 위해 카테고리 이름 맞추기
        df = df.rename(columns={'rank_title': 'keyword'}) # 컬럼명 통일
        all_trend_data.append(df)
        
    df_trend_all = pd.concat(all_trend_data, ignore_index=True)

    # 2. 방금 생성한 유튜브 평균 데이터 로드
    df_yt_avg = pd.read_csv('data/youtube/youtube_keyword_average.csv')

    # 3. 데이터 병합 (category와 keyword가 일치하는 행끼리 연결)
    df_merged = pd.merge(df_trend_all, df_yt_avg, on=['category', 'keyword'], how='inner')
    
    # 분석 결과를 CSV로 저장
    df_merged.to_csv('data/youtube/trend_vs_youtube_merged.csv', index=False, encoding='utf-8-sig')

    # 4. 상관관계(Correlation) 계산
    corr_cols = ['total_score', 'avg_view_count', 'avg_like_count', 'avg_comment_count']
    corr_matrix = df_merged[corr_cols].corr()
    
    print("📈 [상관계수 도출 결과]")
    print(f"- 조회수와의 상관관계: {corr_matrix.loc['total_score', 'avg_view_count']:.2f}")
    print(f"- 좋아요와의 상관관계: {corr_matrix.loc['total_score', 'avg_like_count']:.2f}")
    print(f"- 댓글수와의 상관관계: {corr_matrix.loc['total_score', 'avg_comment_count']:.2f}")

    # ==========================================
    # 🎨 시각화 1: 지표별 다중 산점도 (1 x 3 배열)
    # ==========================================
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # (1) Total Score vs 평균 조회수
    sns.regplot(data=df_merged, x='total_score', y='avg_view_count', ax=axes[0], color='blue', scatter_kws={'alpha':0.6})
    axes[0].set_title(f"Total Score vs 평균 조회수\n(상관계수: {corr_matrix.loc['total_score', 'avg_view_count']:.2f})")
    
    # (2) Total Score vs 평균 좋아요
    sns.regplot(data=df_merged, x='total_score', y='avg_like_count', ax=axes[1], color='red', scatter_kws={'alpha':0.6})
    axes[1].set_title(f"Total Score vs 평균 좋아요\n(상관계수: {corr_matrix.loc['total_score', 'avg_like_count']:.2f})")
    
    # (3) Total Score vs 평균 댓글
    sns.regplot(data=df_merged, x='total_score', y='avg_comment_count', ax=axes[2], color='green', scatter_kws={'alpha':0.6})
    axes[2].set_title(f"Total Score vs 평균 댓글 수\n(상관계수: {corr_matrix.loc['total_score', 'avg_comment_count']:.2f})")
    
    for ax in axes:
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_xlabel('통합 트렌드 점수 (Total Score)')
        
    plt.tight_layout()
    plt.savefig('result/visualize/youtube_correlation_scatter.png', dpi=300)
    plt.close()

    # ==========================================
    # 🎨 시각화 2: 상관관계 히트맵 (Heatmap)
    # ==========================================
    plt.figure(figsize=(8, 6))
    # 한글화를 위해 컬럼명 변경 (그래프용)
    heatmap_data = corr_matrix.rename(columns={'total_score':'트렌드 점수', 'avg_view_count':'조회수', 'avg_like_count':'좋아요', 'avg_comment_count':'댓글'}, 
                                      index={'total_score':'트렌드 점수', 'avg_view_count':'조회수', 'avg_like_count':'좋아요', 'avg_comment_count':'댓글'})
                                      
    sns.heatmap(heatmap_data, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1, linewidths=0.5)
    plt.title('트렌드 점수와 유튜브 지표 간의 상관관계 히트맵', fontsize=14, weight='bold', pad=15)
    
    plt.tight_layout()
    plt.savefig('result/visualize/youtube_correlation_heatmap.png', dpi=300)
    plt.close()

    print("\n✅ 시각화 완료! (youtube_correlation_scatter.png, youtube_correlation_heatmap.png 생성)")

except FileNotFoundError as e:
    print(f"❌ 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    print(f"❌ 에러 발생: {e}")