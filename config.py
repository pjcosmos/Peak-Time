# config.py

import os
from dotenv import load_dotenv

def load_config():
    """
    .env 파일에서 환경 변수를 로드하고, 프로젝트 설정을 반환합니다.
    """
    load_dotenv()

    config = {
        # API Keys
        "NAVER_CLIENT_ID": os.getenv("NAVER_CLIENT_ID"),
        "NAVER_CLIENT_SECRET": os.getenv("NAVER_CLIENT_SECRET"),
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
        
        # Instagram Credentials
        "INSTAGRAM_USERNAME": os.getenv("INSTAGRAM_USERNAME"),
        "INSTAGRAM_PASSWORD": os.getenv("INSTAGRAM_PASSWORD"),
        
        # Database (MySQL)
        "MYSQL_HOST": os.getenv("MYSQL_HOST"),
        "MYSQL_PORT": int(os.getenv("MYSQL_PORT", 3306)),
        "MYSQL_USER": os.getenv("MYSQL_USER"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
        
        # Peak-Time Index Weights (기획서 기준)
        "WEIGHT_GOOGLE": 0.4,
        "WEIGHT_NAVER": 0.6,
        
        # Collection Settings
        "CATEGORIES": ["비즈니스·금융", "스포츠", "엔터테인먼트", "기후"],
        "DEFAULT_PERIOD_DAYS": 7,
        "TOP_K_LIMIT": 30,  # 1차 수집 제한
        "FINAL_TOP_N": 10   # 최종 확정 TOP 10
    }

    # 필수 API 키 확인
    missing_keys = []
    if not config["NAVER_CLIENT_ID"] or not config["NAVER_CLIENT_SECRET"]:
        missing_keys.append("NAVER_API (ID/SECRET)")
    if not config["YOUTUBE_API_KEY"]:
        missing_keys.append("YOUTUBE_API_KEY")
        
    if missing_keys:
        print(f"⚠️ 경고: 다음 설정이 누락되었습니다: {', '.join(missing_keys)}")
        print("네이버 및 유튜브 데이터 수집이 제한될 수 있습니다.")

    return config

if __name__ == "__main__":
    app_config = load_config()
    print("✅ Peak-Time 프로젝트 설정 로드 완료")
    print(f"분석 카테고리: {', '.join(app_config['CATEGORIES'])}")
    print(f"적용 가중치: 구글({app_config['WEIGHT_GOOGLE']}) : 네이버({app_config['WEIGHT_NAVER']})")
