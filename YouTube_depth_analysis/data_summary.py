import pandas as pd

# 1. 수집된 원본 파일 불러오기
df = pd.read_csv('youtube_deep_analysis.csv')

# 2. 키워드별로 그룹화하여 수치 합산하기
# youtube_total_scale은 어차피 같은 값이니 평균(mean)이나 첫 번째 값(first)을 가져옵니다.
summary_df = df.groupby('keyword').agg({
    'youtube_total_scale': 'first',  # 관련 영상 총 개수
    'view_count': 'sum',             # 상위 3개 조회수 통합
    'like_count': 'sum',             # 상위 3개 좋아요 통합
    'comment_count': 'sum'           # 상위 3개 댓글 통합
}).reset_index()

# 3. 컬럼명 알아보기 쉽게 변경
summary_df.columns = [
    '검색어(Keyword)', 
    '유튜브_전체_영상수', 
    '상위3개_조회수_통합', 
    '상위3개_좋아요_통합', 
    '상위3개_댓글_통합'
]

# 4. 최종 결과 저장
summary_df.to_csv('youtube_final_summary.csv', index=False, encoding='utf-8-sig')
print("✅ 분석팀 전달용 요약 파일(youtube_final_summary.csv)이 생성되었습니다!")