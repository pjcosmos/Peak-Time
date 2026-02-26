import os
import pandas as pd
import matplotlib.pyplot as plt

# ⚠️ 한글 폰트 설정 (윈도우: 'Malgun Gothic', 맥: 'AppleGothic')
# 시스템에 맞게 폰트 이름을 수정해 주세요.
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

# 분석할 카테고리
categories = ['climate', 'entertainment', 'finance', 'sports']

# 사분면별 마커 색상 지정
color_map = {
    "👑 메가 트렌드 (대세)": "red",
    "💎 스테디셀러 (꾸준함)": "blue",
    "🚀 라이징 스타 (급상승)": "orange",
    "🏕️ 니치 마켓 (틈새시장)": "green"
}

print("🎨 [Volume vs Momentum] 포지셔닝 맵 시각화를 시작합니다...\n")


for cat in categories:
    try:
        # 이전에 만든 포지셔닝 맵 CSV 파일 읽기
        df = pd.read_csv(f'result/quadrant/positioning_map_{cat}.csv')
        
        # 그래프 도화지 크기 설정
        plt.figure(figsize=(10, 8))
        
        # 십자선(기준점) 위치 계산 (Top 10의 평균)
        vol_threshold = df['volume_score'].mean()
        mom_threshold = df['momentum_score'].mean()
        
        # 각 키워드별로 점(Scatter) 찍기
        for idx, row in df.iterrows():
            color = color_map.get(row['positioning'], 'black')
            
            # 점 그리기 (s는 점의 크기, alpha는 투명도)
            plt.scatter(row['volume_score'], row['momentum_score'], 
                        color=color, s=150, alpha=0.7, edgecolors='white')
            
            # 점 바로 옆에 키워드 이름(텍스트) 달아주기
            plt.text(row['volume_score'] + 1.5, row['momentum_score'] + 1.0, 
                     row['rank_title'], fontsize=11, weight='bold')
            
        # 기준선(십자선) 그리기
        plt.axvline(x=vol_threshold, color='gray', linestyle='--', alpha=0.5)
        plt.axhline(y=mom_threshold, color='gray', linestyle='--', alpha=0.5)
        
        # 4개 모서리에 사분면 이름(워터마크) 표시
        plt.text(100, 100, "👑 메가 트렌드", fontsize=15, color='red', alpha=0.2, ha='right', va='top')
        plt.text(100, 0, "💎 스테디셀러", fontsize=15, color='blue', alpha=0.2, ha='right', va='bottom')
        plt.text(0, 100, "🚀 라이징 스타", fontsize=15, color='orange', alpha=0.2, ha='left', va='top')
        plt.text(0, 0, "🏕️ 니치 마켓", fontsize=15, color='green', alpha=0.2, ha='left', va='bottom')
        
        # 축 이름과 제목 달기
        plt.title(f'[{cat.upper()}] 트렌드 포지셔닝 맵 (Volume vs Momentum)', fontsize=16, weight='bold', pad=15)
        plt.xlabel('Volume Score (규모와 꾸준함 ->)', fontsize=12)
        plt.ylabel('Momentum Score (단기 폭발력 ->)', fontsize=12)
        
        # X축 Y축 범위 고정 (0~105점)
        plt.xlim(-5, 105)
        plt.ylim(-5, 105)
        plt.grid(True, linestyle=':', alpha=0.6)
        
        # 그래프를 여백 없이 꽉 채운 후 이미지 파일(PNG)로 저장
        plt.tight_layout()
        output_filename = f'result/quadrant/quadrant_map_{cat}.png'
        plt.savefig(output_filename, dpi=300)
        plt.close() # 다음 그래프를 위해 도화지 비우기
        
        print(f"✅ [{cat.upper()}] 시각화 이미지 생성 완료! ({output_filename})")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: positioning_map_{cat}.csv")
    except Exception as e:
        print(f"❌ [{cat.upper()}] 시각화 중 에러 발생: {e}")

print("\n🎉 모든 시각화 작업이 완료되었습니다!")