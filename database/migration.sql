BEGIN;

-- 1️⃣ 더미 run 먼저 삭제 (안전)
DELETE FROM collection_run WHERE is_dummy = TRUE;

-- 2️⃣ category 초기화 (연결된 run 없으면 안전)
TRUNCATE TABLE category RESTART IDENTITY CASCADE;

-- 3️⃣ 확정 5개 카테고리 삽입
INSERT INTO category (code, name_ko) VALUES
('business', '비즈니스'),
('finance', '금융'),
('sports', '스포츠'),
('entertainment', '엔터테인먼트'),
('climate', '기후');

COMMIT;