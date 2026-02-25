import json
import pandas as pd
import os

# 영문 카테고리명과 뉴스 JSON 파일의 한글 카테고리명 매핑
category_map = {
    'climate': '기후',
    'entertainment': '엔터테인먼트',
    'finance': '비즈니스 및 금융',
    'sports': '스포츠'
}

print("📰 [뉴스 데이터 전처리] TOP 10 키워드와 뉴스 발행량 매칭을 시작합니다...\n")

# 결과를 저장할 폴더 확인 및 생성
os.makedirs('result', exist_ok=True)

try:
    # 1. 통합 뉴스 JSON 파일 로드
    with open('data/news/google_news_grouped_by_category_keyword.json', 'r', encoding='utf-8') as f:
        news_data = json.load(f)
        
    for eng_cat, kor_cat in category_map.items():
        try:
            # 2. 각 카테고리별 TOP 10 CSV 파일 로드
            df_top10 = pd.read_csv(f'data/raw_data/final_weighted_top10_{eng_cat}.csv')
            
            news_counts = []
            
            # 3. TOP 10 키워드별로 뉴스 기사 수(total_count) 추출
            for keyword in df_top10['rank_title']:
                try:
                    # JSON 구조: 카테고리 -> 키워드 -> total_count -> google
                    count = news_data[kor_cat][keyword]['total_count']['google']
                    news_counts.append(count)
                except KeyError:
                    # JSON 파일에 해당 키워드의 뉴스 데이터가 없는 경우 0으로 처리
                    news_counts.append(0)
                    
            # 4. 기존 데이터프레임에 'google_news_count' 컬럼 추가
            df_top10['google_news_count'] = news_counts
            
            # 5. 뉴스가 결합된 새로운 CSV 파일로 저장
            output_filename = f'data/news/trend_with_news_{eng_cat}.csv'
            df_top10.to_csv(output_filename, index=False, encoding='utf-8-sig')
            
            print(f"✅ [{kor_cat}] 뉴스 데이터 병합 완료! ({output_filename})")
            
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: final_weighted_top10_{eng_cat}.csv")
            
except FileNotFoundError:
    print("❌ 구글 뉴스 JSON 파일을 찾을 수 없습니다: google_news_grouped_by_category_keyword.json")
except Exception as e:
    print(f"❌ 에러 발생: {e}")

print("\n🎉 모든 카테고리의 뉴스 데이터 전처리가 완료되었습니다!")