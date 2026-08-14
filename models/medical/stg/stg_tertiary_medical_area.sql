{{ config(tags=['medical_area']) }}

-- 二次医療圏と同じく 1 行 = 1 ポリゴンなので、医療圏単位に集約する。
-- 三次医療圏の名称は都道府県全域を 1 つの圏域とする場合に原典で空になるため、
-- 都道府県コードと名称の組で集約する
SELECT
    prefecture_code,
    {{ prefecture_name_from_code('prefecture_code') }} AS prefecture_name,
    area_name,
    ST_CollectionExtract(
        ST_MakeValid(ST_Union_Agg(ST_MakeValid(ST_GeomFromWKB(geom)))), 3
    ) AS geometry
FROM {{ ref('raw_tertiary_medical_area') }}
WHERE geom IS NOT NULL
GROUP BY prefecture_code, area_name
