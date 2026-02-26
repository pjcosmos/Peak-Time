import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# ⚠️ 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

print("🌡️ [카테고리별 유튜브 찐팬 온도계] 데이터 생성을 시작합니다...\n")

os.makedirs('result/', exist_ok=True)
os.makedirs('result/youtube_thermometer', exist_ok=True)

# 영문-한글 카테고리 매핑
category_map = {
    '기후': 'climate',
    '엔터테인먼트': 'entertainment',
    '비즈니스 및 금융': 'finance',
    '스포츠': 'sports'
}

# 온도별 막대 색상 지정
color_map = {
    '🔥 펄펄 끓는 찐팬': '#ff4d4d',   # 빨간색
    '♨️ 훈훈한 호감': '#ffa64d',     # 주황색
    '🍃 가벼운 관심': '#66cc66',     # 초록색
    '🧊 조회수 위주': '#66b3ff'      # 파란색
}

try:
    # 1. 유튜브 평균 데이터 로드
    df = pd.read_csv('data/youtube/youtube_keyword_average.csv')
    df = df[df['avg_view_count'] > 0].copy()

    # 2. 찐팬 지수 (Engagement Rate) 계산
    df['engagement_rate'] = ((df['avg_like_count'] + df['avg_comment_count']) / df['avg_view_count']) * 100
    df['engagement_rate'] = df['engagement_rate'].round(2)

    # 3. 온도 분류 함수
    def get_temperature(rate):
        if rate >= 3.0: return '🔥 펄펄 끓는 찐팬'
        elif rate >= 1.5: return '♨️ 훈훈한 호감'
        elif rate >= 0.5: return '🍃 가벼운 관심'
        else: return '🧊 조회수 위주'

    df['temperature_status'] = df['engagement_rate'].apply(get_temperature)

    # 전체 데이터 API로도 하나 저장해 둡니다 (프론트엔드 선택용)
    df_all_sorted = df.sort_values(by='engagement_rate', ascending=False)
    df_all_sorted.to_dict(orient='records')
    with open('result/youtube_thermometer/youtube_engagement_all.json', 'w', encoding='utf-8') as f:
        json.dump(df_all_sorted.to_dict(orient='records'), f, ensure_ascii=False, indent=4)

    # 4. 카테고리별로 반복하면서 JSON 및 시각화 파일 생성
    for kor_cat, eng_cat in category_map.items():
        # 해당 카테고리 데이터만 필터링 및 정렬
        df_cat = df[df['category'] == kor_cat].copy()
        df_cat = df_cat.sort_values(by='engagement_rate', ascending=False)
        
        # [데이터 저장] 카테고리별 JSON 및 CSV 저장
        cols = ['keyword', 'avg_view_count', 'avg_like_count', 'avg_comment_count', 'engagement_rate', 'temperature_status']
        df_cat_web = df_cat[cols].copy()
        
        df_cat_web.to_csv(f'result/youtube_thermometer/youtube_engagement_{eng_cat}.csv', index=False, encoding='utf-8-sig')
        with open(f'result/youtube_thermometer/youtube_engagement_{eng_cat}.json', 'w', encoding='utf-8') as f:
            json.dump(df_cat_web.to_dict(orient='records'), f, ensure_ascii=False, indent=4)
        
        # [시각화 생성]
        bar_colors = [color_map[temp] for temp in df_cat['temperature_status']]

        plt.figure(figsize=(10, 6))
        bars = plt.barh(df_cat['keyword'], df_cat['engagement_rate'], color=bar_colors, edgecolor='white')
        
        # 1위가 위로 가도록 Y축 뒤집기
        plt.gca().invert_yaxis()

        # 막대 끝에 텍스트 (퍼센트 + 이모지)
        for bar, temp in zip(bars, df_cat['temperature_status']):
            width = bar.get_width()
            emoji = temp.split()[0] 
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                     f"{width}% ({emoji})", va='center', fontsize=11, weight='bold', color='#333333')

        plt.title(f'[{kor_cat}] 유튜브 찐팬(인게이지먼트) 온도계', fontsize=16, weight='bold', pad=15)
        plt.xlabel('인게이지먼트 율 (%)', fontsize=12)
        plt.grid(axis='x', linestyle='--', alpha=0.5)

        # 우측 하단 범례 추가
        handles = [plt.Rectangle((0,0),1,1, color=color_map[label]) for label in color_map]
        plt.legend(handles, color_map.keys(), title='온도(반응도)', loc='lower right')

        plt.tight_layout()
        output_png = f'result/youtube_thermometer/youtube_thermometer_{eng_cat}.png'
        plt.savefig(output_png, dpi=300)
        plt.close()
        
        print(f"✅ [{kor_cat}] 온도계 데이터 및 시각화 완료!")

except FileNotFoundError:
    print("❌ 파일을 찾을 수 없습니다: result/youtube/youtube_keyword_average.csv")
except Exception as e:
    print(f"❌ 에러 발생: {e}")

print("\n🎉 모든 카테고리별 찐팬 온도계 모듈 구동 완료!")