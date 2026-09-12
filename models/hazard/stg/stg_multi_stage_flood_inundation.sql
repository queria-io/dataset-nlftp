{{ config(tags=['multi_stage_flood']) }}

SELECT
    bureau_code,
    river_system_code,
    river_system_name,
    data_year,
    rainfall_probability_denominator,
    depth_rank_3,
    depth_rank_6,
    ST_MakeValid(ST_GeomFromWKB(geom)) AS geometry
FROM {{ ref('raw_multi_stage_flood_inundation') }}
WHERE geom IS NOT NULL
