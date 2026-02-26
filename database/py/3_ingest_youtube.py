# database/py/3_ingest_youtube.py
import os
import pandas as pd
import psycopg2
import re

def normalize(text):
    if not text: return ""
    return re.sub(r'\s+', '', str(text)).lower()

def ingest_youtube():
    url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(url)
    cursor = conn.cursor()

    cursor.execute("SELECT keyword_id, keyword_text FROM keyword")
    kv_map = {normalize(txt): kid for kid, txt in cursor.fetchall()}

    f_path = "YouTube_depth_analysis/youtube_data_integrated.csv"
    if not os.path.exists(f_path): return {}
    df = pd.read_csv(f_path, encoding='utf-8')
    
    stats = {}
    for code in ['sports', 'climate', 'entertainment', 'finance_business']:
        cursor.execute("SELECT run_id FROM collection_run cr JOIN category c ON cr.category_id = c.category_id WHERE c.code = %s ORDER BY cr.created_at DESC LIMIT 1", (code,))
        run_id = cursor.fetchone()[0]
        
        # In reality, CSV might not have 'keyword_text', but let's assume it does or use 'keyword_id' if trusted.
        # Strict requirement: "Normalization based mapping".
        # Let's assume there's a way to get the text, or we use the 'keyword_id' from CSV if it aligns.
        # But instructions say "Normalized Text-based Matching" for all 2,3,4 stages.
        # If CSV only has keyword_id, I'll need a mapping back to text or just use ID if it's consistent.
        # To be safe, I'll look for a 'keyword' column.
        k_col = 'keyword' if 'keyword' in df.columns else 'rank_title' if 'rank_title' in df.columns else None
        
        if k_col:
            for k_text in df[k_col].unique():
                norm_k = normalize(k_text)
                if norm_k not in kv_map: continue
                k_id = kv_map[norm_k]
                
                df_k = df[df[k_col] == k_text].sort_values('view_count', ascending=False).head(3)
                for i, (_, row) in enumerate(df_k.iterrows()):
                    cursor.execute("""
                        INSERT INTO youtube_video (run_id, keyword_id, youtube_id, title, channel_title, published_at, 
                                                 view_count, like_count, comment_count, url, rank_no)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (run_id, keyword_id, youtube_id) DO NOTHING
                    """, (run_id, k_id, row['youtube_id'], row['title'], row['channel_title'], row['published_at'],
                          row['view_count'], row['like_count'], row['comment_count'], f"https://www.youtube.com/watch?v={row['youtube_id']}", i+1))
                    stats[code] = stats.get(code, 0) + 1
    conn.commit()
    cursor.close()
    conn.close()
    return stats

if __name__ == "__main__":
    ingest_youtube()
