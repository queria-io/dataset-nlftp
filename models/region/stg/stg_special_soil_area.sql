-- 原典市区町村名は指定された時点の市区町村名で、郡名や「〇〇市の一部」の
-- 形で入り、市区町村名とは一致しないので残す
SELECT
    prefecture_code,
    area_code,
    lg_code,
    subprefecture_name,
    district_name,
    municipality_name,
    source_municipality_name,
    former_municipality_name,
    category_code,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3) AS geometry
FROM {{ ref('raw_special_soil_area') }}
WHERE geom IS NOT NULL
