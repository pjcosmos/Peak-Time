import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from pytrends.request import TrendReq
from dotenv import load_dotenv

load_dotenv()

YT_KEY = os.getenv("YOUTUBE_API_KEY")

def get_trending_keywords():
    """네이버 파일과 동일한 로직으로 키워드 추출"""
    pytrends = TrendReq(hl='ko-KR', tz=540)
    df = pytrends.trending_searches(pn='south_korea')
    return df[0].head(25).tolist()

def fetch_youtube_info(keyword):
    """유튜브 검색 및 상세 정보 수집"""
    youtube = build('youtube', 'v3', developerKey=YT_KEY)
    
    # 영상 검색
    search_res = youtube.search().list(q=keyword, part='snippet', maxResults=3, type='video').execute()
    
    videos = []
    for item in search_res.get('items', []):
        v_id = item['id']['videoId']
        # 조회수 수집
        v_res = youtube.videos().list(part='statistics', id=v_id).execute()
        stats = v_res['items'][0]['statistics']
        
        videos.append({
            "keyword": keyword,
            "title": item['snippet']['title'],
            "viewCount": stats.get('viewCount', 0),
            "likeCount": stats.get('likeCount', 0),
            "publishedAt": item['snippet']['publishedAt'],
            "url": f"https://www.youtube.com/watch?v={v_id}"
        })
    return videos

if __name__ == "__main__":
    kws = get_trending_keywords()
    all_youtube_data = []
    
    for kw in kws[:10]: # 할당량 관리를 위해 우선 10개 테스트
        print(f"유튜브 수집 중: {kw}")
        all_youtube_data.extend(fetch_youtube_info(kw))
        
    output = {
        "source": "youtube_api",
        "collected_at": datetime.now().isoformat(),
        "data": all_youtube_data
    }
    
    with open('youtube_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("youtube_data.json 저장 완료.")