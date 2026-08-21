-- 前回国勢調査の人口・面積は、前回その地区が人口集中地区でなかった場合に
-- -99999 が入る（原典の欠測値）。NULL に直してから公開する
SELECT
    A16_001 AS did_code,
    A16_002 AS lg_code,
    LEFT(A16_002, 2) AS prefecture_code,
    {{ prefecture_name_from_code('LEFT(A16_002, 2)') }} AS prefecture_name,
    A16_003 AS municipality_name,
    A16_004 AS did_number,
    A16_005 AS population,
    A16_006 AS area_km2,
    NULLIF(A16_007, -99999) AS previous_population,
    NULLIF(A16_008, -99999) AS previous_area_km2,
    A16_009 AS population_share_pct,
    A16_010 AS area_share_pct,
    A16_011 AS census_year,
    A16_012 AS population_male,
    A16_013 AS population_female,
    A16_014 AS households,
    -- 面だけを取り出して型を揃える（ST_MakeValid が線分や点を含む
    -- GEOMETRYCOLLECTION を返すことがある）
    ST_CollectionExtract(ST_MakeValid(ST_GeomFromWKB(geom)), 3) AS geometry
FROM {{ ref('raw_did') }}
WHERE geom IS NOT NULL
