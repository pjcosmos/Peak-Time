import json
import pandas as pd
import os

os.makedirs('data', exist_ok=True)
os.makedirs('data/youtube', exist_ok=True)

print("🎥 [유튜브 데이터 전처리] 키워드 매핑 및 평균 수치 도출을 시작합니다...\n")

try:
    # =====================================================================
    # 1단계: 뉴스 JSON 파일에서 카테고리/키워드 매핑 정보 추출
    # =====================================================================
    with open('raw_data/google_news_grouped_by_category_keyword.json', 'r', encoding='utf-8') as f:
        news_data = json.load(f)

    mapping_list = []
    
    # JSON 구조를 순회하며 run_id, keyword_id 추출
    for category, keywords in news_data.items():
        for keyword, data in keywords.items():
            if 'articles' in data and len(data['articles']) > 0:
                run_id = data['articles'][0]['run_id']
                keyword_id = data['articles'][0]['keyword_id']
                
                mapping_list.append({
                    'run_id': run_id,
                    'keyword_id': keyword_id,
                    'category': category,
                    'keyword': keyword
                })

    mapping_df = pd.DataFrame(mapping_list)
    print("✅ 1/4. JSON 기반 매핑 테이블 생성 완료")

    # =====================================================================
    # 2단계: 유튜브 통합 데이터(Integrated) 매핑
    # =====================================================================
    yt_integrated = pd.read_csv('raw_data/youtube_data_integrated.csv')
    
    # 'run_id'와 'keyword_id' 기준으로 병합
    yt_integrated_mapped = pd.merge(yt_integrated, mapping_df, on=['run_id', 'keyword_id'], how='left')
    
    # 보기 좋게 컬럼 순서 재배치
    cols = ['run_id', 'keyword_id', 'category', 'keyword'] + [c for c in yt_integrated_mapped.columns if c not in ['run_id', 'keyword_id', 'category', 'keyword']]
    yt_integrated_mapped = yt_integrated_mapped[cols]
    
    output_integrated = 'data/youtube/youtube_data_integrated_mapped.csv'
    yt_integrated_mapped.to_csv(output_integrated, index=False, encoding='utf-8-sig')
    print("✅ 2/4. 유튜브 통합 데이터 매핑 및 저장 완료")

    # =====================================================================
    # 3단계: 유튜브 요약 데이터(Summary) 매핑
    # =====================================================================
    yt_summary = pd.read_csv('raw_data/youtube_keyword_summary.csv')
    
    yt_summary_mapped = pd.merge(yt_summary, mapping_df, on=['run_id', 'keyword_id'], how='left')
    
    cols_sum = ['run_id', 'keyword_id', 'category', 'keyword'] + [c for c in yt_summary_mapped.columns if c not in ['run_id', 'keyword_id', 'category', 'keyword']]
    yt_summary_mapped = yt_summary_mapped[cols_sum]
    
    output_summary = 'data/youtube/youtube_keyword_summary_mapped.csv'
    yt_summary_mapped.to_csv(output_summary, index=False, encoding='utf-8-sig')
    print("✅ 3/4. 유튜브 요약 데이터 매핑 및 저장 완료")

    # =====================================================================
    # 4단계: 키워드별 평균(조회수, 좋아요, 댓글수) 도출
    # =====================================================================
    # 방금 메모리에 만들어둔 yt_integrated_mapped 데이터프레임을 바로 활용합니다. (불필요한 파일 읽기 최소화)
    df_avg = yt_integrated_mapped.groupby(['category', 'keyword']).agg({
        'view_count': 'mean',
        'like_count': 'mean',
        'comment_count': 'mean'
    }).reset_index()

    # 컬럼 이름을 '평균(avg_)'으로 변경
    df_avg = df_avg.rename(columns={
        'view_count': 'avg_view_count',
        'like_count': 'avg_like_count',
        'comment_count': 'avg_comment_count'
    })

    # 소수점 첫째 자리에서 반올림
    df_avg['avg_view_count'] = df_avg['avg_view_count'].round(1)
    df_avg['avg_like_count'] = df_avg['avg_like_count'].round(1)
    df_avg['avg_comment_count'] = df_avg['avg_comment_count'].round(1)

    output_average = 'data/youtube/youtube_keyword_average.csv'
    df_avg.to_csv(output_average, index=False, encoding='utf-8-sig')
    print("✅ 4/4. 키워드별 평균 수치 계산 및 저장 완료")

except FileNotFoundError as e:
    print(f"❌ 파일을 찾을 수 없습니다. 경로를 확인해주세요: {e}")
except Exception as e:
    print(f"❌ 에러 발생: {e}")

print("\n🎉 모든 유튜브 데이터 전처리가 하나로 완벽하게 통합 완료되었습니다!")