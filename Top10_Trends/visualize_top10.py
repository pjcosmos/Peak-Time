import pandas as pd
import matplotlib.pyplot as plt
import os

# ⚠️ 한글 폰트 설정 (윈도우: 'Malgun Gothic', 맥: 'AppleGothic')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

categories = ['climate', 'entertainment', 'finance', 'sports']
colors = ['#4CAF50', '#E91E63', '#2196F3', '#FF9800'] # 카테고리별 테마 색상 지정

print("📊 [TOP 10 랭킹] 수평 막대 그래프 생성을 시작합니다...\n")

# 👈 추가: 시각화 이미지를 저장할 전용 폴더 생성
os.makedirs('result/visualize', exist_ok=True)

for i, cat in enumerate(categories):
    try:
        # 최종 산출된 CSV 파일 로드
        df = pd.read_csv(f'result/final_weighted_top10_{cat}.csv')
        
        # 수평 막대 그래프는 아래에서부터 그려지므로, 점수를 오름차순 정렬해야 1등이 맨 위로 올라갑니다!
        df = df.sort_values(by='total_score', ascending=True)
        
        # 도화지 생성
        plt.figure(figsize=(10, 6))
        
        # 막대 그래프 그리기 (y축: 키워드, x축: 총점)
        bars = plt.barh(df['rank_title'], df['total_score'], color=colors[i], alpha=0.8)
        
        # 제목 및 축 이름 설정
        plt.title(f'[{cat.upper()}] 통합 트렌드 TOP 10', fontsize=16, weight='bold', pad=15)
        plt.xlabel('Total Score (통합 트렌드 점수)', fontsize=12)
        plt.ylabel('Keywords', fontsize=12)
        
        # 막대 끝에 글자가 잘리지 않도록 X축 여백을 15% 정도 더 넓게 설정
        plt.xlim(0, max(df['total_score']) * 1.15) 
        
        # 🎯 막대 끝부분에 정확한 점수(Text) 달아주기
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}점', 
                     ha='left', va='center', fontsize=11, weight='bold', color='black')
                     
        # 보기 편하게 세로 점선 그리드 추가
        plt.grid(axis='x', linestyle='--', alpha=0.5)
        
        # 여백 최적화 후 이미지 저장
        plt.tight_layout()
        output_filename = f'result/visualize/top10_bar_{cat}.png'
        plt.savefig(output_filename, dpi=300)
        plt.close()
        
        print(f"✅ [{cat.upper()}] 시각화 완료! ({output_filename})")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: final_weighted_top10_{cat}.csv")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

print("\n🎉 모든 막대 그래프가 성공적으로 생성되었습니다!")