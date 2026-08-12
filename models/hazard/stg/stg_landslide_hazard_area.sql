{{ config(tags=['landslide']) }}

SELECT
    prefecture_code,
    phenomenon_code,
    zone_code,
    zone_number,
    zone_name,
    address,
    notice_date,
    -- 特別警戒未指定フラグ（0=特別警戒区域指定済み / 1=未指定）
    special_zone_unspecified_code = 1 AS special_zone_unspecified,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_landslide_hazard_area') }}
WHERE geom IS NOT NULL
