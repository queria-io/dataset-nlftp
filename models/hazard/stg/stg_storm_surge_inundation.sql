{{ config(tags=['storm_surge']) }}

SELECT
    prefecture_code,
    data_year,
    depth_label,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_storm_surge_inundation') }}
WHERE geom IS NOT NULL
