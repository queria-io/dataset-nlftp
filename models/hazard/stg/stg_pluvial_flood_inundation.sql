{{ config(tags=['pluvial_flood']) }}

SELECT
    prefecture_code,
    admin_code,
    municipality_name,
    data_year,
    depth_label,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_pluvial_flood_inundation') }}
WHERE geom IS NOT NULL
