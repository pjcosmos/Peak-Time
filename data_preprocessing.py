import json
import pandas as pd
import numpy as np
import os

# 구글 볼륨 문자열에서 '절대 검색량'과 '급상승 비율'을 숫자로 추출하는 함수
def parse_google_data(vol_str):
    if not isinstance(vol_str, str):
        return 0, 0
    
    lines = vol_str.split('\n')
    absolute_volume = 0
    surge_ratio = 0
    
    # 절대 검색량 추출
    if len(lines) > 0:
        val_str = lines[0].replace('+', '').replace(',', '').strip()
        if '만' in val_str:
            absolute_volume = float(val_str.replace('만', '')) * 10000
        elif '천' in val_str:
            absolute_volume = float(val_str.replace('천', '')) * 1000
        else:
            try:
                absolute_volume = float(val_str)
            except ValueError:
                absolute_volume = 0
                
    # 급상승 비율 추출
    if len(lines) >= 3:
        surge_str = lines[2].replace('%', '').replace(',', '').strip()
        try:
            surge_ratio = float(surge_str)
        except ValueError:
            surge_ratio = 0
            
    return absolute_volume, surge_ratio

# 1. 환경 설정
categories = ['climate', 'entertainment', 'finance', 'sports']
os.makedirs('data', exist_ok=True) # 전처리된 데이터를 저장할 data 폴더 자동 생성

print("🧹 [Step 1] 통합 데이터 전처리를 시작합니다 (Google 분해 + Naver 기울기 산출)...\n")

for cat in categories:
    try:
        # 원본 Raw Data 읽기
        with open(f'raw_data/trend_report_{cat}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        processed_results = []
        
        for item in data['results']:
            # 1️⃣ 구글 데이터 분해 (절대량, 급상승)
            g_vol, g_surge = parse_google_data(item.get('google_volume', '0'))
            
            # 2️⃣ 네이버 데이터 성장세 기울기 계산
            daily_ratios = [day.get('ratio', 0) for day in item.get('naver_daily_ratio', [])]
            if len(daily_ratios) > 1:
                x = np.arange(len(daily_ratios))
                slope, _ = np.polyfit(x, daily_ratios, 1) 
            else:
                slope = 0.0
            
            # 3️⃣ 통합된 하나의 새로운 데이터 구조 생성
            new_item = {
                'rank_title': item.get('rank_title', ''),
                'google_absolute_volume': g_vol,
                'google_surge_ratio': g_surge,
                'naver_trend_sum': item.get('naver_trend_sum', 0),
                'naver_growth_slope': round(slope, 2), # 소수점 둘째 자리까지
                'naver_daily_ratio': item.get('naver_daily_ratio', [])
            }
            
            processed_results.append(new_item)
            
        # 1. 통합 전처리된 JSON 파일 저장
        new_json_data = {
            "category": data.get("category", cat),
            "base_date": data.get("base_date", ""),
            "results": processed_results
        }
        
        json_filename = f'data/preprocessed_{cat}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(new_json_data, f, ensure_ascii=False, indent=4)
            
        # 2. 통합 전처리된 CSV 파일 저장
        df = pd.DataFrame(processed_results)
        csv_filename = f'data/preprocessed_{cat}.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ [{cat.upper()}] 통합 전처리 완료! -> {json_filename}, {csv_filename} 생성")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: trend_report_{cat}.json")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 전처리 중 에러 발생: {e}")

print("\n🎉 모든 데이터의 전처리가 성공적으로 통합되었습니다!")