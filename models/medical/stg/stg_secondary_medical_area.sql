{{ config(tags=['medical_area']) }}

-- 原典は 1 行 = 1 ポリゴンで、1 つの医療圏が離島や飛び地の分だけ行に分かれる。
-- 医療圏単位に集約して 1 行 = 1 医療圏にする。属性は医療圏ごとに同じ値が
-- 全行に入っているので、代表値を 1 つ取る（値が揃っていることは dbt テストで
-- 確かめる）
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    area_code,
    max(area_name) AS area_name,
    max(planned_area_km2) AS planned_area_km2,
    max(surveyed_area_km2) AS surveyed_area_km2,
    max(planned_population) AS planned_population,
    max(population) AS population,
    max(population_under_15) AS population_under_15,
    max(population_15_to_64) AS population_15_to_64,
    max(population_65_and_over) AS population_65_and_over,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(
        ST_MakeValid(ST_Union_Agg(ST_MakeValid(ST_GeomFromWKB(geom)))), 3
    ) AS geometry
FROM {{ ref('raw_secondary_medical_area') }}
WHERE geom IS NOT NULL
GROUP BY prefecture_code, area_code
