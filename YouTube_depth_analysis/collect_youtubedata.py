import os
import json
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 1. 환경 설정 및 API 로드
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')
KST = timezone(timedelta(hours=9))

def format_kst_time(iso_date_str=None):
    """유튜브의 UTC 시간을 뉴스 데이터와 동일한 YYYY-MM-DD HH:MM (KST) 형식으로 변환"""
    if not iso_date_str:
        dt = datetime.now(KST)
    else:
        try:
            # 유튜브 API는 ISO8601(Z) 형식을 주므로 변환 필요
            dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
            dt = dt.astimezone(KST)
        except:
            return iso_date_str
    return dt.strftime("%Y-%m-%d %H:%M")

def get_youtube_data(keyword, keyword_id, run_id):
    """특정 키워드에 대해 유튜브 상세 데이터를 수집"""
    if not API_KEY:
        print("🚨 API_KEY가 설정되지 않았습니다.")
        return None
    
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    try:
        # 1단계: 검색을 통해 영상 ID 3개 추출 (순위 보존)
        search_res = youtube.search().list(
            q=keyword,
            part='id',
            maxResults=3,
            type='video',
            regionCode='KR',
            order='relevance' # 관련성 순 (유행 반영)
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_res.get('items', []) if 'videoId' in item['id']]
        
        if not video_ids:
            return []

        # 2단계: 영상 ID들로 상세 지표(조회수 등) 수집
        video_res = youtube.videos().list(
            part='statistics,snippet',
            id=','.join(video_ids)
        ).execute()

        collected_at = format_kst_time()
        youtube_rows = []
        
        for video in video_res.get('items', []):
            stats = video.get('statistics', {})
            snippet = video.get('snippet', {})
            
            youtube_rows.append({
                "run_id": run_id,               
                "keyword_id": keyword_id,       
                "youtube_id": video['id'],
                "title": snippet.get('title'),
                "channel_title": snippet.get('channelTitle'),
                "published_at": format_kst_time(snippet.get('publishedAt')),
                "view_count": int(stats.get('viewCount', 0)),
                "like_count": int(stats.get('likeCount', 0)),
                "comment_count": int(stats.get('commentCount', 0)),
                "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url'),
                "collected_at": collected_at
            })
        return youtube_rows

    except HttpError as e:
        if e.resp.status == 403:
            return "QUOTA_EXCEEDED"
        print(f"❌ API 에러 발생: {e}")
        return []

# =========================
# 메인 실행부
# =========================
if __name__ == "__main__":
    # 조원이 생성한 뉴스 데이터 파일 로드
    news_file_path = r'C:\git_down\Peak-Time\news\daum_news_grouped_by_category_keyword.json'
    
    if not os.path.exists(news_file_path):
        print(f"🚨 파일을 찾을 수 없습니다: {news_file_path}")
        exit()

    with open(news_file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)

    final_db_data = []
    is_halted = False

    # 뉴스 데이터의 [카테고리] -> [키워드] 구조를 그대로 따라감 (순서 보장)
    for category, keywords_dict in news_data.items():
        if is_halted: break
        print(f"\n📂 카테고리 수집 중: {category}")

        for keyword, articles in keywords_dict.items():
            if not articles: continue
            
            # (각 키워드의 첫 번째 기사 객체에서 ID를 참조)
            target_run_id = articles[0]['run_id']
            target_keyword_id = articles[0]['keyword_id']
            
            print(f"  └─ 키워드: '{keyword}' (ID: {target_keyword_id}) 수집 시작...", end="", flush=True)
            
            # 유튜브 데이터 가져오기
            results = get_youtube_data(keyword, target_keyword_id, target_run_id)
            
            if results == "QUOTA_EXCEEDED":
                print("\n🛑 유튜브 API 할당량이 초과되었습니다. 수집을 중단합니다.")
                is_halted = True
                break
            
            if results:
                final_db_data.extend(results)
                print(f" 완료 ({len(results)}개 영상)")
            else:
                print(" 데이터 없음")
            
            time.sleep(0.5) # API 매너 타임

    # 최종 저장 (JSON 및 CSV)
    if final_db_data:
        # 1. DB 적재용 전체 데이터 저장
        with open("youtube_data_integrated.json", "w", encoding="utf-8") as f:
            json.dump(final_db_data, f, ensure_ascii=False, indent=4)
        
        # 2. 분석 및 확인용 CSV 저장
        df = pd.DataFrame(final_db_data)
        df.to_csv("youtube_data_integrated.csv", index=False, encoding='utf-8-sig')

        # 3. 분석팀을 위한 키워드별 요약 파일 (합계 지표)
        summary = df.groupby(['run_id', 'keyword_id']).agg({
            'view_count': 'sum',
            'like_count': 'sum',
            'comment_count': 'sum'
        }).reset_index()
        summary.to_csv("youtube_keyword_summary.csv", index=False, encoding='utf-8-sig')

        print("\n" + "="*50)
        print(f"✨ 수집 및 동기화 완료!")
        print(f"📊 총 수집된 영상 수: {len(final_db_data)}개")
        print(f"📁 저장 파일: youtube_data_integrated.json / csv")
        print("="*50)