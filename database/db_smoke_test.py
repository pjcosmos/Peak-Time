import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from sqlalchemy import create_engine, text

db_url = os.environ["DATABASE_URL"]
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(db_url, pool_pre_ping=True)

queries = {
    "category": "select count(*) as cnt from category",
    "collection_run": "select count(*) as cnt from collection_run",
    "keyword": "select count(*) as cnt from keyword",
    "keyword_score": "select count(*) as cnt from keyword_score",
    "trend_series": "select count(*) as cnt from trend_series",
    "news_article": "select count(*) as cnt from news_article",
    "youtube_video": "select count(*) as cnt from youtube_video",
}

out = []
with engine.connect() as conn:
    for name, q in queries.items():
        cnt = conn.execute(text(q)).scalar()
        out.append((name, int(cnt)))

df = pd.DataFrame(out, columns=["table", "count"])
print(df.to_string(index=False))