-- 大字・町丁目レベル位置参照情報も都道府県別の zip を 47 本取り込んで作るので、
-- 47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('oaza') }}
HAVING count(DISTINCT prefecture_code) <> 47
