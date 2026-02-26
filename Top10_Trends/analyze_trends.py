import json
import os
import pandas as pd

# 1. 분석할 카테고리
categories = ['climate', 'entertainment', 'finance', 'sports']

# 💡 가중치 세팅 (Volume 70% : Momentum 30%)
w_google_vol = 0.35
w_naver_sum = 0.35
w_google_surge = 0.15
w_naver_slope = 0.15

print("🔍 키워드별 [플랫폼 기여도 심층 분석]을 시작합니다...\n")

# 👈 추가: result 폴더가 없으면 자동으로 생성 (exist_ok=True는 이미 폴더가 있어도 에러 내지 않음)
os.makedirs('result/platform', exist_ok=True)

for cat in categories:
    try:
        # 전처리 완료된 JSON 파일 로드
        with open(f'data/preprocessed_{cat}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        df = pd.DataFrame(data['results'])
        
        # 2. 4가지 지표 정규화 (Min-Max)
        metrics = ['google_absolute_volume', 'google_surge_ratio', 'naver_trend_sum', 'naver_growth_slope']
        for metric in metrics:
            m_min, m_max = df[metric].min(), df[metric].max()
            if m_max > m_min:
                df[f'{metric}_score'] = ((df[metric] - m_min) / (m_max - m_min)) * 100
            else:
                df[f'{metric}_score'] = 0
                
        # 3. 플랫폼별 획득 점수(Point) 분리 계산
        df['google_point'] = (df['google_absolute_volume_score'] * w_google_vol) + (df['google_surge_ratio_score'] * w_google_surge)
        df['naver_point'] = (df['naver_trend_sum_score'] * w_naver_sum) + (df['naver_growth_slope_score'] * w_naver_slope)
        
        # 총점은 두 플랫폼 점수의 합
        df['total_score'] = df['google_point'] + df['naver_point']
        
        # 4. 플랫폼별 기여도(%) 계산 (분모가 0일 경우 에러 방지를 위해 fillna(0) 사용)
        df['google_ratio(%)'] = (df['google_point'] / df['total_score'] * 100).fillna(0).round(1)
        df['naver_ratio(%)'] = (df['naver_point'] / df['total_score'] * 100).fillna(0).round(1)
        
        # 5. 성향 분석 (Dominance Labeling) 함수
        def get_dominance(g_ratio, n_ratio):
            if g_ratio >= 60:
                return "🔵 구글 강세 (Google 주도)"
            elif n_ratio >= 60:
                return "🟢 네이버 강세 (Naver 주도)"
            else:
                return "⚖️ 플랫폼 균형 (Balanced)"
                
        # 각 행(row)마다 함수를 적용하여 새로운 라벨 컬럼 생성
        df['trend_type'] = df.apply(lambda row: get_dominance(row['google_ratio(%)'], row['naver_ratio(%)']), axis=1)
        
        # 6. 정렬 및 정리
        # 총점 내림차순 10개 추출
        top10 = df.sort_values(by='total_score', ascending=False).head(10).copy()
        
        # 점수들을 소수점 둘째 자리까지 깔끔하게 반올림
        top10['total_score'] = top10['total_score'].round(2)
        top10['google_point'] = top10['google_point'].round(2)
        top10['naver_point'] = top10['naver_point'].round(2)
        
        # 엑셀로 내보낼 핵심 컬럼만 선택
        output_cols = [
            'rank_title', 'total_score', 
            'google_point', 'naver_point', 
            'google_ratio(%)', 'naver_ratio(%)', 'trend_type'
        ]
        
        output_filename = f'result/platform/analyzed_top10_{cat}.csv'
        top10[output_cols].to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ [{cat.upper()}] 심층 분석 완료! ({output_filename})")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: preprocessed_{cat}.json")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 처리 중 에러 발생: {e}")

print("\n🎉 모든 분석 리포트 생성이 완료되었습니다! CSV 파일을 확인해 보세요.")