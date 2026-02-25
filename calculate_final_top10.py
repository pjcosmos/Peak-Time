import json
import os
import pandas as pd

# 4가지 카테고리 목록
categories = ['climate', 'entertainment', 'finance', 'sports']

# 💡 최적화된 가중치 설정 (Volume 70% / Momentum 30%)
w_google_vol = 0.35
w_google_surge = 0.15
w_naver_sum = 0.35
w_naver_slope = 0.15

print("🏆 최적의 가중치(35:15:35:15)를 적용한 최종 TOP 10 산출을 시작합니다...\n")

# 👈 추가: result 폴더가 없으면 자동으로 생성 (exist_ok=True는 이미 폴더가 있어도 에러 내지 않음)
os.makedirs('result', exist_ok=True)

for cat in categories:
    try:
        # 전처리 완료된 JSON 파일 로드
        with open(f'data/preprocessed_{cat}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        df = pd.DataFrame(data['results'])
        
        # 1. 4가지 지표 정규화 (Min-Max Scaling)
        metrics = ['google_absolute_volume', 'google_surge_ratio', 'naver_trend_sum', 'naver_growth_slope']
        
        for metric in metrics:
            m_min = df[metric].min()
            m_max = df[metric].max()
            
            if m_max > m_min:
                df[f'{metric}_score'] = ((df[metric] - m_min) / (m_max - m_min)) * 100
            else:
                df[f'{metric}_score'] = 0
                
        # 2. 정교화된 가중치를 반영한 Total Score 계산
        df['total_score'] = (
            (df['google_absolute_volume_score'] * w_google_vol) +
            (df['google_surge_ratio_score'] * w_google_surge) +
            (df['naver_trend_sum_score'] * w_naver_sum) +
            (df['naver_growth_slope_score'] * w_naver_slope)
        )
        
        # 소수점 둘째 자리 반올림
        df['total_score'] = df['total_score'].round(2)
        
        # 3. 내림차순 정렬 후 Top 10 추출
        df_top10 = df.sort_values(by='total_score', ascending=False).head(10)
        
        # 4. 결과 CSV 저장 (사용자가 엑셀에서 보기 편하도록)
        output_filename = f'result/final_weighted_top10_{cat}.csv'
        output_cols = ['rank_title', 'total_score', 'google_absolute_volume', 'google_surge_ratio', 'naver_trend_sum', 'naver_growth_slope']
        df_top10[output_cols].to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ [{cat.upper()}] TOP 10 산출 성공! ({output_filename})")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: preprocessed_{cat}.json (전처리를 먼저 진행해주세요!)")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 처리 중 에러 발생: {e}")

print("\n🎉 모든 카테고리의 최종 랭킹 추출이 성공적으로 완료되었습니다!")