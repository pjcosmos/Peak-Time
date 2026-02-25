import os
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 1. 환경 설정 및 시간대 정의
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')
KST = timezone(timedelta(hours=9))

def format_kst_time(iso_date_str=None):
    """유튜브의 UTC 시간을 KST(YYYY-MM-DD HH:MM) 포맷으로 변환"""
    if not iso_date_str:
        dt = datetime.now(KST)
    else:
        # 유튜브 날짜 포맷(2026-02-25T05:30:00Z) 처리
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        dt = dt.astimezone(KST)
    return dt.strftime("%Y-%m-%d %H:%M")

def get_youtube_data_for_db(keyword, keyword_id, run_id):
    """
    특정 키워드에 대해 유튜브 API를 호출하고
    DB 테이블(youtube_video) 구조에 맞는 리스트를 반환
    """
    if not API_KEY:
        print("🚨 API_KEY가 없습니다!")
        return None

    youtube = build('youtube', 'v3', developerKey=API_KEY)

    try:
        # [A] 검색 수행 (maxResults=3)
        search_res = youtube.search().list(
            q=keyword, 
            part='id', 
            maxResults=3, 
            type='video', 
            regionCode='KR'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_res.get('items', []) if 'videoId' in item['id']]
        
        if not video_ids:
            return []

        # [B] 영상 상세 정보 및 통계 수집
        video_res = youtube.videos().list(
            part='statistics,snippet', 
            id=','.join(video_ids)
        ).execute()

        collected_at = format_kst_time() # 수집 시점 (KST)
        
        youtube_rows = []
        for video in video_res.get('items', []):
            stats = video.get('statistics', {})
            snippet = video.get('snippet', {})
            
            # DB youtube_video 테이블 컬럼 1:1 매칭
            row = {
                "run_id": run_id,                         # FK
                "keyword_id": keyword_id,                 # FK
                "youtube_id": video['id'],                # videoId
                "title": snippet.get('title'),
                "channel_title": snippet.get('channelTitle'),
                "published_at": format_kst_time(snippet.get('publishedAt')), # 발행일 KST 변환
                "view_count": int(stats.get('viewCount', 0)),
                "like_count": int(stats.get('likeCount', 0)),
                "comment_count": int(stats.get('commentCount', 0)),
                "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url'),
                "collected_at": collected_at
            }
            youtube_rows.append(row)
        
        return youtube_rows

    except HttpError as e:
        if e.resp.status == 403:
            print(f"🛑 할당량 초과! 수집을 중단합니다. (키워드: {keyword})")
            return "QUOTA_EXCEEDED"
        return []

# 2. 메인 실행부
if __name__ == "__main__":
    # [데이터 로드] 분석팀의 키워드 리스트
    with open('../naver_data/collection_summary.json', 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # [임시 ID 매핑] 실제 DB와 연결 전, 뉴스 조원과 동일한 방식으로 ID 생성
    # 실제 운영 시에는 DB에서 키워드/런 ID를 조회해와야 합니다.
    keyword_id_map = {}
    k_id_counter = 1
    run_id_map = {}
    r_id_counter = 1

    final_db_data = []
    is_halted = False

    for category, info in config_data.items():
        if is_halted: break
        
        # 카테고리별 run_id 할당
        if category not in run_id_map:
            run_id_map[category] = r_id_counter
            r_id_counter += 1
        
        print(f"\n📂 카테고리 수집: {category} (Run ID: {run_id_map[category]})")

        for kw in info['keywords']:
            # 키워드별 keyword_id 할당
            if kw not in keyword_id_map:
                keyword_id_map[kw] = k_id_counter
                k_id_counter += 1
            
            print(f"  > '{kw}' 수집 중... (ID: {keyword_id_map[kw]})")
            
            results = get_youtube_data_for_db(kw, keyword_id_map[kw], run_id_map[category])
            
            if results == "QUOTA_EXCEEDED":
                is_halted = True
                break
            
            if results:
                final_db_data.extend(results)

    # 3. 결과 저장 (JSON & CSV)
    # DB에 바로 Insert하기 가장 좋은 형태는 JSON 리스트입니다.
    if final_db_data:
        # 전체 상세 데이터 (DB youtube_video 테이블용)
        df = pd.DataFrame(final_db_data)
        df.to_csv("youtube_data.csv", index=False, encoding='utf-8-sig')
        
        with open("youtube_data.json", "w", encoding="utf-8") as f:
            json.dump(final_db_data, f, ensure_ascii=False, indent=4)

        # 분석팀 보고용 요약본 (키워드별 통계 통합)
        df_summary = df.groupby('keyword_id').agg({
            'run_id': 'first',
            'view_count': 'sum',
            'like_count': 'sum',
            'comment_count': 'sum'
        }).reset_index()
        df_summary.to_csv("youtube_final_summary.csv", index=False, encoding='utf-8-sig')

        print(f"\n✅ 수집 완료! 총 {len(final_db_data)}개 영상 데이터 저장됨.")
        print("- DB용: youtube_db_ready.json / .csv")
        print("- 요약용: youtube_final_summary.csv")