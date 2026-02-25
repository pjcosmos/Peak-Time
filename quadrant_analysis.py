import json
import os
import pandas as pd

# 분석할 카테고리
categories = ['climate', 'entertainment', 'finance', 'sports']

print("🌟 [Volume vs Momentum] 4분면 포지셔닝 맵 분석을 시작합니다...\n")

# 👈 추가: result 폴더 안의 quadrant 폴더까지 한 번에 생성
os.makedirs('result/quadrant', exist_ok=True)

for cat in categories:
    try:
        # 전처리 완료된 데이터 로드
        with open(f'data/preprocessed_{cat}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        df = pd.DataFrame(data['results'])
        
        # 1. 4가지 지표 정규화 (Min-Max, 0~100점)
        metrics = ['google_absolute_volume', 'google_surge_ratio', 'naver_trend_sum', 'naver_growth_slope']
        for metric in metrics:
            m_min, m_max = df[metric].min(), df[metric].max()
            if m_max > m_min:
                df[f'{metric}_score'] = ((df[metric] - m_min) / (m_max - m_min)) * 100
            else:
                df[f'{metric}_score'] = 0
                
        # 2. X축(Volume)과 Y축(Momentum) 점수 생성 (각 100점 만점)
        df['volume_score'] = (df['google_absolute_volume_score'] + df['naver_trend_sum_score']) / 2
        df['momentum_score'] = (df['google_surge_ratio_score'] + df['naver_growth_slope_score']) / 2
        
        # 3. 기존의 70:30 가중치를 바탕으로 종합 순위 도출을 위한 Total Score 계산
        df['total_score'] = (df['volume_score'] * 0.7) + (df['momentum_score'] * 0.3)
        
        # Top 10 추출
        top10 = df.sort_values(by='total_score', ascending=False).head(10).copy()
        
        # 4. 사분면을 나누기 위한 십자선(기준점) 설정 -> Top 10의 평균값 사용
        vol_threshold = top10['volume_score'].mean()
        mom_threshold = top10['momentum_score'].mean()
        
        # 5. 사분면 분류 함수 (Quadrant Assignment)
        def get_quadrant(vol, mom):
            if vol >= vol_threshold and mom >= mom_threshold:
                return "👑 메가 트렌드 (대세)"
            elif vol >= vol_threshold and mom < mom_threshold:
                return "💎 스테디셀러 (꾸준함)"
            elif vol < vol_threshold and mom >= mom_threshold:
                return "🚀 라이징 스타 (급상승)"
            else:
                return "🏕️ 니치 마켓 (틈새시장)"
                
        # 분류 함수 적용
        top10['positioning'] = top10.apply(lambda row: get_quadrant(row['volume_score'], row['momentum_score']), axis=1)
        
        # 결과 포맷팅 (소수점 정리)
        top10['total_score'] = top10['total_score'].round(2)
        top10['volume_score'] = top10['volume_score'].round(2)
        top10['momentum_score'] = top10['momentum_score'].round(2)
        
        # CSV 저장
        output_cols = ['rank_title', 'positioning', 'volume_score', 'momentum_score', 'total_score']
        output_filename = f'result/quadrant/positioning_map_{cat}.csv'
        top10[output_cols].to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f"✅ [{cat.upper()}] 사분면 분석 완료! ({output_filename})")
        
        # 분석 요약 출력
        print(f"   [기준점] Volume 평균: {vol_threshold:.1f}점 / Momentum 평균: {mom_threshold:.1f}점")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: preprocessed_{cat}.json")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 처리 중 에러 발생: {e}")

print("\n🎉 모든 포지셔닝 맵 데이터 생성이 완료되었습니다!")