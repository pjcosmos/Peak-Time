-- 1) category
CREATE TABLE IF NOT EXISTS category (
    category_id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name_ko VARCHAR(50) NOT NULL
);

-- 2) keyword
CREATE TABLE IF NOT EXISTS keyword (
    keyword_id BIGSERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3) collection_run
CREATE TABLE IF NOT EXISTS collection_run (
    run_id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    category_id BIGINT REFERENCES category(category_id),
    period_start DATE,
    period_end DATE,
    is_dummy BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4) google_trend_series (PK: run_id + keyword_id + ts)
CREATE TABLE IF NOT EXISTS google_trend_series (
    run_id BIGINT REFERENCES collection_run(run_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    ts TIMESTAMP NOT NULL,
    value NUMERIC(10,2),
    PRIMARY KEY (run_id, keyword_id, ts)
);

-- 5) naver_search_series (PK: run_id + keyword_id + ts)
CREATE TABLE IF NOT EXISTS naver_search_series (
    run_id BIGINT REFERENCES collection_run(run_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    ts TIMESTAMP NOT NULL,
    value NUMERIC(10,2),
    PRIMARY KEY (run_id, keyword_id, ts)
);

-- 6) keyword_score (PK: run_id + keyword_id) + weight 포함
CREATE TABLE IF NOT EXISTS keyword_score (
    run_id BIGINT REFERENCES collection_run(run_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    google_norm NUMERIC(10,4),
    naver_norm NUMERIC(10,4),
    weight_google NUMERIC(5,2),
    weight_naver NUMERIC(5,2),
    peak_time_index NUMERIC(10,4),
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, keyword_id)
);

-- 7) news_article
CREATE TABLE IF NOT EXISTS news_article (
    article_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES collection_run(run_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    title TEXT,
    url TEXT,
    publisher VARCHAR(255),
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8) youtube_video
CREATE TABLE IF NOT EXISTS youtube_video (
    video_pk BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES collection_run(run_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    youtube_id VARCHAR(50),
    title TEXT,
    channel_title VARCHAR(255),
    published_at TIMESTAMP,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 성능용 인덱스 (TOP10 조회, Step2 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_score_run_pti
ON keyword_score (run_id, peak_time_index DESC);

CREATE INDEX IF NOT EXISTS idx_news_run_keyword
ON news_article (run_id, keyword_id);

CREATE INDEX IF NOT EXISTS idx_youtube_run_keyword
ON youtube_video (run_id, keyword_id);