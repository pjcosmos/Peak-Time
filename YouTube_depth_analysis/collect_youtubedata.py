import json
import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 1. 환경 설정
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')

def get_youtube_data(keyword):
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # 검색 결과 (maxResults=3으로 고정하여 3개 초과 방지)
    search_response = youtube.search().list(
        q=keyword, 
        part='id,snippet', 
        maxResults=3, 
        type='video', 
        regionCode='KR'
    ).execute()

    total_results = search_response.get('pageInfo', {}).get('totalResults', 0)
    
    # [수정 포인트 1] videoId 추출 시 에러 방지 (dict.get 활용)
    video_ids = []
    for item in search_response.get('items', []):
        v_id = item.get('id', {}).get('videoId')
        if v_id:
            video_ids.append(v_id)
    
    if not video_ids:
        return []

    # 상세 지표 수집
    video_response = youtube.videos().list(
        part='statistics,snippet', 
        id=','.join(video_ids)
    ).execute()

    video_data = []
    # [수정 포인트 2] 수집된 리스트가 3개를 넘지 않도록 슬라이싱 보장
    for video in video_response.get('items', [])[:3]:
        stats = video.get('statistics', {})
        video_data.append({
            'keyword': keyword,
            'youtube_total_scale': total_results,
            'video_title': video['snippet']['title'],
            'view_count': int(stats.get('viewCount', 0)),
            'like_count': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0))
        })
    return video_data

# 2. JSON 파일 읽기 및 실행
with open('collection_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

all_youtube_results = []

for category, info in data.items():
    print(f"[{category}] 카테고리 수집 시작...")
    for kw in info['keywords']:
        try:
            print(f"  > '{kw}' 수집 중...")
            result = get_youtube_data(kw)
            if result:
                all_youtube_results.extend(result)
        except Exception as e:
            print(f"  ! '{kw}' 수집 실패: {e}")

# 3. 상세 데이터 저장 (CSV - 3줄씩 나옴)
df_detail = pd.DataFrame(all_youtube_results)
df_detail.to_csv("youtube_deep_analysis.csv", index=False, encoding='utf-8-sig')

# 4. 요약 데이터 생성 및 저장 (CSV - 키워드당 1줄 통합)
if not df_detail.empty:
    df_summary = df_detail.groupby('keyword').agg({
        'youtube_total_scale': 'first',
        'view_count': 'sum',
        'like_count': 'sum',
        'comment_count': 'sum'
    }).reset_index()
    
    # 컬럼명 정리
    df_summary.columns = ['keyword', 'total_scale', 'sum_views', 'sum_likes', 'sum_comments']
    df_summary.to_csv("youtube_final_summary.csv", index=False, encoding='utf-8-sig')

print("\n✅ 모든 작업 완료!")
print("- 상세 리스트: youtube_deep_analysis.csv")
print("- 통합 요약본: youtube_final_summary.csv")