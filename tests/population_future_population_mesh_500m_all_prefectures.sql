-- 500mメッシュ別将来推計人口は全国版 zip に入れ子になった 47 都道府県別
-- Shapefile を UNION ALL して作る。どれかの展開や ST_Read が欠けても行数が
-- 減るだけでビルドは通ってしまうため、47 都道府県が揃っていることを検査する。
SELECT count(DISTINCT substr(city_code, 1, 2)) AS prefecture_count
FROM {{ ref('future_population_mesh_500m') }}
HAVING count(DISTINCT substr(city_code, 1, 2)) <> 47
