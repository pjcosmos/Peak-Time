import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# ⚠️ 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 파일 경로 및 카테고리 매핑
categories = {
    'climate': '기후',
    'entertainment': '엔터테인먼트',
    'finance': '비즈니스 및 금융',
    'sports': '스포츠'
}

print("🌊 [블루오션 / 레드오션 판별기] 데이터 생성을 시작합니다...\n")

# 결과물 저장 폴더 세팅
os.makedirs('result/web_data', exist_ok=True)
os.makedirs('result/visualize', exist_ok=True)

try:
    all_data = []
    
    # 1. 4개의 뉴스 포함 트렌드 CSV 파일 하나로 병합
    for eng_cat, kor_cat in categories.items():
        df = pd.read_csv(f'data/news/trend_with_news_{eng_cat}.csv')
        df['category'] = kor_cat
        all_data.append(df)
        
    df_all = pd.concat(all_data, ignore_index=True)

    # 2. 기준점(Threshold) 설정: 전체 40개 키워드의 평균값
    score_th = df_all['total_score'].mean()
    news_th = df_all['google_news_count'].mean()
    
    print(f"📊 [판별 기준] 평균 트렌드 점수: {score_th:.1f} / 평균 기사량: {news_th:.1f}")

    # 3. 오션(Ocean) 상태 분류 함수
    def classify_ocean(row):
        if row['total_score'] >= score_th and row['google_news_count'] < news_th:
            return '🔵 블루오션'
        elif row['total_score'] >= score_th and row['google_news_count'] >= news_th:
            return '🔴 레드오션'
        elif row['total_score'] < score_th and row['google_news_count'] >= news_th:
            return '🫧 미디어 버블'
        else:
            return '🏕️ 마이너(잠복기)'

    # 데이터프레임에 판별 결과 컬럼 추가
    df_all['ocean_status'] = df_all.apply(classify_ocean, axis=1)
    
    # 웹사이트에서 쓰기 좋게 컬럼 정리
    cols = ['category', 'rank_title', 'total_score', 'google_news_count', 'ocean_status']
    df_web = df_all[cols].copy()
    
    # 4. 웹 데이터(API용 JSON 및 CSV) 저장
    df_web.to_csv('result/web_data/ocean_discriminator.csv', index=False, encoding='utf-8-sig')
    
    # 프론트엔드가 사랑하는 JSON 형태로 변환
    web_json_data = df_web.to_dict(orient='records')
    with open('result/web_data/ocean_discriminator.json', 'w', encoding='utf-8') as f:
        json.dump(web_json_data, f, ensure_ascii=False, indent=4)
        
    print("✅ 웹사이트 API용 데이터(JSON, CSV) 생성 완료!")

    # =========================================================
    # 5. 블루오션/레드오션 시각화 맵 생성 (웹사이트에 삽입할 이미지)
    # =========================================================
    plt.figure(figsize=(12, 9))
    
    color_map = {
        '🔵 블루오션': '#1E90FF',    # Dodger Blue
        '🔴 레드오션': '#FF4500',    # Orange Red
        '🫧 미디어 버블': '#FFA500', # Orange
        '🏕️ 마이너(잠복기)': '#808080' # Gray
    }
    
    # 그룹별로 색상을 다르게 점 찍기
    for status, color in color_map.items():
        subset = df_web[df_web['ocean_status'] == status]
        plt.scatter(subset['total_score'], subset['google_news_count'], 
                    c=color, label=status, s=150, alpha=0.8, edgecolors='white')

    # 십자선 그리기
    plt.axvline(x=score_th, color='gray', linestyle='--', alpha=0.5)
    plt.axhline(y=news_th, color='gray', linestyle='--', alpha=0.5)

    # 텍스트 라벨 추가 (블루오션이거나, 값이 높은 주요 키워드만)
    for idx, row in df_web.iterrows():
        if row['ocean_status'] == '🔵 블루오션' or row['total_score'] > 45 or row['google_news_count'] > 50:
            plt.text(row['total_score'] + 0.5, row['google_news_count'] + 0.5, row['rank_title'], fontsize=10, weight='bold')

    # 축과 제목
    plt.title('블루오션/레드오션 판별기 (수요 vs 경쟁)', fontsize=16, weight='bold', pad=15)
    plt.xlabel('통합 트렌드 점수 (수요 / 대중 관심도)', fontsize=12)
    plt.ylabel('구글 뉴스 발행 기사 수 (공급 / 언론 경쟁도)', fontsize=12)

    # 각 사분면 모서리에 의미 설명(워터마크) 추가
    plt.text(score_th + 1, news_th - 3, "🔵 블루오션 (기회 영역)", fontsize=14, color='blue', alpha=0.4, ha='left', va='top')
    plt.text(score_th + 1, news_th + 3, "🔴 레드오션 (치열한 경쟁)", fontsize=14, color='red', alpha=0.4, ha='left', va='bottom')
    plt.text(score_th - 1, news_th + 3, "🫧 미디어 버블 (노이즈)", fontsize=14, color='orange', alpha=0.4, ha='right', va='bottom')
    plt.text(score_th - 1, news_th - 3, "🏕️ 마이너 (잠재적 수요)", fontsize=14, color='gray', alpha=0.4, ha='right', va='top')

    plt.legend(title='포스팅 추천도', loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # 이미지 저장
    plt.tight_layout()
    output_png = 'result/visualize/ocean_discriminator.png'
    plt.savefig(output_png, dpi=300)
    plt.close()
    
    print(f"✅ 판별기 시각화 맵 생성 완료! ({output_png})")

except Exception as e:
    print(f"❌ 에러 발생: {e}")

print("\n🎉 블루오션 분석 모듈 구동 완료!")