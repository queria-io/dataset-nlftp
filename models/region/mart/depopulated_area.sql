{{ config(materialized='table') }}

-- 1 行 = 1 指定区域。原典は区域を島や飛び地ごとのポリゴンに分けて持つので、
-- 過疎IDでまとめて 1 つのマルチポリゴンにする。区域の属性はどのポリゴンにも
-- 同じ値が入っているため any_value で取り出す
SELECT
    area_code,
    any_value(lg_code) AS lg_code,
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    any_value(subprefecture_name) AS subprefecture_name,
    any_value(district_name) AS district_name,
    any_value(municipality_name) AS municipality_name,
    any_value(former_municipality_name) AS former_municipality_name,
    any_value(category_code) AS category_code,
    {{ depopulated_category_name('any_value(category_code)') }} AS category,
    ST_Union_Agg(geometry) AS geometry
FROM {{ ref('stg_depopulated_area') }}
GROUP BY area_code, prefecture_code
