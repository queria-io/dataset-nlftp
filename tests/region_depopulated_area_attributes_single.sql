-- 区域の属性は原典では区域に属する全ポリゴンに同じ値が入っている。
-- 公開テーブルは区域ごとに 1 行へ集約して代表値を取るので、集約する前の
-- 値が区域の中でそろっていることを確かめる。
SELECT area_code
FROM {{ ref('stg_depopulated_area') }}
GROUP BY area_code
HAVING count(DISTINCT lg_code) > 1
    OR count(DISTINCT prefecture_code) > 1
    OR count(DISTINCT subprefecture_name) > 1
    OR count(DISTINCT district_name) > 1
    OR count(DISTINCT municipality_name) > 1
    OR count(DISTINCT former_municipality_name) > 1
    OR count(DISTINCT category_code) > 1
