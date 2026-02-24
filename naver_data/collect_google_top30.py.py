import os
import json
import time
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 1. 환경 설정 및 API 키 로드
load_dotenv()
NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_integrated_analysis_final_ultra():
    # 분석 대상 카테고리 (금융, 스포츠, 엔터, 기후)
    target_urls = {
        'finance': 'https://trends.google.co.kr/trending?geo=KR&hl=ko&hours=168&category=3',
        'sports': 'https://trends.google.co.kr/trending?geo=KR&hl=ko&hours=168&category=17',
        'entertainment': 'https://trends.google.co.kr/trending?geo=KR&hl=ko&hours=168&category=4',
        'climate': 'https://trends.google.co.kr/trending?geo=KR&hl=ko&hours=168&category=20'
    }
    
    options = Options()
    options.add_argument("--window-size=1920,1080")
    # 봇 탐지 방지를 위한 유저 에이전트 설정
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    summary_report = {}

    # [핵심] 클래스명 대신 태그 구조(tr > td)로 접근하는 범용 스크립트
    # innerText와 textContent를 모두 활용해 로딩 지연 데이터를 강제 추출합니다.
    precision_scan_script = r"""
    let snapshot = [];
    let rows = document.querySelectorAll('tr');
    
    rows.forEach(row => {
        let cells = row.querySelectorAll('td');
        // 구글 트렌드 표 구조상 칸이 3개 이상인 곳에 데이터가 있습니다.
        if(cells.length >= 3) {
            // 2번째 칸(index 1) = 키워드, 3번째 칸(index 2) = 검색량
            let titleText = (cells[1].innerText || cells[1].textContent || "").split('\n')[0].trim();
            let volumeText = (cells[2].innerText || cells[2].textContent || "").trim();
            
            if(titleText && titleText.length > 1) {
                snapshot.push({title: titleText, google_volume: volumeText});
            }
        }
    });
    return snapshot;
    """

    for label, url in target_urls.items():
        print(f"\n📡 [{label}] 정밀 구조 스캔 프로세스 가동...")
        driver.get(url)
        time.sleep(12) # 페이지 및 데이터 로딩 대기

        collected_dict = {} # 중복 제거용 저장소
        
        # 촘촘하게 내려가며 화면에 걸리는 모든 것을 낚아챕니다. (25단계 스캔)
        for step in range(25): 
            current_snapshot = driver.execute_script(precision_scan_script)
            
            new_finds = 0
            for item in current_snapshot:
                title = item['title']
                # 시간 정보 및 숫자만 있는 노이즈 제거
                if not title.isdigit() and "시간 전" not in title and "분 전" not in title:
                    if title not in collected_dict:
                        collected_dict[title] = item['google_volume']
                        new_finds += 1
            
            # 목표치(35개) 확보 시 조기 종료
            if len(collected_dict) >= 35:
                print(f"   > 목표 수량 충분 확보 ({len(collected_dict)}개)")
                break
                
            # 스크롤 단위를 300px로 좁혀서 아주 꼼꼼하게 훑습니다.
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(2.5) # 구글 서버가 데이터를 채워넣을 충분한 시간 부여
            
            if new_finds > 0:
                print(f"   > {step+1}단계: 누계 {len(collected_dict)}개 (새 키워드 {new_finds}개 포착)")

        # 최종 TOP 30 슬라이싱
        final_list = [{"title": t, "google_volume": v} for t, v in collected_dict.items()][:30]
        
        if not final_list:
            print(f"⚠️ {label}에서 데이터를 가져오지 못했습니다. (페이지 로딩 확인 필요)")
            continue

        print(f"✅ {label}: 최종 {len(final_list)}개 키워드 확정")

        # 2. 네이버 API 연동 및 결과 병합
        titles = [it['title'] for it in final_list]
        naver_raw = fetch_naver_data(titles)

        final_data_list = []
        for item in final_list:
            n_data = next((res['data'] for res in naver_raw if res['title'] == item['title']), [])
            ratio_sum = round(sum(day['ratio'] for day in n_data), 2)
            
            final_data_list.append({
                "rank_title": item['title'],
                "google_volume": item['google_volume'],
                "naver_trend_sum": ratio_sum,
                "naver_daily_ratio": n_data
            })

        # 3. 개별 결과 저장
        save_path = f'trend_report_{label}.json'
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump({
                "category": label,
                "base_date": datetime.now().strftime('%Y-%m-%d'),
                "results": final_data_list
            }, f, ensure_ascii=False, indent=4)
        
        summary_report[label] = {
            "total_count": len(final_data_list),
            "keywords": [x['rank_title'] for x in final_data_list]
        }

    # 4. 전체 요약 리포트 저장
    with open('collection_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=4)
    
    print("\n✨ 분석 완료! 결과는 'trend_report_*.json' 및 'collection_summary.json' 파일에 저장되었습니다.")
    driver.quit()

def fetch_naver_data(keywords):
    if not keywords: return []
    url = "https://openapi.naver.com/v1/datalab/search"
    results = []
    for i in range(0, len(keywords), 5):
        chunk = keywords[i:i+5]
        body = {
            "startDate": "2026-02-18",
            "endDate": datetime.now().strftime('%Y-%m-%d'),
            "timeUnit": "date",
            "keywordGroups": [{"groupName": k, "keywords": [k]} for k in chunk]
        }
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", NAVER_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_SECRET)
        req.add_header("Content-Type", "application/json")
        try:
            res = urllib.request.urlopen(req, data=json.dumps(body).encode("utf-8"))
            results.extend(json.loads(res.read())['results'])
            time.sleep(0.5)
        except:
            pass
    return results

if __name__ == "__main__":
    get_integrated_analysis_final_ultra()