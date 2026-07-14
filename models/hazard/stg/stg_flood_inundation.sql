{{ config(tags=['flood']) }}

SELECT
    region_code,
    river_code,
    river_name,
    admin_code,
    admin_name,
    depth_rank,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_flood_inundation') }}
WHERE geom IS NOT NULL
