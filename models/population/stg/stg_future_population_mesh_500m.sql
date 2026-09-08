SELECT
    MESH_ID AS mesh_id,
    SHICODE AS city_code,
    PTN_2020 AS population_2020,
    PTN_2025 AS population_2025,
    PTN_2030 AS population_2030,
    PTN_2035 AS population_2035,
    PTN_2040 AS population_2040,
    PTN_2045 AS population_2045,
    PTN_2050 AS population_2050,
    PTN_2055 AS population_2055,
    PTN_2060 AS population_2060,
    PTN_2065 AS population_2065,
    PTN_2070 AS population_2070,
    PTC_2025 AS elderly_2025,
    PTC_2050 AS elderly_2050,
    ST_MakeValid(geom) AS geometry
FROM {{ ref('raw_future_population_mesh_500m') }}
WHERE geom IS NOT NULL
  AND SHICODE IS NOT NULL
