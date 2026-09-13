-- 原典市区町村名は「郡・政令都市名 + 市区町村名」と一致するので取らない。
--
-- 属性がすべて空の行が岩手県に 1 行ある（過疎ID・行政区域コードが無く、
-- 過疎区分コードが 0、面積が計算できない退化ポリゴン）。どの区域にも
-- 結び付けられないので落とす
SELECT
    prefecture_code,
    area_code,
    lg_code,
    subprefecture_name,
    district_name,
    municipality_name,
    former_municipality_name,
    category_code,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3) AS geometry
FROM {{ ref('raw_depopulated_area') }}
WHERE geom IS NOT NULL
  AND area_code IS NOT NULL
