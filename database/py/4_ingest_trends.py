# database/py/4_ingest_trends.py
import os
import json
import psycopg2
import re

def normalize(text):
    if not text: return ""
    return re.sub(r'\s+', '', str(text)).lower()

def ingest_trends():
    url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(url)
    cursor = conn.cursor()

    cursor.execute("SELECT keyword_id, keyword_text FROM keyword")
    kv_map = {normalize(txt): kid for kid, txt in cursor.fetchall()}

    CATEGORIES = ['sports', 'climate', 'entertainment', 'finance_business']
    stats = {}

    for code in CATEGORIES:
        cursor.execute("SELECT run_id FROM collection_run cr JOIN category c ON cr.category_id = c.category_id WHERE c.code = %s ORDER BY cr.created_at DESC LIMIT 1", (code,))
        run_id = cursor.fetchone()[0]
        
        files = [f"naver_data/trend_report_{code}.json", f"Top10_Trends/raw_data/trend_report_{code}.json"]
        for f_path in files:
            if not os.path.exists(f_path): continue
            with open(f_path, 'r', encoding='utf-8') as f: data = json.load(f)
            for res in data.get('results', []):
                k_text = res.get('rank_title')
                norm_k = normalize(k_text)
                if norm_k not in kv_map: continue
                k_id = kv_map[norm_k]
                
                series = res.get('naver_daily_ratio', [])
                if len(series) < 7: continue
                
                for item in series:
                    cursor.execute("""
                        INSERT INTO trend_series (run_id, keyword_id, source, d, value)
                        VALUES (%s, %s, 'naver', %s, %s)
                        ON CONFLICT (run_id, keyword_id, source, d) DO UPDATE SET value = EXCLUDED.value
                    """, (run_id, k_id, item['period'], item['ratio']))
                    stats[code] = stats.get(code, 0) + 1
    conn.commit()
    cursor.close()
    conn.close()
    return stats

if __name__ == "__main__":
    ingest_trends()
