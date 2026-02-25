import json
import pandas as pd
import numpy as np

# 분석할 4가지 카테고리 목록
categories = ['climate', 'entertainment', 'finance', 'sports']

print("📈 '성장세 기울기(naver_growth_slope)' 지표 추가 전처리를 시작합니다...\n")

for cat in categories:
    try:
        # 1. 기존 전처리된 JSON 파일 읽기
        with open(f'data/preprocessed_{cat}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 2. 각 키워드별로 기울기 계산 및 데이터 추가
        for item in data['results']:
            # naver_daily_ratio에서 비율(ratio) 값만 추출하여 리스트로 만듭니다.
            daily_ratios = [day.get('ratio', 0) for day in item.get('naver_daily_ratio', [])]
            
            # 데이터가 2일 치 이상 있어야 선의 기울기(추세)를 구할 수 있습니다.
            if len(daily_ratios) > 1:
                x = np.arange(len(daily_ratios)) # [0, 1, 2, ...] 형태의 X축 (시간의 흐름)
                
                # np.polyfit(X축, Y축, 1차원)을 사용해 기울기(slope)를 구합니다.
                slope, _ = np.polyfit(x, daily_ratios, 1) 
            else:
                slope = 0.0
                
            # 기존 딕셔너리에 새로운 항목 추가 (반올림하여 소수점 둘째 자리까지 저장)
            item['naver_growth_slope'] = round(slope, 2)
            
        # 3. 업데이트된 데이터를 기존 JSON 파일에 그대로 덮어쓰기
        with open(f'data/preprocessed_{cat}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        # 4. 눈으로 확인하기 쉽게 CSV 파일도 업데이트하여 저장
        df = pd.DataFrame(data['results'])
        df.to_csv(f'data/preprocessed_{cat}.csv', index=False, encoding='utf-8-sig')
        
        print(f"✅ [{cat.upper()}] 카테고리 전처리 완료! (naver_growth_slope 추가됨)")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: preprocessed_{cat}.json")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 처리 중 오류 발생: {e}")

print("\n🎉 모든 카테고리에 새로운 지표 추가가 성공적으로 완료되었습니다!")