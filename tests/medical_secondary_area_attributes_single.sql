-- 二次医療圏の属性は原典では医療圏に属する全ポリゴンに同じ値が入っている。
-- 公開テーブルは医療圏ごとに 1 行へ集約して代表値を取るので、集約する前の
-- 値が医療圏の中でそろっていることを確かめる。
SELECT area_code
FROM {{ ref('raw_secondary_medical_area') }}
GROUP BY area_code
HAVING count(DISTINCT area_name) > 1
    OR count(DISTINCT planned_area_km2) > 1
    OR count(DISTINCT surveyed_area_km2) > 1
    OR count(DISTINCT planned_population) > 1
    OR count(DISTINCT population) > 1
    OR count(DISTINCT population_under_15) > 1
    OR count(DISTINCT population_15_to_64) > 1
    OR count(DISTINCT population_65_and_over) > 1
