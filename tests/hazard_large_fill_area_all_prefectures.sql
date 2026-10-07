-- 大規模盛土造成地は 47 都道府県すべてに配布がある。全国版の zip から
-- 一部の県が抜けても行数が減るだけでビルドは通ってしまうので、
-- 47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT prefecture_code) AS prefecture_count
FROM {{ ref('large_fill_area') }}
HAVING count(DISTINCT prefecture_code) <> 47
