import os
import json
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
import time
import xml.etree.ElementTree as ET

load_dotenv()

# 네이버 API 키 설정
NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_all_trending_keywords():
    """구글 트렌드 RSS 주소를 최신 버전으로 갱신하여 전체 키워드 추출"""
    print("구글 트렌드 RSS 최신 경로로 수집 시도 중...")
    
    rss_url = "https://trends.google.com/trending/rss?geo=KR"
    
    # 구글 봇 감지를 피하기 위한 브라우저 모사 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    keywords = []
    
    try:
        req = urllib.request.Request(rss_url, headers=headers)
        with urllib.request.urlopen(req) as res:
            xml_data = res.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            
            items = root.findall('.//item')
            for item in items:
                title = item.find('title').text
                if title and title not in keywords:
                    keywords.append(title)
            
            if not keywords:
                # 2안: 1안 실패 시 대체 경로 (daily 대신 일반 trending)
                print("1안 결과 없음, 대체 경로 시도...")
                # ... 필요 시 추가 경로 시도 로직 ...
            
            print(f"총 {len(keywords)}개의 실시간 검색어를 확보했습니다.")
            return keywords

    except urllib.error.HTTPError as e:
        print(f"HTTP 에러 발생 ({e.code}): 주소를 다시 확인해야 합니다.")
        return []
    except Exception as e:
        print(f"기타 에러 발생: {e}")
        return []

def fetch_naver_trend_full(keywords):
    """수집된 모든 키워드에 대해 네이버 데이터랩 검색량 조회 (5개씩 분할)"""
    if not keywords:
        return []

    url = "https://openapi.naver.com/v1/datalab/search"
    # 분석 기간: 2026-02-17부터 오늘까지
    start_date = "2026-02-17" 
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    all_results = []
    
    # 네이버 API는 한 번에 최대 5개 키워드 그룹 가능
    for i in range(0, len(keywords), 5):
        chunk = keywords[i:i+5]
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "date",
            "keywordGroups": [{"groupName": kw, "keywords": [kw]} for kw in chunk]
        }

        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", NAVER_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_SECRET)
        req.add_header("Content-Type", "application/json")
        
        try:
            res = urllib.request.urlopen(req, data=json.dumps(body).encode("utf-8"))
            res_data = json.loads(res.read())
            all_results.extend(res_data['results'])
            print(f"네이버 API 수집 중: {i+len(chunk)}/{len(keywords)} 완료")
            
            # API 호출 간 약간의 지연 (차단 방지)
            time.sleep(0.5) 
        except Exception as e:
            print(f"네이버 API 호출 중 오류 발생 (키워드: {chunk}): {e}")
            
    return all_results

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] 전체 데이터 수집 시작")
    
    # 1. RSS가 제공하는 모든 실시간 키워드 가져오기
    all_kws = get_all_trending_keywords()
    
    if all_kws:
        # 2. 모든 키워드에 대해 네이버 검색량 데이터 수집
        results = fetch_naver_trend_full(all_kws)
        
        # 3. JSON 구조화
        output_data = {
            "meta": {
                "source": "Google Trends RSS & Naver DataLab",
                "collected_at": datetime.now().isoformat(),
                "total_keywords": len(all_kws),
                "period": f"2026-02-17 to {datetime.now().strftime('%Y-%m-%d')}"
            },
            "keywords_list": all_kws,
            "trends": results
        }
        
        # 4. JSON 파일 저장
        with open('naver_data.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"최종 완료: {len(all_kws)}개 데이터 저장됨 (소요시간: {duration.seconds}초)")
    else:
        print("수집할 키워드가 없어 종료합니다.")