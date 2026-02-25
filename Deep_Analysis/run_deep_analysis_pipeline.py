import subprocess
import sys
import time
import os

def run_script(script_name, description):
    """개별 파이썬 스크립트를 실행하고 소요 시간과 에러를 관리하는 도우미 함수"""
    print(f"\n▶️ [{description}] 시작... ({script_name})")
    start_time = time.time()
    
    try:
        # sys.executable을 사용하여 현재 환경의 파이썬으로 스크립트 실행
        subprocess.run([sys.executable, script_name], check=True)
        
        elapsed_time = time.time() - start_time
        print(f"✅ [{description}] 완료! (소요 시간: {elapsed_time:.2f}초)")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [{description}] 단계에서 오류가 발생했습니다! (파일: {script_name})")
        print("💡 파이프라인을 중단합니다. 이전 단계의 코드와 데이터를 확인해 주세요.")
        sys.exit(1) # 에러 발생 시 즉시 중단 (Fail-fast)
    except FileNotFoundError:
        print(f"\n❌ {script_name} 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해 주세요!")
        sys.exit(1)

def main():
    print("🚀 [뉴스 & 유튜브 심층 분석 파이프라인] 가동을 시작합니다 🚀")
    print("=" * 70)
    
    # 결과물이 저장될 최상위 폴더가 없다면 미리 생성해 둡니다.
    os.makedirs('result', exist_ok=True)
    
    total_start = time.time()
    
    # ---------------------------------------------------------
    # 📦 [Phase 1] 외부 데이터 전처리 및 병합
    # ---------------------------------------------------------
    run_script('news_data_preprocessing.py', 'Step 1: 뉴스 데이터 전처리 및 트렌드 점수 병합')
    run_script('youtube_data_preprocessing.py', 'Step 2: 유튜브 데이터 매핑 및 평균 수치 도출')
    
    # ---------------------------------------------------------
    # 🧠 [Phase 2] 상관관계 심층 분석
    # ---------------------------------------------------------
    run_script('analyze_news_correlation.py', 'Step 3: 대중 트렌드 vs 언론 기사량 상관관계 분석')
    run_script('analyze_youtube_correlation.py', 'Step 4: 대중 트렌드 vs 유튜브 화제성 상관관계 분석')
    
    # ---------------------------------------------------------
    # 💡 [Phase 3] 웹사이트용 핵심 인사이트 기능 추출
    # ---------------------------------------------------------
    run_script('analyze_ocean_status.py', 'Step 5: 블루오션/레드오션 판별기 데이터 생성')
    run_script('analyze_youtube_engagement.py', 'Step 6: 카테고리별 유튜브 찐팬 온도계 데이터 생성')
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "=" * 70)
    print(f"🎉 모든 심층 분석 파이프라인이 성공적으로 완료되었습니다! (총 소요 시간: {total_elapsed:.2f}초)")
    print("📁 'result/web_data/' 폴더에서 웹사이트용 JSON 데이터를,")
    print("📁 'result/visualize/' 폴더에서 시각화 그래프 이미지를 확인해 보세요!")

if __name__ == "__main__":
    main()