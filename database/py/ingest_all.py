# database/py/ingest_all.py
import os
import subprocess
import psycopg2

def run_script(script_name):
    print(f"
--- Running {script_name} ---")
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error in {script_name}: {result.stderr}")
    return result.returncode == 0

def get_final_stats():
    url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(url)
    cursor = conn.cursor()

    CATEGORIES = ['sports', 'climate', 'entertainment', 'finance_business']
    
    print("
" + "="*50)
    print("📊 FINAL INGESTION SUMMARY")
    print("="*50)
    
    for code in CATEGORIES:
        cursor.execute("""
            SELECT run_id, cr.created_at FROM collection_run cr
            JOIN category c ON cr.category_id = c.category_id
            WHERE c.code = %s ORDER BY cr.created_at DESC LIMIT 1
        """, (code,))
        res_run = cursor.fetchone()
        if not res_run:
            print(f"[Category: {code}] No run found.")
            continue
        
        run_id = res_run[0]
        
        # Counts
        cursor.execute("SELECT count(*) FROM keyword_score WHERE run_id = %s", (run_id,))
        ks_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM news_article WHERE run_id = %s", (run_id,))
        na_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM youtube_video WHERE run_id = %s", (run_id,))
        yv_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT min(cnt) FROM (
                SELECT keyword_id, count(*) as cnt FROM trend_series 
                WHERE run_id = %s GROUP BY keyword_id
            ) s
        """, (run_id,))
        min_trend = cursor.fetchone()[0] or 0
        
        print(f"
[Category: {code}] (Run ID: {run_id})")
        print(f" - Keyword Score 적재: {ks_count}/10")
        print(f" - News Article 적재: {na_count}")
        print(f" - YouTube Video 적재: {yv_count}")
        print(f" - Trend Series 최소 일수: {min_trend}")

    cursor.close()
    conn.close()
    print("="*50)

def main():
    scripts = [
        "database/py/0_schema_patch.py",
        "database/py/1_ingest_top10.py",
        "database/py/2_ingest_news.py",
        "database/py/3_ingest_youtube.py",
        "database/py/4_ingest_trends.py"
    ]
    
    success = True
    for script in scripts:
        if not run_script(script):
            success = False
            print(f"❌ Script {script} failed.")
            break
            
    if success:
        get_final_stats()
        print("
✨ Full pipeline execution completed.")
    else:
        print("
❌ Pipeline failed early.")

if __name__ == "__main__":
    main()
