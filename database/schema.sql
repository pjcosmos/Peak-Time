BEGIN;

-- 전부 삭제(갈아엎기)
DROP TABLE IF EXISTS youtube_video CASCADE;
DROP TABLE IF EXISTS news_article CASCADE;
DROP TABLE IF EXISTS trend_series CASCADE;
DROP TABLE IF EXISTS keyword_score CASCADE;
DROP TABLE IF EXISTS collection_run CASCADE;
DROP TABLE IF EXISTS keyword CASCADE;
DROP TABLE IF EXISTS category CASCADE;

-- category
CREATE TABLE category (
  category_id  BIGSERIAL PRIMARY KEY,
  code         VARCHAR(50) UNIQUE NOT NULL,
  name_ko      VARCHAR(50) NOT NULL
);

-- keyword
CREATE TABLE keyword (
  keyword_id    BIGSERIAL PRIMARY KEY,
  keyword_text  VARCHAR(255) UNIQUE NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- collection_run
CREATE TABLE collection_run (
  run_id        BIGSERIAL PRIMARY KEY,
  country_code  CHAR(2) NOT NULL DEFAULT 'KR',
  category_id   BIGINT NOT NULL REFERENCES category(category_id) ON DELETE RESTRICT,
  period_start  DATE NOT NULL,
  period_end    DATE NOT NULL,
  is_dummy      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX ux_run_unique
ON collection_run(country_code, category_id, period_start, period_end, is_dummy);

CREATE INDEX ix_run_category_created
ON collection_run(category_id, created_at DESC);

-- keyword_score (TOP10)
CREATE TABLE keyword_score (
  run_id            BIGINT NOT NULL REFERENCES collection_run(run_id) ON DELETE CASCADE,
  keyword_id         BIGINT NOT NULL REFERENCES keyword(keyword_id) ON DELETE RESTRICT,

  rank_no            INT,
  peak_time_index    NUMERIC(10,4) NOT NULL,

  google_share       NUMERIC(10,4),
  naver_share        NUMERIC(10,4),

  google_volume_text VARCHAR(50),
  naver_trend_sum    NUMERIC(12,2),

  computed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, keyword_id)
);

CREATE INDEX ix_score_run_pti
ON keyword_score(run_id, peak_time_index DESC);

CREATE INDEX ix_score_run_rank
ON keyword_score(run_id, rank_no ASC);

-- trend_series (라인차트: google/naver 통합, 날짜만)
CREATE TABLE trend_series (
  run_id     BIGINT NOT NULL REFERENCES collection_run(run_id) ON DELETE CASCADE,
  keyword_id BIGINT NOT NULL REFERENCES keyword(keyword_id) ON DELETE RESTRICT,

  source     VARCHAR(10) NOT NULL CHECK (source IN ('google', 'naver')),
  d          DATE NOT NULL,
  value      NUMERIC(12,2) NOT NULL,

  PRIMARY KEY (run_id, keyword_id, source, d)
);

CREATE INDEX ix_series_lookup
ON trend_series(run_id, keyword_id, source, d);

-- news_article (이미지 포함)
CREATE TABLE news_article (
  article_id    BIGSERIAL PRIMARY KEY,
  run_id        BIGINT NOT NULL REFERENCES collection_run(run_id) ON DELETE CASCADE,
  keyword_id    BIGINT NOT NULL REFERENCES keyword(keyword_id) ON DELETE RESTRICT,

  title         TEXT NOT NULL,
  url           TEXT NOT NULL,
  publisher     VARCHAR(255),
  published_at  TIMESTAMPTZ,
  image_url     TEXT,
  collected_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_news_run_keyword
ON news_article(run_id, keyword_id);

-- youtube_video (썸네일 포함)
CREATE TABLE youtube_video (
  video_pk      BIGSERIAL PRIMARY KEY,
  run_id        BIGINT NOT NULL REFERENCES collection_run(run_id) ON DELETE CASCADE,
  keyword_id    BIGINT NOT NULL REFERENCES keyword(keyword_id) ON DELETE RESTRICT,

  youtube_id    VARCHAR(50) NOT NULL,
  title         TEXT,
  channel_title VARCHAR(255),
  published_at  TIMESTAMPTZ,

  view_count    BIGINT,
  like_count    BIGINT,
  comment_count BIGINT,
  thumbnail_url TEXT,

  collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (run_id, keyword_id, youtube_id)
);

CREATE INDEX ix_youtube_run_keyword
ON youtube_video(run_id, keyword_id);

CREATE INDEX ix_youtube_views
ON youtube_video(run_id, keyword_id, view_count DESC);

-- 카테고리 시드(5개)
INSERT INTO category(code, name_ko) VALUES
  ('sports', '스포츠'),
  ('climate', '기후'),
  ('entertainment', '엔터'),
  ('finance', '금융'),
  ('business', '비즈니스')
ON CONFLICT (code) DO NOTHING;

COMMIT;