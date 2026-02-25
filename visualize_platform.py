import os
import pandas as pd
import matplotlib.pyplot as plt

# ⚠️ 한글 폰트 설정 (윈도우: 'Malgun Gothic', 맥: 'AppleGothic')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 분석할 4가지 카테고리
categories = ['climate', 'entertainment', 'finance', 'sports']

# 🎨 플랫폼을 상징하는 브랜드 컬러 지정
color_google = '#4285F4' # 구글을 상징하는 파란색
color_naver = '#03C75A'  # 네이버를 상징하는 초록색

print("📊 [플랫폼 기여도] 누적 막대 그래프 생성을 시작합니다...\n")

# 👈 추가: 시각화 이미지를 저장할 전용 폴더 생성
os.makedirs('result/visualize', exist_ok=True)

for cat in categories:
    try:
        # 심층 분석이 완료된 CSV 파일 로드
        df = pd.read_csv(f'result/analyzed_top10_{cat}.csv')
        
        # 1위가 그래프 맨 위로 올라오도록 점수 기준 오름차순 정렬
        df = df.sort_values(by='total_score', ascending=True)
        
        # 도화지 생성
        plt.figure(figsize=(10, 7))
        
        # 1. 네이버 점수를 먼저 그립니다 (왼쪽부터 시작)
        plt.barh(df['rank_title'], df['naver_point'], color=color_naver, edgecolor='white', label='Naver (네이버 기여도)')
        
        # 2. 구글 점수를 그 위에 쌓습니다 (left 속성에 네이버 점수를 넣어 오른쪽으로 밀어냅니다)
        plt.barh(df['rank_title'], df['google_point'], left=df['naver_point'], color=color_google, edgecolor='white', label='Google (구글 기여도)')
        
        # 제목 및 축 이름 설정
        plt.title(f'[{cat.upper()}] 키워드별 플랫폼 기여도 (Naver vs Google)', fontsize=16, weight='bold', pad=15)
        plt.xlabel('Total Score (플랫폼별 획득 점수)', fontsize=12)
        
        # 우측 하단에 범례(Legend) 표시
        plt.legend(loc='lower right', fontsize=11)
        
        # 🎯 각 막대 안에 정확한 퍼센트(%) 텍스트 삽입하기
        for i, (idx, row) in enumerate(df.iterrows()):
            n_pt = row['naver_point']
            g_pt = row['google_point']
            n_ratio = row['naver_ratio(%)']
            g_ratio = row['google_ratio(%)']
            
            # 네이버 비율이 10% 이상일 때만 글씨를 씁니다 (비율이 너무 작으면 글자가 삐져나감 방지)
            if n_ratio >= 10:
                plt.text(n_pt / 2, i, f'{n_ratio:.0f}%', ha='center', va='center', color='white', weight='bold', fontsize=10)
            
            # 구글 비율이 10% 이상일 때만 글씨를 씁니다
            if g_ratio >= 10:
                plt.text(n_pt + (g_pt / 2), i, f'{g_ratio:.0f}%', ha='center', va='center', color='white', weight='bold', fontsize=10)
        
        # x축 여백을 가장 높은 점수보다 10% 넓게 설정 (그래프가 답답해 보이지 않도록)
        plt.xlim(0, max(df['total_score']) * 1.1)
        
        # 배경에 희미한 세로선 추가 (점수 파악 용이)
        plt.grid(axis='x', linestyle='--', alpha=0.5)
        
        # 여백 최적화 후 고해상도 이미지(PNG) 저장
        plt.tight_layout()
        output_filename = f'result/visualize/platform_dominance_{cat}.png'
        plt.savefig(output_filename, dpi=300)
        plt.close() # 다음 그래프를 그리기 위해 도화지 닫기
        
        print(f"✅ [{cat.upper()}] 시각화 완료! ({output_filename})")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: analyzed_top10_{cat}.csv")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

print("\n🎉 모든 누적 막대 그래프가 성공적으로 생성되었습니다!")