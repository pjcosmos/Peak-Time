import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    # 1. 환경 변수에서 Railway DB 연결 주소 불러오기
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("❌ DATABASE_URL을 찾을 수 없습니다. .env 파일을 확인해 주세요.")
        return

    # 2. schema.sql 파일 읽어오기
    try:
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except FileNotFoundError:
        print("❌ schema.sql 파일을 찾을 수 없습니다.")
        return

    print("🔌 Railway 데이터베이스에 접속 중입니다...")
    conn = None
    cursor = None

    try:
        # 3. 데이터베이스 연결 및 커서 생성
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 4. 준비된 SQL 스크립트 실행
        print("🏗️ 기존 테이블을 지우고 새로운 스키마를 생성합니다...")
        cursor.execute(sql_script)

        # 5. 변경 사항 확정 (적용)
        conn.commit()
        print("🎉 성공적으로 테이블 생성 및 카테고리 데이터 세팅이 완료되었습니다!")

    except Exception as e:
        print(f"❌ 데이터베이스 작업 중 오류가 발생했습니다: {e}")
        # 오류 발생 시 변경 사항 취소 (안전 장치)
        if conn:
            conn.rollback()
    
    finally:
        # 6. 작업이 끝나면 반드시 연결 종료
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("🔒 데이터베이스 연결을 안전하게 종료했습니다.")

if __name__ == "__main__":
    setup_database()