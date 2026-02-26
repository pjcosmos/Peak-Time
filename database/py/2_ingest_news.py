# database/py/2_ingest_news.py
import os
import json
import psycopg2
import re

def normalize(text):
    if not text: return ""
    return re.sub(r'\s+', '', str(text)).lower()

def ingest_news():
    url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(url)
    cursor = conn.cursor()

    # Pre-fetch keyword mappings for normalization
    cursor.execute("SELECT keyword_id, keyword_text FROM keyword")
    kv_map = {normalize(txt): kid for kid, txt in cursor.fetchall()}

    news_files = {
        'naver': 'news/naver_news_grouped_by_category_keyword.json',
        'daum': 'news/daum_news_grouped_by_category_keyword.json',
        'google': 'news/google_news_grouped_by_category_keyword.json'
    }
    cat_map = {'sports': '스포츠', 'climate': '기후', 'entertainment': '연예/문화', 'finance_business': '금융/비즈니스'}
    
    stats = {}
    for source, f_path in news_files.items():
        if not os.path.exists(f_path): continue
        with open(f_path, 'r', encoding='utf-8') as f: data = json.load(f)
        
        for code, cat_name in cat_map.items():
            if cat_name not in data: continue
            cursor.execute("SELECT run_id FROM collection_run cr JOIN category c ON cr.category_id = c.category_id WHERE c.code = %s ORDER BY cr.created_at DESC LIMIT 1", (code,))
            run_id = cursor.fetchone()[0]
            
            for k_text, articles in data[cat_name].items():
                norm_k = normalize(k_text)
                if norm_k not in kv_map:
                    print(f"⚠️ [매핑 실패] {code}: {k_text} - Top10 DB에 없음")
                    continue
                k_id = kv_map[norm_k]
                for i, art in enumerate(articles[:3]):
                    cursor.execute("INSERT INTO news_article (run_id, keyword_id, title, url, publisher, published_at, source, rank_no) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                                 (run_id, k_id, art['title'], art['url'], art.get('publisher'), art.get('published_at'), source, i+1))
                    stats[code] = stats.get(code, 0) + 1
    conn.commit()
    cursor.close()
    conn.close()
    return stats

if __name__ == "__main__":
    ingest_news()
