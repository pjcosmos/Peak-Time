import os
import json
import time
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv()

NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_trending_30_selenium():
    print("구글 트렌드 웹사이트 접속 중 (강력 추출 모드)...")
    
    options = Options()
    # options.add_argument("--headless") # 성공할 때까지는 창을 띄워서 확인하세요
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    keywords = []

    try:
        # 1. 페이지 접속
        driver.get("https://trends.google.co.kr/trending?geo=KR&hl=ko")
        time.sleep(8) # 구글 서버가 응답할 충분한 시간

        # 2. 특정 클래스가 아닌, 텍스트가 포함된 모든 요소 탐색
        # 구글 트렌드 키워드는 보통 'ng-binding' 혹은 특정 구조 안에 있습니다.
        potential_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'title')] | //div[@class='ng-binding'] | //td")
        
        for el in potential_elements:
            val = el.text.strip()
            # 한글이 포함되어 있고 길이가 적당한(2~20자) 텍스트만 추출
            if val and 2 <= len(val) <= 20 and val not in keywords:
                # 숫자나 '검색량' 같은 단어 제외 필터링
                if not any(char.isdigit() for char in val) and "분석" not in val:
                    keywords.append(val)
            if len(keywords) >= 30:
                break

        # 3. 만약 위 방법으로도 못 찾았다면, 페이지 전체 텍스트에서 쪼개기 시도
        if not keywords:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print("전체 텍스트 스캔 중...")
            # 구글 트렌드 페이지 특유의 줄바꿈 구조를 이용해 분리 (임시 로직)
            raw_lines = body_text.split('\n')
            for line in raw_lines:
                line = line.strip()
                if 2 <= len(line) <= 15 and line not in keywords:
                    keywords.append(line)
                if len(keywords) >= 30: break

        print(f"✅ 수집 완료: {len(keywords)}개 확보")
        return keywords

    except Exception as e:
        print(f"❌ 오류: {e}")
        return []
    finally:
        driver.quit()

def fetch_naver_trend(keywords):
    if not keywords: return []
    url = "https://openapi.naver.com/v1/datalab/search"
    all_results = []
    
    for i in range(0, len(keywords), 5):
        chunk = keywords[i:i+5]
        body = {
            "startDate": "2026-02-17",
            "endDate": datetime.now().strftime('%Y-%m-%d'),
            "timeUnit": "date",
            "keywordGroups": [{"groupName": kw, "keywords": [kw]} for kw in chunk]
        }
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", NAVER_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_SECRET)
        req.add_header("Content-Type", "application/json")
        try:
            res = urllib.request.urlopen(req, data=json.dumps(body).encode("utf-8"))
            all_results.extend(json.loads(res.read())['results'])
            print(f"네이버 호출 성공: {i+len(chunk)}개 완료")
            time.sleep(0.5)
        except: pass
    return all_results

if __name__ == "__main__":
    kws = get_trending_30_selenium()
    if kws:
        results = fetch_naver_trend(kws)
        output = {"top_keywords_list": kws, "data": results}
        with open('Croll_naver_data.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        print("🚀 저장 완료!")