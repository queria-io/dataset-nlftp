-- 名称に「十¥勝」「能¥美市」「西予¥市」のような円記号が混ざる（56 区域）。
-- Shift_JIS の 2 バイト目が 0x5C の文字の後ろに、エスケープの名残が
-- 残ったもの。地名に円記号は現れないので取り除く。
--
-- 原典市区町村名は指定された時点（合併前）の市区町村名で、市区町村名とは
-- 一致しないので残す
SELECT
    prefecture_code,
    area_code,
    lg_code,
    replace(subprefecture_name, '¥', '') AS subprefecture_name,
    replace(district_name, '¥', '') AS district_name,
    replace(municipality_name, '¥', '') AS municipality_name,
    replace(source_municipality_name, '¥', '') AS source_municipality_name,
    replace(former_municipality_name, '¥', '') AS former_municipality_name,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3) AS geometry
FROM {{ ref('raw_specified_rural_area') }}
WHERE geom IS NOT NULL
