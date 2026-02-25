import subprocess
import sys
import time

# 개별 스크립트를 실행해주는 도우미 함수
def run_script(script_name, description):
    print(f"\n▶️ [{description}] 시작... ({script_name})")
    start_time = time.time()
    
    try:
        # sys.executable을 사용해 현재 실행 중인 파이썬 환경으로 스크립트를 실행합니다.
        # check=True: 에러가 나면 즉시 예외(Exception)를 발생시킵니다.
        subprocess.run([sys.executable, script_name], check=True)
        
        elapsed_time = time.time() - start_time
        print(f"✅ [{description}] 완료! (소요 시간: {elapsed_time:.2f}초)")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [{description}] 단계에서 오류가 발생했습니다! (파일: {script_name})")
        print("💡 파이프라인을 중단합니다. 이전 단계의 코드와 데이터를 확인해 주세요.")
        sys.exit(1) # 에러 발생 시 파이프라인 즉시 중단
    except FileNotFoundError:
        print(f"\n❌ {script_name} 파일을 찾을 수 없습니다. 파일 이름을 확인해 주세요!")
        sys.exit(1)

def main():
    print("🚀 [구글 x 네이버 통합 트렌드 분석 파이프라인] 가동을 시작합니다 🚀")
    print("=" * 65)
    
    total_start = time.time()
    
    # ---------------------------------------------------------
    # 📦 [Step 1] 데이터 전처리 (Preprocessing)
    # ---------------------------------------------------------
    run_script('data_preprocessing.py', 'Step 1: 데이터 전처리 및 신규 지표(기울기) 생성')
    
    # ---------------------------------------------------------
    # 🧠 [Step 2] 데이터 분석 (Analysis)
    # ---------------------------------------------------------
    run_script('calculate_final_top10.py', 'Step 2-1: 가중치(70:30) 기반 TOP 10 랭킹 산출')
    run_script('analyze_trends.py', 'Step 2-2: 키워드별 플랫폼 기여도(%) 심층 분석')
    run_script('quadrant_analysis.py', 'Step 2-3: 4분면(Volume vs Momentum) 포지셔닝 분석')
    
    # ---------------------------------------------------------
    # 🎨 [Step 3] 데이터 시각화 (Visualization)
    # ---------------------------------------------------------
    run_script('visualize_top10.py', 'Step 3-1: 카테고리별 TOP 10 수평 막대 그래프 생성')
    run_script('visualize_platform.py', 'Step 3-2: 플랫폼 기여도 누적 막대 그래프 생성')
    run_script('visualize_quadrant.py', 'Step 3-3: 4분면 포지셔닝 맵 스캐터 플롯 생성')
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 65)
    print(f"🎉 모든 파이프라인이 성공적으로 완료되었습니다! (총 소요 시간: {total_elapsed:.2f}초)")
    print("📁 생성된 결과물(.csv, .png)을 확인해 보세요.")

if __name__ == "__main__":
    main()