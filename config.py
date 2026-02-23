# config.py

import os
from dotenv import load_dotenv

def load_config():
    """
    .env 파일에서 환경 변수를 로드하고, 설정 딕셔너리를 반환합니다.
    """
    load_dotenv() # .env 파일에서 환경 변수를 로드합니다.

    config = {
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
        "INSTAGRAM_USERNAME": os.getenv("INSTAGRAM_USERNAME"),
        "INSTAGRAM_PASSWORD": os.getenv("INSTAGRAM_PASSWORD"),
        "MYSQL_HOST": os.getenv("MYSQL_HOST"),
        "MYSQL_PORT": int(os.getenv("MYSQL_PORT", 3306)), # 정수로 변환, 기본값 제공
        "MYSQL_USER": os.getenv("MYSQL_USER"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
    }

    # 주요 환경 변수 설정 여부 확인 (경고 메시지 출력)
    if not config["YOUTUBE_API_KEY"]:
        print("Warning: YOUTUBE_API_KEY가 .env 파일에 설정되지 않았습니다. YouTube 데이터 수집에 문제가 발생할 수 있습니다.")
    if not (config["INSTAGRAM_USERNAME"] and config["INSTAGRAM_PASSWORD"]):
        print("Warning: Instagram 사용자 이름 또는 비밀번호가 설정되지 않았습니다. Instagram 데이터 수집에 문제가 발생할 수 있습니다.")
    if not all([config["MYSQL_HOST"], config["MYSQL_USER"], config["MYSQL_PASSWORD"], config["MYSQL_DATABASE"]]):
        print("Warning: MySQL 데이터베이스 자격 증명이 불완전합니다. 데이터베이스 작업에 문제가 발생할 수 있습니다.")

    return config

if __name__ == "__main__":
    app_config = load_config()
    print("설정이 성공적으로 로드되었습니다 (누락된 중요 변수에 대한 경고를 확인하십시오).")
    # 예시: 로드된 설정 사용
    # print(f"YouTube API Key (부분): {app_config['YOUTUBE_API_KEY'][:5]}...")
    # print(f"MySQL 데이터베이스: {app_config['MYSQL_DATABASE']}")
